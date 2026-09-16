"""Orchestration service — combines applicability, dependency, document,
consistency, and SLA results into per-approval readiness assessments.

This is a PURE FUNCTION layer: no database calls, no side effects,
no LLM calls. All data is passed in as parameters.

Design principle: delegate to existing engines, do not duplicate logic.
"""
from __future__ import annotations

from typing import Any

from app.orchestration.models import (
    ApplicationOrchestration,
    ApprovalOrchestration,
    BlockerDetail,
    BlockerType,
    DocumentReadinessSummary,
    NextAction,
    OrchestrationStatus,
)
from app.rules.applicability import (
    evaluate_approval_applicability,
    summarize_by_approval,
)
from app.rules.dependency_engine import evaluate_readiness
from app.rules.dependency_models import (
    ApprovalDependency,
    ApprovalReadiness,
    ReadinessStatus,
)
from app.rules.models import ApplicabilityEvaluation, ApprovalRule

# Status priority for worst-case aggregation (higher = worse).
_STATUS_PRIORITY: dict[OrchestrationStatus, int] = {
    OrchestrationStatus.BLOCKED_BY_DEPENDENCY: 6,
    OrchestrationStatus.BLOCKED_BY_DOCUMENTS: 5,
    OrchestrationStatus.INSUFFICIENT_DATA: 4,
    OrchestrationStatus.REVIEW_REQUIRED: 3,
    OrchestrationStatus.READY: 2,
    OrchestrationStatus.NOT_APPLICABLE: 1,
    OrchestrationStatus.COMPLETE: 0,
}

# Next-action priority (lower = higher priority).
_ACTION_PRIORITY: dict[str, int] = {
    "upload_document": 10,
    "validate_document": 20,
    "review_document": 30,
    "fix_extraction": 40,
    "consistency_review": 50,
    "sla_attention": 60,
    "resolve_dependency": 70,
    "complete": 999,
}


def _is_mandatory(req: dict[str, Any]) -> bool:
    """A document is mandatory if its requirement_level is 'required' or 'mandatory'."""
    return req.get("requirement_level") in ("required", "mandatory")


def _compute_document_readiness(
    approval_id: str,
    document_requirements: list[dict[str, Any]],
    uploaded_documents: list[dict[str, Any]],
    extraction_results: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
) -> tuple[
    str,
    list[DocumentReadinessSummary],
    list[BlockerDetail],
    list[dict[str, Any]],
]:
    """Compute document readiness for a single approval.

    Returns:
        (readiness_label, document_summaries, blockers, doc_dicts)
    """
    reqs = [r for r in document_requirements if approval_id in r.get("approval_ids", [])]

    # Build lookup maps
    uploaded_map: dict[str, dict[str, Any]] = {
        doc["requirement_key"]: doc for doc in uploaded_documents
    }
    extraction_map: dict[str, dict[str, Any]] = {
        ex["requirement_key"]: ex for ex in extraction_results
    }
    validation_map: dict[str, dict[str, Any]] = {
        val["requirement_key"]: val for val in validation_results
    }

    if not reqs:
        return "no_requirements", [], [], []

    summaries: list[DocumentReadinessSummary] = []
    blockers: list[BlockerDetail] = []
    mandatory_results: list[bool] = []  # True = satisfied

    for req in reqs:
        rk = req["requirement_key"]
        doc_name = req["document_name"]
        mandatory = _is_mandatory(req)
        uploaded = rk in uploaded_map
        extraction = extraction_map.get(rk)
        validation = validation_map.get(rk)

        extraction_status = extraction["extraction_status"] if extraction else None
        validation_outcome = validation["outcome"] if validation else None

        if not uploaded:
            doc_readiness = "missing"
            blocking = mandatory
            reason = "Document not uploaded"
            if mandatory:
                mandatory_results.append(False)
                blockers.append(
                    BlockerDetail(
                        blocker_type=BlockerType.DOCUMENT_MISSING,
                        description=f"Missing mandatory document: {doc_name}",
                        affected_approval_id=approval_id,
                        affected_document_key=rk,
                        source_ref=req.get("source_basis", ""),
                        evidence=req.get("source_url", ""),
                        action_required=f"Upload {doc_name}",
                    )
                )
            else:
                mandatory_results.append(True)  # Optional docs don't block
        elif extraction_status == "failed":
            doc_readiness = "extraction_failed"
            blocking = mandatory
            reason = "Document extraction failed"
            if mandatory:
                mandatory_results.append(False)
                blockers.append(
                    BlockerDetail(
                        blocker_type=BlockerType.EXTRACTION_FAILED,
                        description=f"Extraction failed for: {doc_name}",
                        affected_approval_id=approval_id,
                        affected_document_key=rk,
                        source_ref=req.get("source_basis", ""),
                        evidence=str(extraction.get("errors", [])) if extraction else "",
                        action_required=f"Re-extract or re-upload {doc_name}",
                    )
                )
            else:
                mandatory_results.append(True)
        elif validation_outcome == "INVALID":
            doc_readiness = "invalid"
            blocking = mandatory
            reason = "Document validation failed"
            if mandatory:
                mandatory_results.append(False)
                blockers.append(
                    BlockerDetail(
                        blocker_type=BlockerType.DOCUMENT_INVALID,
                        description=f"Invalid document: {doc_name}",
                        affected_approval_id=approval_id,
                        affected_document_key=rk,
                        source_ref=req.get("source_basis", ""),
                        evidence=str(validation.get("findings", [])) if validation else "",
                        action_required=f"Fix and re-upload {doc_name}",
                    )
                )
            else:
                mandatory_results.append(True)
        elif validation_outcome == "REVIEW_REQUIRED":
            doc_readiness = "review_required"
            blocking = mandatory
            reason = "Document requires manual review"
            if mandatory:
                mandatory_results.append(False)
                blockers.append(
                    BlockerDetail(
                        blocker_type=BlockerType.DOCUMENT_REVIEW_REQUIRED,
                        description=f"Review required for: {doc_name}",
                        affected_approval_id=approval_id,
                        affected_document_key=rk,
                        source_ref=req.get("source_basis", ""),
                        evidence=str(validation.get("findings", [])) if validation else "",
                        action_required=f"Review {doc_name}",
                    )
                )
            else:
                mandatory_results.append(True)
        else:
            doc_readiness = "valid"
            blocking = False
            reason = "Document uploaded and validated"
            mandatory_results.append(True)

        summaries.append(
            DocumentReadinessSummary(
                requirement_key=rk,
                document_name=doc_name,
                readiness=doc_readiness,
                extraction_status=extraction_status,
                validation_outcome=validation_outcome,
                blocking=blocking,
                reason=reason,
            )
        )

    # Determine overall document readiness label
    if all(mandatory_results):
        label = "all_valid"
    elif any(
        s.readiness == "missing"
        for s in summaries
        if _is_mandatory_next(reqs, s.requirement_key)
    ):
        label = "missing"
    elif any(
        s.readiness == "invalid"
        for s in summaries
        if _is_mandatory_next(reqs, s.requirement_key)
    ):
        label = "invalid"
    elif any(s.readiness == "review_required" for s in summaries):
        label = "review_required"
    else:
        label = "all_valid"

    return label, summaries, blockers, reqs


