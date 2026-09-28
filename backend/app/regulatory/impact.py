"""Stateless regulatory change rehearsal engine.

Flow per change:
  descriptor -> affected rules/approvals (seed scan, no persisted index)
  -> old inputs -> orchestrate_application_full()
  -> new inputs -> orchestrate_application_full()
  -> compare_orchestrations() (reused, never duplicated)
  -> RESULT_CHANGED / SOURCE_RELEVANT / NO_IMPACT

Reuses resolve_project_facts inputs as given, the full orchestration
pipeline, evidence-gap handling, dependency evaluation, blocker
signatures, and diff logic. Seed data is read, never written. The unused
DB approval_rules table is never consulted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.orchestration.service import orchestrate_application_full
from app.orchestration.whatif import compare_orchestrations
from app.regulatory.evidence import EvidenceRecord, EvidenceStatus
from app.regulatory.impact_models import (
    ChangeDescriptor,
    ChangeKind,
    ImpactClassification,
    ProjectImpact,
)
from app.rules.dependency_models import ApprovalDependency
from app.rules.models import ApprovalRule
from app.seed.evidence_gaps import EVIDENCE_TO_APPROVALS, load_evidence_gaps


class ImpactValidationError(ValueError):
    """Raised for unknown references or malformed change payloads (API -> 422)."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


@dataclass
class RehearsalInputs:
    """Everything orchestration needs, loaded once by the caller."""

    base_facts: dict[str, Any]
    approval_rules: list[ApprovalRule]
    approval_authorities: dict[str, str]
    dependencies: list[ApprovalDependency]
    all_approval_ids: list[str]
    document_requirements: list[dict[str, Any]]
    uploaded_documents: list[dict[str, Any]] = field(default_factory=list)
    extraction_results: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    consistency_result: Any | None = None
    sla_info: Any | None = None
    obtained_approvals: set[str] = field(default_factory=set)
    evidence_gaps_by_approval: dict[str, list[EvidenceRecord]] | None = None
    # Pack-derived registries for source/evidence validation. None means
    # the legacy Gujarat seed registries (GJ behavior unchanged).
    known_source_ids: set[str] | None = None
    evidence_registry: list[EvidenceRecord] | None = None
    evidence_hints: dict[str, list[str]] | None = None


def _known_source_ids() -> set[str]:
    from app.seed.sources import load_regulatory_sources

    return {s.id for s in load_regulatory_sources()}


def _resolve_known_source_ids(inputs: RehearsalInputs) -> set[str]:
    if inputs.known_source_ids is not None:
        return inputs.known_source_ids
    return _known_source_ids()


def _resolve_evidence_registry(
    inputs: RehearsalInputs,
) -> dict[str, EvidenceRecord]:
    if inputs.evidence_registry is not None:
        return {g.evidence_id: g for g in inputs.evidence_registry}
    return {g.evidence_id: g for g in load_evidence_gaps()}


def rules_citing_source(
    source_id: str, rules: list[ApprovalRule]
) -> list[ApprovalRule]:
    """Seed scan: rules whose source_refs contain source_id (no persisted index)."""
    return [
        r
        for r in rules
        if any(ref.source_id == source_id for ref in r.source_refs)
    ]


def _summarize(orch) -> dict[str, dict[str, str]]:
    return {
        aid: {
            "status": o.status.value,
            "applicability": o.applicability_result,
            "dependency": o.dependency_readiness,
        }
        for aid, o in orch.approvals.items()
    }


def _run(inputs: RehearsalInputs, *, rules=None, deps=None, reqs=None, gaps=None):
    return orchestrate_application_full(
        application_id="REHEARSAL",
        project_facts=dict(inputs.base_facts),
        approval_rules=rules if rules is not None else inputs.approval_rules,
        approval_authorities=inputs.approval_authorities,
        dependencies=deps if deps is not None else inputs.dependencies,
        all_approval_ids=list(inputs.all_approval_ids),
        document_requirements=reqs if reqs is not None else inputs.document_requirements,
        uploaded_documents=list(inputs.uploaded_documents),
        extraction_results=list(inputs.extraction_results),
        validation_results=list(inputs.validation_results),
        consistency_result=inputs.consistency_result,
        sla_info=inputs.sla_info,
        obtained_approvals=set(inputs.obtained_approvals),
        evidence_gaps_by_approval=gaps if gaps is not None else inputs.evidence_gaps_by_approval,
    )


