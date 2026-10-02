"""Orchestration endpoint — readiness/blocking status for an application."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    get_applications_repository,
    get_consistency_repository,
    get_documents_repository,
    get_project_facts_repository,
    get_workflow_events_repository,
)
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.orchestration.facts import (
    apply_derived_facts,
    resolve_project_facts,
)
from app.orchestration.service import orchestrate_application_full
from app.orchestration.whatif import WhatIfValidationError, run_whatif_assessment
from app.orchestration.whatif_models import WhatIfRequest
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.rules.dependency_models import ApprovalDependency
from app.rules.models import ApprovalRule
from app.seed.pack import UnknownPackError, resolve_persisted_pack
from app.workflow.sla import compute_application_sla

router = APIRouter()

# Terminal statuses that count as "obtained" for dependency satisfaction.
_TERMINAL_STATUSES = frozenset({"approved"})


def _load_extraction_results(
    docs_repo: DocumentsRepository,
    uploaded_docs: list[dict],
) -> list[dict]:
    """Load extraction results for each uploaded document."""
    results: list[dict] = []
    for doc in uploaded_docs:
        doc_id = doc.get("id")
        if not doc_id:
            continue
        ex = docs_repo.get_extraction_result_for_document(doc_id)
        if ex:
            results.append(ex)
    return results


def _load_validation_results(
    docs_repo: DocumentsRepository,
    uploaded_docs: list[dict],
) -> list[dict]:
    """Load validation results for each uploaded document."""
    results: list[dict] = []
    for doc in uploaded_docs:
        doc_id = doc.get("id")
        if not doc_id:
            continue
        val = docs_repo.get_validation_result_for_document(doc_id)
        if val:
            results.append(val)
    return results


def _load_consistency_result(
    consistency_repo: ConsistencyRepository,
    application_id: str,
) -> dict | None:
    """Load the latest consistency result, or None if no check has been run."""
    return consistency_repo.get_latest_result(application_id)


def _compute_obtained_approvals(
    app_repo: ApplicationsRepository,
    project_id: str | None,
    current_application_id: str,
) -> set[str]:
    """Determine which approvals have already been obtained for this project.

    An approval is considered "obtained" if there is an application in
    terminal/approved status for that approval within the same project.
    """
    if not project_id:
        return set()

    from uuid import UUID as _UUID

    try:
        sibling_apps = app_repo.get_by_project(_UUID(project_id))
    except (ValueError, TypeError):
        return set()

    obtained: set[str] = set()
    for app in sibling_apps:
        if app.get("id") == current_application_id:
            continue
        if app.get("status") in _TERMINAL_STATUSES:
            approval_code = app.get("approval_code")
            if approval_code:
                obtained.add(approval_code)
    return obtained


def _select_assessment_scope(
    approval_code: str | None,
    rules: list[ApprovalRule],
    dependencies: list[ApprovalDependency],
) -> list[str]:
    """Resolve the application's own approval plus transitive prerequisites.

    Uses the existing dependency edges (no second implementation): breadth-first
    traversal from the own approval over prerequisite_approval_id links, guarded
    by a visited set so cyclic seed data cannot loop. Only codes backed by a
    seed rule are included. Own approval comes first for determinism.
    """
    if not approval_code:
        raise HTTPException(
            status_code=422, detail="Application has no approval_code"
        )
    known = {rule.approval_id for rule in rules}
    if approval_code not in known:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid approval_code: '{approval_code}'",
        )
    prereq_map: dict[str, list[str]] = {}
    for dep in dependencies:
        prereq_map.setdefault(dep.approval_id, []).append(
            dep.prerequisite_approval_id
        )
    ordered = [approval_code]
    seen = {approval_code}
    queue = [approval_code]
    while queue:
        current = queue.pop(0)
        for prereq in prereq_map.get(current, []):
            if prereq not in seen and prereq in known:
                seen.add(prereq)
                ordered.append(prereq)
                queue.append(prereq)
    return ordered


def _load_baseline_inputs(
    application: dict,
    application_id: UUID,
    repo: ApplicationsRepository,
    facts_repo: ProjectFactsRepository,
    docs_repo: DocumentsRepository,
    events_repo: WorkflowEventsRepository,
    consistency_repo: ConsistencyRepository,
) -> dict:
    """Load the exact baseline inputs shared by GET orchestration and What-If.

    Read-only: never persists anything. Returned facts are resolved through
    the shared resolver (typed columns plus flattened facts_json).
    Regulatory data resolves from the application's persisted
    (jurisdiction, pack_version) — never from the global default.
    Unscoped or unknown pairs fail closed with HTTP 422.
    """
    project_id = application.get("project_id")
    app_id_str = str(application_id)

    facts: dict = {}
    if project_id:
        facts_record = facts_repo.get_by_project(project_id)
        facts = resolve_project_facts(facts_record)

    uploaded_docs = docs_repo.list_documents_for_application(app_id_str)
    # Single regulatory boundary: the persisted application identity
    # selects the pack. No DEFAULT_JURISDICTION fallback for records.
    try:
        pack = resolve_persisted_pack(
            application.get("jurisdiction"), application.get("pack_version")
        )
    except UnknownPackError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # Single derivation point: IN-MH missing derived facts (F-INC-01,
    # F-PRC-03) are computed here via derive_mh_facts; every consumer
    # below (orchestration, What-If, handoffs, rehearse) shares the
    # merged facts. IN-GJ passes through unchanged.
    facts, fact_provenance = apply_derived_facts(facts, pack.jurisdiction)
    doc_requirements = pack.document_requirements
    extraction_results = _load_extraction_results(docs_repo, uploaded_docs)
    validation_results = _load_validation_results(docs_repo, uploaded_docs)
    consistency_result = _load_consistency_result(consistency_repo, app_id_str)

    events = events_repo.list_for_application(app_id_str)
    approval_id = application.get("approval_id")
    stages = repo.get_approval_stages(approval_id) if approval_id else []
    sla_info = compute_application_sla(
        status=application.get("status"),
        current_stage=application.get("current_stage"),
        submitted_at=application.get("submitted_at"),
        created_at=application.get("created_at"),
        workflow_events=events,
        stages=stages or [],
    )

    obtained = _compute_obtained_approvals(repo, project_id, app_id_str)

    rules = pack.approval_rules
    authorities = pack.approval_authorities
    dependencies = pack.dependencies

    approval_code = application.get("approval_code")
    all_approval_ids = _select_assessment_scope(approval_code, rules, dependencies)
    evidence_gaps_by_approval = {
        aid: pack.get_gaps_for_approval(aid) for aid in all_approval_ids
    }

    return {
        "application_id": app_id_str,
        "jurisdiction": pack.jurisdiction,
        "pack": pack,
        "facts": facts,
        "fact_provenance": fact_provenance,
        "uploaded_docs": uploaded_docs,
        "doc_requirements": doc_requirements,
        "extraction_results": extraction_results,
        "validation_results": validation_results,
        "consistency_result": consistency_result,
        "sla_info": sla_info,
        "obtained": obtained,
        "rules": rules,
        "authorities": authorities,
        "dependencies": dependencies,
        "all_approval_ids": all_approval_ids,
        "evidence_gaps_by_approval": evidence_gaps_by_approval,
    }


@router.get("/applications/{application_id}/orchestration")
async def get_application_orchestration(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    facts_repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    docs_repo: DocumentsRepository = Depends(get_documents_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    consistency_repo: ConsistencyRepository = Depends(
        get_consistency_repository
    ),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get orchestration readiness status for an application.

    Returns per-approval readiness, blockers, next action, and overall status.
    Incorporates extraction results, validation results, consistency checks,
    SLA state, dependency satisfaction from sibling applications, and
    relevant G0-R5 evidence gaps (surfaced as INSUFFICIENT_DATA).
    """
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    inputs = _load_baseline_inputs(
        application,
        application_id,
        repo,
        facts_repo,
        docs_repo,
        events_repo,
        consistency_repo,
    )

    # Run orchestration
    result = orchestrate_application_full(
        application_id=inputs["application_id"],
        project_facts=inputs["facts"],
        approval_rules=inputs["rules"],
        approval_authorities=inputs["authorities"],
        dependencies=inputs["dependencies"],
        all_approval_ids=inputs["all_approval_ids"],
        document_requirements=inputs["doc_requirements"],
        uploaded_documents=inputs["uploaded_docs"],
        extraction_results=inputs["extraction_results"],
        validation_results=inputs["validation_results"],
        consistency_result=inputs["consistency_result"],
        sla_info=inputs["sla_info"],
        obtained_approvals=inputs["obtained"],
        evidence_gaps_by_approval=inputs["evidence_gaps_by_approval"],
        fact_provenance=inputs["fact_provenance"],
        approval_compositions=inputs["pack"].approval_compositions,
    )

    return result.model_dump()