def _is_mandatory_next(reqs: list[dict[str, Any]], requirement_key: str) -> bool:
    """Check if a requirement_key is mandatory from the requirement list."""
    for req in reqs:
        if req["requirement_key"] == requirement_key:
            return _is_mandatory(req)
    return False


def _determine_status(
    applicability_result: str,
    dependency_readiness: ReadinessStatus,
    has_doc_blockers: bool,
    has_doc_review: bool,
    consistency_review_needed: bool,
    sla_breached: bool,
) -> OrchestrationStatus:
    """Determine orchestration status using priority rules."""
    if applicability_result == "does_not_apply":
        return OrchestrationStatus.NOT_APPLICABLE

    if applicability_result in ("conditional", "insufficient_data"):
        return OrchestrationStatus.INSUFFICIENT_DATA

    if dependency_readiness == ReadinessStatus.BLOCKED:
        return OrchestrationStatus.BLOCKED_BY_DEPENDENCY

    if has_doc_blockers:
        return OrchestrationStatus.BLOCKED_BY_DOCUMENTS

    if has_doc_review or consistency_review_needed or sla_breached:
        return OrchestrationStatus.REVIEW_REQUIRED

    return OrchestrationStatus.READY


def _pick_next_action(
    blockers: list[BlockerDetail],
    document_readiness: str,
    consistency_review_needed: bool,
    sla_breached: bool,
) -> str:
    """Select the highest-priority next action from blockers."""
    action_candidates: list[str] = []

    for b in blockers:
        if b.blocker_type == BlockerType.DOCUMENT_MISSING:
            action_candidates.append("upload_document")
        elif b.blocker_type == BlockerType.DOCUMENT_INVALID:
            action_candidates.append("validate_document")
        elif b.blocker_type == BlockerType.EXTRACTION_FAILED:
            action_candidates.append("fix_extraction")
        elif b.blocker_type == BlockerType.DOCUMENT_REVIEW_REQUIRED:
            action_candidates.append("review_document")

    if consistency_review_needed:
        action_candidates.append("consistency_review")
    if sla_breached:
        action_candidates.append("sla_attention")

    if not action_candidates:
        return "complete"

    return min(action_candidates, key=lambda a: _ACTION_PRIORITY.get(a, 999))