def _classify(diff, affected_in_scope: list[str]) -> ImpactClassification:
    if not diff.no_change:
        return ImpactClassification.RESULT_CHANGED
    if affected_in_scope:
        return ImpactClassification.SOURCE_RELEVANT
    return ImpactClassification.NO_IMPACT


def _in_scope(ids: list[str], inputs: RehearsalInputs) -> list[str]:
    scope = set(inputs.all_approval_ids)
    return sorted(aid for aid in ids if aid in scope)


def _parse_rule(raw: Any, what: str) -> ApprovalRule:
    if not isinstance(raw, dict):
        raise ImpactValidationError(f"{what} must be an ApprovalRule object")
    try:
        return ApprovalRule(**raw)
    except Exception as exc:
        raise ImpactValidationError(f"{what} is not a valid ApprovalRule: {exc}") from exc


def _rehearse_rule_change(change: ChangeDescriptor, inputs: RehearsalInputs) -> ProjectImpact:
    current = next((r for r in inputs.approval_rules if r.id == change.rule_id), None)
    if current is None:
        raise ImpactValidationError(f"Unknown rule_id '{change.rule_id}'")
    old_rule = _parse_rule(change.old_value, "old_value")
    new_rule = _parse_rule(change.new_value, "new_value")
    for label, rule in (("old_value", old_rule), ("new_value", new_rule)):
        if rule.id != change.rule_id or rule.approval_id != current.approval_id:
            raise ImpactValidationError(
                f"{label} must carry rule_id '{change.rule_id}' "
                f"for approval '{current.approval_id}'"
            )
    if old_rule.model_dump() != current.model_dump():
        raise ImpactValidationError(
            f"old_value does not match the current '{change.rule_id}' rule"
        )
    known_sources = _resolve_known_source_ids(inputs)
    for label, rule in (("old_value", old_rule), ("new_value", new_rule)):
        unknown = [ref.source_id for ref in rule.source_refs if ref.source_id not in known_sources]
        if unknown:
            raise ImpactValidationError(f"{label} cites unknown sources: {unknown}")

    old_rules = [old_rule if r.id == change.rule_id else r for r in inputs.approval_rules]
    new_rules = [new_rule if r.id == change.rule_id else r for r in inputs.approval_rules]
    baseline = _run(inputs, rules=old_rules)
    new = _run(inputs, rules=new_rules)
    diff = compare_orchestrations(baseline, new)
    affected = _in_scope([current.approval_id], inputs)
    classification = _classify(diff, affected)
    if classification == ImpactClassification.RESULT_CHANGED:
        reason = (
            f"Rule {change.rule_id} (approval {current.approval_id}) rehearsed "
            f"old vs new: deterministic results differ."
        )
    elif affected:
        reason = (
            f"Rule {change.rule_id} (approval {current.approval_id}) rehearsed "
            f"old vs new: cited rule is linked, but deterministic results are identical."
        )
    else:
        reason = (
            f"Rule {change.rule_id} (approval {current.approval_id}) is outside "
            f"the rehearsed scope; no relationship to this scope."
        )
    return ProjectImpact(
        classification=classification,
        affected_approvals=affected,
        affected_rule_ids=[change.rule_id] if affected else [],
        source_ids=sorted({ref.source_id for ref in new_rule.source_refs}) if affected else [],
        baseline_overall=baseline.overall_status.value,
        new_overall=new.overall_status.value,
        diffs=diff.changed_approvals,
        baseline_results=_summarize(baseline),
        new_results=_summarize(new),
        reason=reason,
        evidence_caveats=[],
        change=change,
    )