@router.post("/applications/{application_id}/orchestration/what-if")
async def post_application_whatif(
    application_id: UUID,
    request: WhatIfRequest,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    facts_repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    docs_repo: DocumentsRepository = Depends(get_documents_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    consistency_repo: ConsistencyRepository = Depends(
        get_consistency_repository
    ),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Stateless What-If recalculation for an application.

    Applies temporary fact overrides in memory, re-runs the same
    deterministic orchestration pipeline for baseline and what-if, and
    returns the comparison. Never persists overrides; never writes to
    project_facts, projects, applications, documents, workflow, or
    evidence stores.
    """
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    inputs = _load_baseline_inputs(
        application,
        application_id,
        repo,
        facts_repo,
        docs_repo,
        events_repo,
        consistency_repo,
    )

    try:
        result = run_whatif_assessment(
            application_id=inputs["application_id"],
            base_facts=inputs["facts"],
            fact_overrides=request.fact_overrides,
            approval_rules=inputs["rules"],
            approval_authorities=inputs["authorities"],
            dependencies=inputs["dependencies"],
            all_approval_ids=inputs["all_approval_ids"],
            document_requirements=inputs["doc_requirements"],
            uploaded_documents=inputs["uploaded_docs"],
            extraction_results=inputs["extraction_results"],
            validation_results=inputs["validation_results"],
            consistency_result=inputs["consistency_result"],
            sla_info=inputs["sla_info"],
            obtained_approvals=inputs["obtained"],
            evidence_gaps_by_approval=inputs["evidence_gaps_by_approval"],
            include_unchanged=request.include_unchanged,
            jurisdiction=inputs["jurisdiction"],
            fact_provenance=inputs["fact_provenance"],
            approval_compositions=inputs["pack"].approval_compositions,
        )
    except WhatIfValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return result.model_dump()