def _build_explanation(
    applicability_eval: ApplicabilityEvaluation | None,
    dep_readiness: ApprovalReadiness | None,
    doc_readiness_label: str,
    status: OrchestrationStatus,
    blockers: list[BlockerDetail],
) -> str:
    """Build a human-readable explanation of the orchestration result."""
    parts: list[str] = []

    if applicability_eval:
        parts.append(f"Applicability: {applicability_eval.result} — {applicability_eval.reason}")

    if dep_readiness:
        parts.append(f"Dependencies: {dep_readiness.readiness.value} — {dep_readiness.explanation}")

    parts.append(f"Documents: {doc_readiness_label}")

    if blockers:
        parts.append(f"Blockers ({len(blockers)}): " + "; ".join(b.description for b in blockers))
    else:
        parts.append("No blockers.")

    parts.append(f"Status: {status.value}")
    return " | ".join(parts)


def orchestrate_application(
    application_id: str,
    approval_id: str,
    project_facts: dict[str, Any],
    approval_rules: list[ApprovalRule],
    approval_authorities: dict[str, str],
    dependencies: list[ApprovalDependency],
    document_requirements: list[dict[str, Any]],
    uploaded_documents: list[dict[str, Any]],
    extraction_results: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
    consistency_result: Any | None,
    sla_info: Any | None,
    obtained_approvals: set[str],
) -> ApprovalOrchestration:
    """Orchestrate readiness assessment for a single approval.

    Combines applicability evaluation, dependency readiness, document
    completeness, consistency, and SLA checks into a unified status.
    """
    # 1. Run applicability
    applicability_evals = evaluate_approval_applicability(
        approval_rules, project_facts, approval_authorities, [approval_id]
    )
    by_approval = summarize_by_approval(applicability_evals)
    applicability_eval = by_approval.get(approval_id)
    applicability_result = applicability_eval.result if applicability_eval else "insufficient_data"

    # 2. Run dependency readiness
    applicability_results_map = {
        aid: ev.result for aid, ev in by_approval.items()
    }
    # Include this approval even if not in by_approval (for dependency graph completeness)
    if approval_id not in applicability_results_map:
        applicability_results_map[approval_id] = applicability_result

    dep_graph = evaluate_readiness(
        dependencies,
        applicability_results_map,
        obtained=obtained_approvals,
    )
    dep_readiness = dep_graph.readiness.get(approval_id)

    # 3. Compute document readiness
    doc_readiness_label, doc_summaries, doc_blockers, _ = _compute_document_readiness(
        approval_id, document_requirements, uploaded_documents,
        extraction_results, validation_results,
    )

    # 4. Consistency check
    consistency_review_needed = False
    if consistency_result is not None:
        outcome = getattr(consistency_result, "outcome", None)
        if outcome is None and isinstance(consistency_result, dict):
            outcome = consistency_result.get("outcome")
        if outcome == "REVIEW_REQUIRED":
            consistency_review_needed = True

    # 5. SLA check
    sla_breached = False
    if sla_info is not None:
        state = getattr(sla_info, "state", None)
        if state is None and isinstance(sla_info, dict):
            state = sla_info.get("state")
        if state == "breached":
            sla_breached = True

    # 6. Collect all blockers
    all_blockers = list(doc_blockers)
    if consistency_review_needed:
        all_blockers.append(
            BlockerDetail(
                blocker_type=BlockerType.CONSISTENCY_REVIEW,
                description="Consistency check requires review",
                affected_approval_id=approval_id,
                affected_document_key=None,
                source_ref="consistency_engine",
                evidence=(
                    f"Consistency outcome: "
                    f"{getattr(consistency_result, 'outcome', 'unknown')}"
                ),
                action_required="Review consistency findings",
            )
        )
    if sla_breached:
        all_blockers.append(
            BlockerDetail(
                blocker_type=BlockerType.SLA_BREACHED,
                description="SLA has been breached",
                affected_approval_id=approval_id,
                affected_document_key=None,
                source_ref="sla_engine",
                evidence=f"SLA state: {getattr(sla_info, 'state', 'unknown')}",
                action_required="Address SLA breach",
            )
        )

    has_doc_blockers = any(
        b.blocker_type in (
            BlockerType.DOCUMENT_MISSING,
            BlockerType.DOCUMENT_INVALID,
            BlockerType.EXTRACTION_FAILED,
        )
        for b in doc_blockers
    )
    has_doc_review = any(
        b.blocker_type == BlockerType.DOCUMENT_REVIEW_REQUIRED
        for b in doc_blockers
    )

    # 7. Determine status
    status = _determine_status(
        applicability_result,
        dep_readiness.readiness if dep_readiness else ReadinessStatus.PENDING_EVALUATION,
        has_doc_blockers,
        has_doc_review,
        consistency_review_needed,
        sla_breached,
    )

    # 8. Pick next action
    next_action = _pick_next_action(
        all_blockers, doc_readiness_label, consistency_review_needed, sla_breached
    )

    # 9. Build explanation
    explanation = _build_explanation(
        applicability_eval, dep_readiness, doc_readiness_label, status, all_blockers
    )

    dep_readiness_val = (
        dep_readiness.readiness.value if dep_readiness else "pending_evaluation"
    )
    consistency_val = (
        getattr(consistency_result, "outcome", None)
        if consistency_result else None
    )
    sla_val = (
        getattr(sla_info, "state", None) if sla_info else None
    )

    return ApprovalOrchestration(
        approval_id=approval_id,
        status=status,
        applicability_result=applicability_result,
        dependency_readiness=dep_readiness_val,
        document_readiness=doc_readiness_label,
        consistency_outcome=consistency_val,
        sla_state=sla_val,
        blockers=all_blockers,
        documents=doc_summaries,
        explanation=explanation,
        next_action=next_action,
    )


