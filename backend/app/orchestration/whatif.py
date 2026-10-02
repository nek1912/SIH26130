"""Stateless What-If recalculation.

Persisted facts -> resolve -> baseline orchestrate -> apply temporary
overrides (copy) -> what-if orchestrate -> deterministic comparison.

Reuses the existing pipeline wholesale (applicability, dependencies,
documents, consistency, SLA, evidence gaps, status, next action). No second
rules implementation, no persistence, no LLM.
"""
from __future__ import annotations

import re
from typing import Any

from app.orchestration.facts import apply_derived_facts
from app.orchestration.models import (
    ApplicationOrchestration,
    BlockerDetail,
)
from app.orchestration.service import orchestrate_application_full
from app.orchestration.whatif_models import (
    ApprovalDiff,
    WhatIfComparison,
    WhatIfResponse,
)
from app.rules.facts import (
    GJ_JURISDICTION,
    MH_JURISDICTION,
    FactValidationError,
    validate_fact_value,
)
from app.rules.models import ApprovalComposition, ApprovalRule
from app.rules.validation import ALLOWED_FIELDS

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_JURISDICTION_RE = re.compile(r"^IN(-[A-Z]{2})?$")

_BOOLEAN_FIELDS = frozenset(
    {
        "new_project",
        "hazardous_chemicals_handled",
        "hazardous_waste_generated",
        "fire_safety_certificate_candidate",
        "lift_present",
        "boiler_present",
        "groundwater_use",
        "tree_felling",
    }
)

_NUMERIC_FIELDS = frozenset(
    {
        "headcount",
        "annual_turnover_inr",
        "plot_area_sqm",
        "builtup_area_sqm",
        "production_capacity",
        "fresh_water_requirement",
        "process_water",
        "domestic_water",
        "effluent_generation",
        "ETP_capacity",
        "power_demand",
        "DG_capacity",
        "workers_total",
        "workers_powered_factory",
        "building_height",
    }
)

_VALID_ENTITY_TYPES = frozenset(
    {
        "proprietorship",
        "partnership",
        "llp",
        "pvt-ltd",
        "public-ltd",
        "opc",
        "huf",
        "trust",
        "society",
    }
)