def _rehearse_document_change(
    change: ChangeDescriptor, inputs: RehearsalInputs
) -> ProjectImpact:
    key = change.requirement_key or ""
    current = next(
        (r for r in inputs.document_requirements if r.get("requirement_key") == key),
        None,
    )
    if current is None:
        raise ImpactValidationError(f"Unknown requirement_key '{key}'")
    if not isinstance(change.old_value, dict) or not isinstance(change.new_value, dict):
        raise ImpactValidationError("old_value/new_value must be requirement objects")
    if change.old_value.get("requirement_key") != key or change.new_value.get(
        "requirement_key", key
    ) not in (key, None):
        raise ImpactValidationError("requirement_key must match in old/new_value")
    all_reqs = list(inputs.document_requirements)
    old_reqs = [change.old_value if r.get("requirement_key") == key else r for r in all_reqs]
    new_reqs = [change.new_value if r.get("requirement_key") == key else r for r in all_reqs]
    old_ids = set(current.get("approval_ids", []))
    new_ids = set(change.new_value.get("approval_ids", old_ids))
    affected = _in_scope(sorted(old_ids | new_ids), inputs)
    baseline = _run(inputs, reqs=old_reqs)
    new = _run(inputs, reqs=new_reqs)
    diff = compare_orchestrations(baseline, new)
    classification = _classify(diff, affected)
    if classification == ImpactClassification.RESULT_CHANGED:
        reason = (
            f"Document requirement {key} rehearsed old vs new: document readiness "
            f"differs; applicability reasoning is unchanged (documents do not "
            f"alter applicability)."
        )
    elif affected:
        reason = (
            f"Document requirement {key} rehearsed old vs new: linked approvals "
            f"{', '.join(affected)}, but document readiness is identical."
        )
    else:
        reason = f"Document requirement {key} links to no approval in this scope."
    return ProjectImpact(
        classification=classification,
        affected_approvals=affected,
        affected_rule_ids=[],
        source_ids=[],
        baseline_overall=baseline.overall_status.value,
        new_overall=new.overall_status.value,
        diffs=diff.changed_approvals,
        baseline_results=_summarize(baseline),
        new_results=_summarize(new),
        reason=reason,
        evidence_caveats=[],
        change=change,
    )


def _parse_dependency(raw: Any, known_codes: set[str], what: str) -> ApprovalDependency:
    if not isinstance(raw, dict):
        raise ImpactValidationError(f"{what} must be a dependency object")
    try:
        dep = ApprovalDependency(**raw)
    except Exception as exc:
        raise ImpactValidationError(f"{what} is not a valid dependency: {exc}") from exc
    for code in (dep.approval_id, dep.prerequisite_approval_id):
        if code not in known_codes:
            raise ImpactValidationError(f"{what} references unknown approval '{code}'")
    return dep