def orchestrate_application_full(
    application_id: str,
    project_facts: dict[str, Any],
    approval_rules: list[ApprovalRule],
    approval_authorities: dict[str, str],
    dependencies: list[ApprovalDependency],
    all_approval_ids: list[str],
    document_requirements: list[dict[str, Any]],
    uploaded_documents: list[dict[str, Any]],
    extraction_results: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
    consistency_result: Any | None,
    sla_info: Any | None,
    obtained_approvals: set[str],
) -> ApplicationOrchestration:
    """Orchestrate readiness assessment for all approvals in an application.

    Calls orchestrate_application() for each approval, then aggregates
    into an overall application status.
    """
    approvals: dict[str, ApprovalOrchestration] = {}
    total_blockers = 0
    candidate_actions: list[tuple[int, str, str | None, str | None]] = []

    for aid in all_approval_ids:
        orch = orchestrate_application(
            application_id=application_id,
            approval_id=aid,
            project_facts=project_facts,
            approval_rules=approval_rules,
            approval_authorities=approval_authorities,
            dependencies=dependencies,
            document_requirements=document_requirements,
            uploaded_documents=uploaded_documents,
            extraction_results=extraction_results,
            validation_results=validation_results,
            consistency_result=consistency_result,
            sla_info=sla_info,
            obtained_approvals=obtained_approvals,
        )
        approvals[aid] = orch
        total_blockers += len(orch.blockers)

        if orch.next_action and orch.next_action != "complete":
            priority = _ACTION_PRIORITY.get(orch.next_action, 999)
            candidate_actions.append(
                (priority, orch.next_action, orch.approval_id, None)
            )

    # Determine overall status (worst case)
    if not approvals:
        overall_status = OrchestrationStatus.READY
    else:
        overall_status = max(
            approvals.values(),
            key=lambda a: _STATUS_PRIORITY.get(a.status, 0),
        ).status

    # Pick highest-priority next action across all approvals
    next_action_model: NextAction | None = None
    if candidate_actions:
        candidate_actions.sort(key=lambda x: x[0])
        _, action_type, affected_aid, _ = candidate_actions[0]
        next_action_model = NextAction(
            action_type=action_type,
            description=f"Action required for approval {affected_aid}: {action_type}",
            affected_approval_id=affected_aid,
            affected_document_key=None,
            link_section="",
        )

    # Build explanation
    status_counts: dict[str, int] = {}
    for orch in approvals.values():
        status_counts[orch.status.value] = status_counts.get(orch.status.value, 0) + 1
    status_summary = ", ".join(
        f"{count} {status}" for status, count in status_counts.items()
    )
    explanation = (
        f"Application {application_id}: {len(approvals)} approvals evaluated. "
        f"Status distribution: {status_summary}. "
        f"Total blockers: {total_blockers}."
    )

    # Determine stage number from dependency graph
    applicability_results_map = {
        aid: orch.applicability_result for aid, orch in approvals.items()
    }
    dep_graph = evaluate_readiness(
        dependencies, applicability_results_map, obtained=obtained_approvals
    )
    stages = [
        dep_graph.readiness[aid].stage
        for aid in all_approval_ids
        if aid in dep_graph.readiness
        and dep_graph.readiness[aid].applicability != "does_not_apply"
    ]
    stage_number = max(stages) if stages else None

    return ApplicationOrchestration(
        application_id=application_id,
        overall_status=overall_status,
        approvals=approvals,
        total_blockers=total_blockers,
        next_action=next_action_model,
        stage_number=stage_number,
        explanation=explanation,
    )
