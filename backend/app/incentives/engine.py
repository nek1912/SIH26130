"""Incentive assessment engine — deterministic eligibility evaluation.

Reuses the existing recursive condition tree evaluator from
app.rules.applicability. No LLM calls, no invented facts.

Assessment states:
- POTENTIALLY_RELEVANT: all evaluated conditions satisfied
- NOT_RELEVANT: at least one condition fails
- CONDITIONAL: some facts missing but no failure yet
- INSUFFICIENT_DATA: required fact fields are missing

This engine is PURE: no database calls, no side effects.
"""
from __future__ import annotations

from typing import Any

from app.incentives.models import (
    ProjectIncentiveAssessment,
    RelevanceState,
    SchemeRelevance,
    SupportScheme,
)
from app.rules.applicability import (
    _collect_fields_from_node,
    _evaluate_node,
)


def _get_required_fields(scheme: SupportScheme) -> list[str]:
    """Collect all fact fields referenced in the scheme's eligibility conditions."""
    fields: set[str] = set()
    for node in scheme.eligibility_conditions:
        fields |= _collect_fields_from_node(node)
    return sorted(fields)


def _get_missing_fields(
    scheme: SupportScheme, facts: dict[str, Any]
) -> list[str]:
    """Collect fact fields required but missing from project facts."""
    required = _get_required_fields(scheme)
    return [f for f in required if f not in facts]


def assess_scheme(
    scheme: SupportScheme,
    project_facts: dict[str, Any],
) -> SchemeRelevance:
    """Evaluate a single incentive scheme against project facts.

    Deterministic, no LLM. Returns traceable relevance assessment.
    """
    if not scheme.active:
        return SchemeRelevance(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            relevance=RelevanceState.NOT_RELEVANT,
            reason="Scheme is inactive",
            source_refs=scheme.source_refs,
        )

    # No conditions → potentially relevant to all projects
    if not scheme.eligibility_conditions:
        return SchemeRelevance(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            relevance=RelevanceState.POTENTIALLY_RELEVANT,
            reason="No eligibility conditions — scheme potentially relevant to all projects",
            source_refs=scheme.source_refs,
        )

    required_fields = _get_required_fields(scheme)
    missing_fields = _get_missing_fields(scheme, project_facts)

    # If all required fields are missing, we can't assess
    if missing_fields and len(missing_fields) == len(required_fields):
        return SchemeRelevance(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            relevance=RelevanceState.INSUFFICIENT_DATA,
            reason=f"All required fact fields missing: {', '.join(missing_fields)}",
            missing_info=missing_fields,
            source_refs=scheme.source_refs,
        )

    # Evaluate each condition tree
    tree_results: list[tuple[bool | None, str]] = []
    for node in scheme.eligibility_conditions:
        result, reason = _evaluate_node(node, project_facts)
        tree_results.append((result, reason))

    any_true = any(r is True for r, _ in tree_results)
    any_false = any(r is False for r, _ in tree_results)
    any_none = any(r is None for r, _ in tree_results)

    if any_true:
        pass_reasons = [reason for r, reason in tree_results if r is True]
        return SchemeRelevance(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            relevance=RelevanceState.POTENTIALLY_RELEVANT,
            reason="Eligibility conditions satisfied: " + "; ".join(pass_reasons),
            triggered_conditions=pass_reasons,
            source_refs=scheme.source_refs,
        )

    if any_false and not any_none:
        fail_reasons = [reason for r, reason in tree_results if r is False]
        return SchemeRelevance(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            relevance=RelevanceState.NOT_RELEVANT,
            reason="Eligibility conditions not met: " + "; ".join(fail_reasons),
            source_refs=scheme.source_refs,
        )

    if any_none and any_false:
        uneval = [reason for r, reason in tree_results if r is None]
        fail = [reason for r, reason in tree_results if r is False]
        return SchemeRelevance(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            relevance=RelevanceState.CONDITIONAL,
            reason=(
                "Partial evaluation — some facts unavailable: "
                + "; ".join(uneval)
                + "; other conditions failed: "
                + "; ".join(fail)
            ),
            missing_info=missing_fields,
            source_refs=scheme.source_refs,
        )

    # All INSUFFICIENT_DATA
    uneval = [reason for r, reason in tree_results if r is None]
    return SchemeRelevance(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        relevance=RelevanceState.INSUFFICIENT_DATA,
        reason="Required fact fields missing: " + "; ".join(uneval),
        missing_info=missing_fields,
        source_refs=scheme.source_refs,
    )


def assess_all_schemes(
    schemes: list[SupportScheme],
    project_facts: dict[str, Any],
    project_id: str = "",
    scheme_ids: list[str] | None = None,
) -> ProjectIncentiveAssessment:
    """Assess all incentive schemes against project facts.

    Pure function: no database calls, no side effects.
    """
    filtered = schemes
    if scheme_ids:
        id_set = set(scheme_ids)
        filtered = [s for s in schemes if s.id in id_set]

    assessments = [assess_scheme(s, project_facts) for s in filtered]

    relevant = sum(1 for a in assessments if a.relevance == RelevanceState.POTENTIALLY_RELEVANT)
    conditional = sum(1 for a in assessments if a.relevance == RelevanceState.CONDITIONAL)
    insufficient = sum(1 for a in assessments if a.relevance == RelevanceState.INSUFFICIENT_DATA)
    not_relevant = sum(1 for a in assessments if a.relevance == RelevanceState.NOT_RELEVANT)

    # Build explanation
    if relevant > 0:
        rel_names = [
            a.scheme_name for a in assessments
            if a.relevance == RelevanceState.POTENTIALLY_RELEVANT
        ]
        explanation = (
            f"{relevant} scheme(s) potentially relevant: {', '.join(rel_names)}. "
        )
    else:
        explanation = "No schemes found potentially relevant based on available project facts. "

    if conditional > 0:
        cond_names = [
            a.scheme_name for a in assessments
            if a.relevance == RelevanceState.CONDITIONAL
        ]
        explanation += f"{conditional} scheme(s) conditionally relevant: {', '.join(cond_names)}. "

    if insufficient > 0:
        explanation += f"{insufficient} scheme(s) require additional project information. "

    explanation += "Final eligibility remains with the competent authority."

    return ProjectIncentiveAssessment(
        project_id=project_id,
        assessments=assessments,
        relevant_count=relevant,
        conditional_count=conditional,
        insufficient_count=insufficient,
        not_relevant_count=not_relevant,
        explanation=explanation,
    )