class WhatIfValidationError(ValueError):
    """Raised for unknown fields or invalid override value types (API -> 422)."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Invalid fact override '{field}': {reason}")


def _check_override_value(field: str, value: Any) -> str | None:
    """Return an error reason, or None when the value type is acceptable."""
    if field in _BOOLEAN_FIELDS:
        if not isinstance(value, bool):
            return "value must be a boolean"
        return None
    if field in _NUMERIC_FIELDS:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "value must be a number"
        return None
    if field == "jurisdictions":
        if not isinstance(value, list) or not all(
            isinstance(v, str) and _JURISDICTION_RE.match(v) for v in value
        ):
            return "value must match the Jurisdiction shape (IN or IN-XX)"
        return None
    if field == "registered_state":
        if not isinstance(value, str) or not _JURISDICTION_RE.match(value):
            return "value must match the Jurisdiction shape (IN or IN-XX)"
        return None
    if field == "entity_type":
        if not isinstance(value, str) or value not in _VALID_ENTITY_TYPES:
            return "value must match the EntityType enum"
        return None
    if field == "incorporation_date":
        if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
            return "value must be an ISO date string (YYYY-MM-DD)"
        return None
    if field in ("headcount", "annual_turnover_inr"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "value must be a number"
        return None
    return None


def apply_fact_overrides(
    base_facts: dict[str, Any],
    overrides: dict[str, Any],
    jurisdiction: str = GJ_JURISDICTION,
) -> dict[str, Any]:
    """Merge temporary overrides onto a copy of base facts.

    IN-GJ (default): legacy behavior, unchanged — only fields in
    ALLOWED_FIELDS or already present in base_facts are accepted;
    unknown fields and mistyped values raise WhatIfValidationError;
    None removes the key; never mutates base_facts; no type coercion.

    IN-MH: overrides are validated against the MH fact registry
    (unknown field / wrong type / invalid enum / jurisdiction
    mismatch all raise WhatIfValidationError); None removes the key;
    never mutates base_facts.

    Any other jurisdiction raises WhatIfValidationError explicitly.
    """
    if jurisdiction != GJ_JURISDICTION and jurisdiction != MH_JURISDICTION:
        raise WhatIfValidationError(
            "jurisdiction", f"unknown jurisdiction {jurisdiction!r}"
        )
    if jurisdiction == MH_JURISDICTION:
        for field, value in overrides.items():
            if value is None:
                continue
            try:
                validate_fact_value(MH_JURISDICTION, field, value)
            except FactValidationError as exc:
                raise WhatIfValidationError(
                    field, f"{exc.reason} [{exc.code}]"
                ) from exc
        merged = dict(base_facts)
        for field, value in overrides.items():
            if value is None:
                merged.pop(field, None)
            else:
                merged[field] = value
        return merged
    allowed = set(ALLOWED_FIELDS) | set(base_facts.keys())
    # Discharge mode is a validated scenario field missing from ALLOWED_FIELDS.
    allowed.add("discharge_mode")
    for field, value in overrides.items():
        if field not in allowed:
            raise WhatIfValidationError(field, "unknown fact field")
        if value is None:
            continue
        reason = _check_override_value(field, value)
        if reason is not None:
            # Fields outside the typed rule vocabulary (e.g. raw material
            # lists already stored on the project) accept any JSON value;
            # they cannot affect deterministic rules either way.
            if field not in ALLOWED_FIELDS and field != "discharge_mode":
                continue
            raise WhatIfValidationError(field, reason)
    merged = dict(base_facts)
    for field, value in overrides.items():
        if value is None:
            merged.pop(field, None)
        else:
            merged[field] = value
    return merged


def _blocker_signature(blocker: BlockerDetail) -> tuple[str, str, str, str, str]:
    return (
        blocker.blocker_type.value
        if hasattr(blocker.blocker_type, "value")
        else str(blocker.blocker_type),
        blocker.affected_approval_id or "",
        blocker.affected_document_key or "",
        blocker.evidence_id or "",
        blocker.description,
    )


def compare_orchestrations(
    baseline: ApplicationOrchestration,
    what_if: ApplicationOrchestration,
    include_unchanged: bool = False,
) -> WhatIfComparison:
    """Pure deterministic diff of two independently evaluated orchestrations."""
    all_ids = sorted(set(baseline.approvals.keys()) | set(what_if.approvals.keys()))
    changed: list[ApprovalDiff] = []
    unchanged: list[str] = []
    added_all: list[BlockerDetail] = []
    removed_all: list[BlockerDetail] = []

    for aid in all_ids:
        base = baseline.approvals.get(aid)
        alt = what_if.approvals.get(aid)
        if base is None or alt is None:
            # Scope is fixed per application; treat presence-only drift as
            # changed with the available side carried through.
            changed.append(
                ApprovalDiff(
                    approval_id=aid,
                    baseline_applicability=base.applicability_result if base else "",
                    whatif_applicability=alt.applicability_result if alt else "",
                    baseline_status=base.status.value if base else "",
                    whatif_status=alt.status.value if alt else "",
                    baseline_dependency=base.dependency_readiness if base else "",
                    whatif_dependency=alt.dependency_readiness if alt else "",
                    added_blockers=list(alt.blockers) if alt else [],
                    removed_blockers=list(base.blockers) if base else [],
                    baseline_explanation=base.explanation if base else "",
                    whatif_explanation=alt.explanation if alt else "",
                )
            )
            continue
        base_sigs = {_blocker_signature(b) for b in base.blockers}
        alt_sigs = {_blocker_signature(b) for b in alt.blockers}
        added = [b for b in alt.blockers if _blocker_signature(b) not in base_sigs]
        removed = [b for b in base.blockers if _blocker_signature(b) not in alt_sigs]
        status_changed = base.status != alt.status
        applicability_changed = base.applicability_result != alt.applicability_result
        dependency_changed = base.dependency_readiness != alt.dependency_readiness
        if status_changed or applicability_changed or dependency_changed or added or removed:
            changed.append(
                ApprovalDiff(
                    approval_id=aid,
                    baseline_applicability=base.applicability_result,
                    whatif_applicability=alt.applicability_result,
                    baseline_status=base.status.value,
                    whatif_status=alt.status.value,
                    baseline_dependency=base.dependency_readiness,
                    whatif_dependency=alt.dependency_readiness,
                    added_blockers=added,
                    removed_blockers=removed,
                    # Explanations are engine output carried verbatim; never
                    # generated here.
                    baseline_explanation=base.explanation,
                    whatif_explanation=alt.explanation,
                )
            )
            added_all.extend(added)
            removed_all.extend(removed)
        else:
            unchanged.append(aid)

    base_action = baseline.next_action.model_dump() if baseline.next_action else None
    alt_action = what_if.next_action.model_dump() if what_if.next_action else None
    no_change = (
        not changed
        and baseline.overall_status == what_if.overall_status
        and base_action == alt_action
    )
    if not include_unchanged:
        unchanged = sorted(unchanged)
    return WhatIfComparison(
        changed_approvals=changed,
        unchanged_approvals=sorted(unchanged),
        added_blockers=added_all,
        removed_blockers=removed_all,
        overall_baseline=baseline.overall_status.value,
        overall_whatif=what_if.overall_status.value,
        next_action_baseline=baseline.next_action,
        next_action_whatif=what_if.next_action,
        no_change=no_change,
    )


def run_whatif_assessment(
    application_id: str,
    base_facts: dict[str, Any],
    fact_overrides: dict[str, Any],
    approval_rules: list[ApprovalRule],
    approval_authorities: dict[str, str],
    dependencies: list,
    all_approval_ids: list[str],
    document_requirements: list[dict[str, Any]],
    uploaded_documents: list[dict[str, Any]],
    extraction_results: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
    consistency_result: Any | None,
    sla_info: Any | None,
    obtained_approvals: set[str],
    evidence_gaps_by_approval: dict | None = None,
    include_unchanged: bool = False,
    jurisdiction: str = GJ_JURISDICTION,
    fact_provenance: dict[str, dict[str, Any]] | None = None,
    approval_compositions: dict[str, ApprovalComposition] | None = None,
) -> WhatIfResponse:
    """Run baseline + what-if through the SAME pipeline and compare.

    ``fact_provenance`` names the base-fact keys that were derived (as
    produced by ``apply_derived_facts``). Those keys are stripped before
    applying overrides so a changed source fact recomputes instead of
    reusing a stale value; a directly-overridden derived key stays
    supplied and takes precedence per the ``derive_mh_facts``
    contract. IN-GJ passes through exactly as before.
    """
    baseline = orchestrate_application_full(
        application_id=application_id,
        project_facts=dict(base_facts),
        approval_rules=approval_rules,
        approval_authorities=approval_authorities,
        dependencies=dependencies,
        all_approval_ids=all_approval_ids,
        document_requirements=document_requirements,
        uploaded_documents=uploaded_documents,
        extraction_results=extraction_results,
        validation_results=validation_results,
        consistency_result=consistency_result,
        sla_info=sla_info,
        obtained_approvals=set(obtained_approvals),
        evidence_gaps_by_approval=evidence_gaps_by_approval,
        fact_provenance=fact_provenance,
        approval_compositions=approval_compositions,
    )
    base_raw = {
        key: value
        for key, value in base_facts.items()
        if key not in (fact_provenance or {})
    }
    merged = apply_fact_overrides(
        base_raw, fact_overrides, jurisdiction=jurisdiction
    )
    alt_provenance: dict[str, dict[str, Any]] = {}
    if jurisdiction == MH_JURISDICTION:
        merged, alt_provenance = apply_derived_facts(merged, jurisdiction)
    what_if = orchestrate_application_full(
        application_id=application_id,
        project_facts=merged,
        approval_rules=approval_rules,
        approval_authorities=approval_authorities,
        dependencies=dependencies,
        all_approval_ids=all_approval_ids,
        document_requirements=document_requirements,
        uploaded_documents=uploaded_documents,
        extraction_results=extraction_results,
        validation_results=validation_results,
        consistency_result=consistency_result,
        sla_info=sla_info,
        obtained_approvals=set(obtained_approvals),
        evidence_gaps_by_approval=evidence_gaps_by_approval,
        fact_provenance=alt_provenance,
        approval_compositions=approval_compositions,
    )
    diff = compare_orchestrations(baseline, what_if, include_unchanged=include_unchanged)
    return WhatIfResponse(
        application_id=application_id,
        baseline=baseline,
        what_if=what_if,
        diff=diff,
        applied_overrides=dict(fact_overrides),
    )