def _rehearse_dependency_change(
    change: ChangeDescriptor, inputs: RehearsalInputs
) -> ProjectImpact:
    known_codes = {r.approval_id for r in inputs.approval_rules}
    old_dep = (
        _parse_dependency(change.old_value, known_codes, "old_value")
        if change.old_value is not None
        else None
    )
    new_dep = (
        _parse_dependency(change.new_value, known_codes, "new_value")
        if change.new_value is not None
        else None
    )
    if old_dep is None and new_dep is None:
        raise ImpactValidationError("DEPENDENCY_CHANGE needs old_value and/or new_value")
    current = list(inputs.dependencies)

    def _key(d: ApprovalDependency) -> tuple[str, str]:
        return (d.approval_id, d.prerequisite_approval_id)

    if old_dep is not None and all(_key(d) != _key(old_dep) for d in current):
        raise ImpactValidationError("old_value matches no current dependency edge")
    if old_dep is None and new_dep is not None and any(
        _key(d) == _key(new_dep) for d in current
    ):
        raise ImpactValidationError("new_value duplicates a current dependency edge")

    if old_dep is None:
        old_deps, new_deps = current, current + [new_dep]  # type: ignore[operator]
        involved = [new_dep.approval_id, new_dep.prerequisite_approval_id]  # type: ignore[union-attr]
    elif new_dep is None:
        old_deps = current
        new_deps = [d for d in current if _key(d) != _key(old_dep)]
        involved = [old_dep.approval_id, old_dep.prerequisite_approval_id]
    else:
        old_deps = [new_dep if _key(d) == _key(old_dep) else d for d in current]
        new_deps = [new_dep if _key(d) == _key(old_dep) else d for d in current]
        # Replace-by-key where keys are equal; differing keys mean remove+add.
        if _key(old_dep) != _key(new_dep):
            new_deps = [d for d in current if _key(d) != _key(old_dep)] + [new_dep]
        involved = [old_dep.approval_id, old_dep.prerequisite_approval_id,
                    new_dep.approval_id, new_dep.prerequisite_approval_id]
    affected = _in_scope(sorted(set(involved)), inputs)
    baseline = _run(inputs, deps=old_deps)
    new = _run(inputs, deps=new_deps)
    diff = compare_orchestrations(baseline, new)
    classification = _classify(diff, affected)
    if classification == ImpactClassification.RESULT_CHANGED:
        reason = (
            "Dependency set rehearsed old vs new: readiness results differ; "
            "downstream effects follow the existing dependency engine."
        )
    elif affected:
        reason = (
            "Dependency set rehearsed old vs new: linked approvals found, "
            "but readiness results are identical."
        )
    else:
        reason = "Dependency change links to no approval in this scope."
    return ProjectImpact(
        classification=classification,
        affected_approvals=affected,
        affected_rule_ids=[],
        source_ids=[],
        baseline_overall=baseline.overall_status.value,
        new_overall=new.overall_status.value,
        diffs=diff.changed_approvals,
        baseline_results=_summarize(baseline),
        new_results=_summarize(new),
        reason=reason,
        evidence_caveats=[],
        change=change,
    )


def _rehearse_evidence_change(
    change: ChangeDescriptor, inputs: RehearsalInputs
) -> ProjectImpact:
    known = _resolve_evidence_registry(inputs)
    record = known.get(change.evidence_id or "")
    if record is None:
        raise ImpactValidationError(f"Unknown evidence_id '{change.evidence_id}'")
    try:
        old_status = EvidenceStatus(change.old_status)
        new_status = EvidenceStatus(change.new_status)
    except ValueError as exc:
        raise ImpactValidationError(f"Invalid evidence status: {exc}") from exc
    if old_status.value != record.status.value:
        raise ImpactValidationError(
            f"old_status '{change.old_status}' does not match current '{record.status.value}'"
        )
    hints = (
        inputs.evidence_hints
        if inputs.evidence_hints is not None
        else EVIDENCE_TO_APPROVALS
    )
    mapped = hints.get(record.evidence_id, [])
    affected = _in_scope(list(mapped), inputs)

    def _variant(status: EvidenceStatus) -> dict[str, list[EvidenceRecord]]:
        out: dict[str, list[EvidenceRecord]] = {}
        for aid in inputs.all_approval_ids:
            rows = (inputs.evidence_gaps_by_approval or {}).get(aid, [])
            out[aid] = [
                r.model_copy(update={"status": status})
                if r.evidence_id == record.evidence_id
                else r
                for r in rows
            ]
        return out

    baseline = _run(inputs, gaps=_variant(old_status))
    new = _run(inputs, gaps=_variant(new_status))
    diff = compare_orchestrations(baseline, new)
    classification = _classify(diff, affected)
    caveats = [
        f"Evidence {record.evidence_id} rehearsed {old_status.value} -> {new_status.value}; "
        "only VERIFIED evidence can resolve a gap; all other states fail closed."
    ]
    if classification == ImpactClassification.RESULT_CHANGED:
        reason = (
            f"Evidence {record.evidence_id} rehearsed {old_status.value} -> "
            f"{new_status.value}: deterministic output differs."
        )
    elif affected:
        reason = (
            f"Evidence {record.evidence_id} rehearsed {old_status.value} -> "
            f"{new_status.value}: linked approvals found, but deterministic output is identical."
        )
    else:
        reason = f"Evidence {record.evidence_id} links to no approval in this scope."
    return ProjectImpact(
        classification=classification,
        affected_approvals=affected,
        affected_rule_ids=[],
        source_ids=[],
        baseline_overall=baseline.overall_status.value,
        new_overall=new.overall_status.value,
        diffs=diff.changed_approvals,
        baseline_results=_summarize(baseline),
        new_results=_summarize(new),
        reason=reason,
        evidence_caveats=caveats,
        change=change,
    )


def _rehearse_source_metadata(
    change: ChangeDescriptor, inputs: RehearsalInputs
) -> ProjectImpact:
    known = _resolve_known_source_ids(inputs)
    if (change.source_id or "") not in known:
        raise ImpactValidationError(f"Unknown source_id '{change.source_id}'")
    if change.old_value == change.new_value:
        return ProjectImpact(
            classification=ImpactClassification.NO_IMPACT,
            affected_approvals=[],
            affected_rule_ids=[],
            source_ids=[change.source_id or ""],
            reason=f"Source {change.source_id} metadata identical old vs new: nothing to rehearse.",
            evidence_caveats=[],
            change=change,
        )
    citing = rules_citing_source(change.source_id or "", inputs.approval_rules)
    affected = _in_scope(sorted({r.approval_id for r in citing}), inputs)
    if not affected:
        return ProjectImpact(
            classification=ImpactClassification.NO_IMPACT,
            affected_approvals=[],
            affected_rule_ids=[],
            source_ids=[change.source_id or ""],
            reason=(
                f"Source {change.source_id} is cited by no rule in this scope: "
                "no relationship to rehearse."
            ),
            evidence_caveats=[],
            change=change,
        )
    rule_ids = sorted({r.id for r in citing if r.approval_id in set(affected)})
    baseline = _run(inputs)
    summary = _summarize(baseline)
    return ProjectImpact(
        classification=ImpactClassification.SOURCE_RELEVANT,
        affected_approvals=affected,
        affected_rule_ids=rule_ids,
        source_ids=[change.source_id or ""],
        baseline_overall=baseline.overall_status.value,
        new_overall=baseline.overall_status.value,
        diffs=[],
        baseline_results=summary,
        new_results=dict(summary),
        reason=(
            f"Source {change.source_id} is cited by rules {', '.join(rule_ids)}; "
            "metadata alone is not consumed by the decision engine, so results "
            "cannot differ — human review of the cited rules is advised."
        ),
        evidence_caveats=[
            "Provenance metadata (title, URL, checked date, authority wording) "
            "carries no legal conclusion."
        ],
        change=change,
    )


def rehearse_impact(change: ChangeDescriptor, inputs: RehearsalInputs) -> ProjectImpact:
    """Rehearse one change against one scope. Pure: no reads, no writes."""
    kind = change.change_kind
    if kind == ChangeKind.RULE_CHANGE:
        return _rehearse_rule_change(change, inputs)
    if kind == ChangeKind.DOCUMENT_REQUIREMENT_CHANGE:
        return _rehearse_document_change(change, inputs)
    if kind == ChangeKind.DEPENDENCY_CHANGE:
        return _rehearse_dependency_change(change, inputs)
    if kind == ChangeKind.EVIDENCE_STATUS_CHANGE:
        return _rehearse_evidence_change(change, inputs)
    if kind == ChangeKind.SOURCE_METADATA_CHANGE:
        return _rehearse_source_metadata(change, inputs)
    raise ImpactValidationError(f"Unsupported change_kind '{kind}'")
