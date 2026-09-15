"""Generic, data-driven approval applicability evaluation engine.

Evaluates arbitrary project facts against a recursive condition tree
to produce deterministic, traceable applicability results. Rules are
data/config driven — new approvals, authorities, industries, and states
can be added without changing engine code.

This engine is deterministic and separate from RAG/LLM logic.
No LLM calls are made during evaluation.

Condition tree supports:
- Leaf predicates: {kind: "condition", field, op, value}
- AND groups:     {kind: "and",   conditions: [...]}
- OR groups:      {kind: "or",    conditions: [...]}
- NOT groups:     {kind: "not",   condition: ...}

Three-valued logic (TRUE / FALSE / INSUFFICIENT_DATA):
- AND: any FALSE → FALSE; any INSUFFICIENT (no FALSE) → INSUFFICIENT; all TRUE → TRUE
- OR:  any TRUE → TRUE; any INSUFFICIENT (no TRUE) → INSUFFICIENT; all FALSE → FALSE
- NOT: TRUE→FALSE, FALSE→TRUE, INSUFFICIENT→INSUFFICIENT

Output for each rule:
- APPLIES: tree evaluated to TRUE
- DOES_NOT_APPLY: tree evaluated to FALSE
- CONDITIONAL: tree evaluated to INSUFFICIENT_DATA with at least one leaf evaluated
- INSUFFICIENT_DATA: required fact fields are missing
"""
from __future__ import annotations

from typing import Any

from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityEvaluation,
    ApprovalResult,
    ApprovalRule,
    ConditionNode,
    NotNode,
    OrNode,
)

# ─────────────────────────────────────────────────────────────
# Leaf evaluation
# ─────────────────────────────────────────────────────────────


def _get_fact_value(facts: dict[str, Any], field: str) -> tuple[Any, bool]:
    """Look up a field in project facts. Returns (value, found)."""
    if field in facts:
        return facts[field], True
    return None, False


def _evaluate_leaf(
    condition: ApplicabilityCondition,
    facts: dict[str, Any],
) -> tuple[bool | None, str]:
    """Evaluate a single leaf condition against project facts.

    Returns:
        (result, reason)
        - (True, ...) if condition is satisfied
        - (False, ...) if condition fails (fact present but doesn't match)
        - (None, ...) if the fact field is missing (can't evaluate)
    """
    value, found = _get_fact_value(facts, condition.field)

    if not found:
        return None, f"fact field '{condition.field}' not provided"

    match condition.op:
        case "eq":
            if value == condition.value:
                return True, f"{condition.field} == {condition.value!r}"
            return False, f"{condition.field} ({value!r}) != {condition.value!r}"

        case "in":
            if not isinstance(condition.value, list):
                return False, "rule value for 'in' op must be a list"
            if isinstance(value, list):
                if any(v in condition.value for v in value):
                    return True, f"{condition.field} ({value}) overlaps {condition.value}"
                return False, f"{condition.field} ({value}) has no overlap with {condition.value}"
            if value in condition.value:
                return True, f"{condition.field} ({value!r}) in {condition.value}"
            return False, f"{condition.field} ({value!r}) not in {condition.value}"

        case "gt":
            if not isinstance(value, (int, float)) or not isinstance(condition.value, (int, float)):
                return False, f"{condition.field} value must be numeric for gt"
            if value > condition.value:
                return True, f"{condition.field} ({value}) > {condition.value}"
            return False, f"{condition.field} ({value}) <= {condition.value}"

        case "gte":
            if not isinstance(value, (int, float)) or not isinstance(condition.value, (int, float)):
                return False, f"{condition.field} value must be numeric for gte"
            if value >= condition.value:
                return True, f"{condition.field} ({value}) >= {condition.value}"
            return False, f"{condition.field} ({value}) < {condition.value}"

        case "lt":
            if not isinstance(value, (int, float)) or not isinstance(condition.value, (int, float)):
                return False, f"{condition.field} value must be numeric for lt"
            if value < condition.value:
                return True, f"{condition.field} ({value}) < {condition.value}"
            return False, f"{condition.field} ({value}) >= {condition.value}"

        case "lte":
            if not isinstance(value, (int, float)) or not isinstance(condition.value, (int, float)):
                return False, f"{condition.field} value must be numeric for lte"
            if value <= condition.value:
                return True, f"{condition.field} ({value}) <= {condition.value}"
            return False, f"{condition.field} ({value}) > {condition.value}"

    # Unknown operator — conservatively reject
    return False, f"operator '{condition.op}' not recognized"


# ─────────────────────────────────────────────────────────────
# Recursive tree evaluation
# ─────────────────────────────────────────────────────────────


def _evaluate_node(
    node: ConditionNode,
    facts: dict[str, Any],
) -> tuple[bool | None, str]:
    """Evaluate a condition tree node against project facts.

    Returns (result, reason) where result is True/False/None.
    None means INSUFFICIENT_DATA (could not evaluate).
    """
    if isinstance(node, ApplicabilityCondition):
        return _evaluate_leaf(node, facts)

    if isinstance(node, AndNode):
        child_results = [_evaluate_node(c, facts) for c in node.conditions]
        has_false = any(r is False for r, _ in child_results)
        has_none = any(r is None for r, _ in child_results)

        if has_false:
            fail_reasons = [reason for r, reason in child_results if r is False]
            return False, "AND: " + "; ".join(fail_reasons)
        if has_none:
            uneval_reasons = [reason for r, reason in child_results if r is None]
            return None, "AND: missing " + ", ".join(uneval_reasons)
        all_reasons = [reason for _, reason in child_results]
        return True, "AND: all satisfied (" + "; ".join(all_reasons) + ")"

    if isinstance(node, OrNode):
        child_results = [_evaluate_node(c, facts) for c in node.conditions]
        has_true = any(r is True for r, _ in child_results)
        has_none = any(r is None for r, _ in child_results)

        if has_true:
            pass_reasons = [reason for r, reason in child_results if r is True]
            return True, "OR: " + "; ".join(pass_reasons)
        if has_none:
            uneval_reasons = [reason for r, reason in child_results if r is None]
            return None, "OR: missing " + ", ".join(uneval_reasons)
        fail_reasons = [reason for r, reason in child_results if r is False]
        return False, "OR: all failed (" + "; ".join(fail_reasons) + ")"

    if isinstance(node, NotNode):
        child_result, child_reason = _evaluate_node(node.condition, facts)
        if child_result is True:
            return False, f"NOT: ({child_reason}) negated to false"
        if child_result is False:
            return True, f"NOT: ({child_reason}) negated to true"
        return None, f"NOT: ({child_reason}) — cannot negate insufficient data"

    # Should not reach here with valid discriminated union
    return None, "unknown node type"


# ─────────────────────────────────────────────────────────────
# Field collection (walks the tree)
# ─────────────────────────────────────────────────────────────


def _collect_fields_from_node(node: ConditionNode) -> set[str]:
    """Recursively collect all field names referenced in a condition tree."""
    if isinstance(node, ApplicabilityCondition):
        return {node.field}
    if isinstance(node, AndNode):
        result: set[str] = set()
        for c in node.conditions:
            result |= _collect_fields_from_node(c)
        return result
    if isinstance(node, OrNode):
        result = set()
        for c in node.conditions:
            result |= _collect_fields_from_node(c)
        return result
    if isinstance(node, NotNode):
        return _collect_fields_from_node(node.condition)
    return set()


def _collect_required_inputs(rule: ApprovalRule) -> list[str]:
    """Collect all fact fields required by a rule's condition tree."""
    result: set[str] = set()
    for node in rule.applicability_conditions:
        result |= _collect_fields_from_node(node)
    return sorted(result)


def _collect_missing_inputs(
    rule: ApprovalRule, facts: dict[str, Any]
) -> list[str]:
    """Collect fact fields required by the rule but missing from project facts."""
    required = _collect_required_inputs(rule)
    return sorted(f for f in required if f not in facts)


# ─────────────────────────────────────────────────────────────
# Rule evaluation
# ─────────────────────────────────────────────────────────────


def evaluate_rule(
    rule: ApprovalRule,
    project_facts: dict[str, Any],
    authority: str = "",
) -> ApplicabilityEvaluation:
    """Evaluate a single approval rule against project facts.

    Deterministic, no LLM calls. Returns a detailed evaluation result
    with full traceability.

    The rule's applicability_conditions is a list of ConditionNode trees.
    Each tree is evaluated independently; if ANY tree evaluates to TRUE,
    the rule APPLIES. This preserves the "multiple rules, any match"
    semantic from the flat-list design.

    Logic:
    1. If any required fact field is missing → INSUFFICIENT_DATA
    2. If any condition tree evaluates to TRUE → APPLIES
    3. If all trees evaluate to FALSE → DOES_NOT_APPLY
    4. If at least one tree is INSUFFICIENT_DATA and none TRUE → CONDITIONAL
    """
    required_inputs = _collect_required_inputs(rule)
    missing_inputs = _collect_missing_inputs(rule, project_facts)

    # No conditions → rule always applies
    if not rule.applicability_conditions:
        return ApplicabilityEvaluation(
            rule_id=rule.id,
            approval_id=rule.approval_id,
            result=ApprovalResult.APPLIES.value,
            reason="No applicability conditions — rule applies to all projects",
            required_inputs=required_inputs,
            missing_inputs=[],
            authority=authority,
            source_references=rule.source_refs,
        )

    # Evaluate each top-level condition tree
    tree_results: list[tuple[bool | None, str]] = []
    for node in rule.applicability_conditions:
        result, reason = _evaluate_node(node, project_facts)
        tree_results.append((result, reason))

    any_true = any(r is True for r, _ in tree_results)
    any_false = any(r is False for r, _ in tree_results)
    any_none = any(r is None for r, _ in tree_results)

    # APPLIES: at least one tree evaluated to TRUE
    if any_true:
        pass_reasons = [reason for r, reason in tree_results if r is True]
        return ApplicabilityEvaluation(
            rule_id=rule.id,
            approval_id=rule.approval_id,
            result=ApprovalResult.APPLIES.value,
            reason="Conditions satisfied: " + "; ".join(pass_reasons),
            required_inputs=required_inputs,
            missing_inputs=[],
            authority=authority,
            source_references=rule.source_refs,
        )

    # DOES_NOT_APPLY: all trees evaluated to FALSE (no INSUFFICIENT_DATA)
    if any_false and not any_none:
        fail_reasons = [reason for r, reason in tree_results if r is False]
        return ApplicabilityEvaluation(
            rule_id=rule.id,
            approval_id=rule.approval_id,
            result=ApprovalResult.DOES_NOT_APPLY.value,
            reason="Conditions not met: " + "; ".join(fail_reasons),
            required_inputs=required_inputs,
            missing_inputs=[],
            authority=authority,
            source_references=rule.source_refs,
        )

    # CONDITIONAL: at least one INSUFFICIENT_DATA, at least one FALSE, no TRUE
    if any_none and any_false:
        uneval_reasons = [reason for r, reason in tree_results if r is None]
        fail_reasons = [reason for r, reason in tree_results if r is False]
        return ApplicabilityEvaluation(
            rule_id=rule.id,
            approval_id=rule.approval_id,
            result=ApprovalResult.CONDITIONAL.value,
            reason=(
                "Partial evaluation — some facts unavailable: "
                + "; ".join(uneval_reasons)
                + "; other conditions failed: "
                + "; ".join(fail_reasons)
            ),
            required_inputs=required_inputs,
            missing_inputs=[],
            authority=authority,
            source_references=rule.source_refs,
        )

    # INSUFFICIENT_DATA: all trees evaluated to INSUFFICIENT_DATA
    if any_none and not any_false:
        uneval_reasons = [reason for r, reason in tree_results if r is None]
        return ApplicabilityEvaluation(
            rule_id=rule.id,
            approval_id=rule.approval_id,
            result=ApprovalResult.INSUFFICIENT_DATA.value,
            reason="Required fact fields missing: " + "; ".join(uneval_reasons),
            required_inputs=required_inputs,
            missing_inputs=missing_inputs,
            authority=authority,
            source_references=rule.source_refs,
        )

    # Fallback (should not reach here)
    return ApplicabilityEvaluation(
        rule_id=rule.id,
        approval_id=rule.approval_id,
        result=ApprovalResult.INSUFFICIENT_DATA.value,
        reason="Unable to determine applicability",
        required_inputs=required_inputs,
        missing_inputs=[],
        authority=authority,
        source_references=rule.source_refs,
    )


def evaluate_approval_applicability(
    rules: list[ApprovalRule],
    project_facts: dict[str, Any],
    approval_authorities: dict[str, str] | None = None,
    approval_ids: list[str] | None = None,
) -> list[ApplicabilityEvaluation]:
    """Evaluate multiple approval rules against project facts.

    Args:
        rules: All approval rules to evaluate.
        project_facts: Arbitrary project fact fields.
        approval_authorities: Optional mapping of approval_id → authority name.
        approval_ids: Optional filter — only evaluate rules for these approvals.

    Returns:
        List of detailed evaluation results, one per rule evaluated.
    """
    if approval_authorities is None:
        approval_authorities = {}

    # Optionally filter to specific approvals
    filtered_rules = rules
    if approval_ids:
        approval_id_set = set(approval_ids)
        filtered_rules = [r for r in rules if r.approval_id in approval_id_set]

    evaluations: list[ApplicabilityEvaluation] = []
    for rule in filtered_rules:
        authority = approval_authorities.get(rule.approval_id, "")
        evaluation = evaluate_rule(rule, project_facts, authority)
        evaluations.append(evaluation)

    return evaluations


def summarize_evaluations(
    evaluations: list[ApplicabilityEvaluation],
) -> dict[str, int]:
    """Count evaluations by result type."""
    summary: dict[str, int] = {
        ApprovalResult.APPLIES.value: 0,
        ApprovalResult.DOES_NOT_APPLY.value: 0,
        ApprovalResult.CONDITIONAL.value: 0,
        ApprovalResult.INSUFFICIENT_DATA.value: 0,
    }
    for e in evaluations:
        if e.result in summary:
            summary[e.result] += 1
    return summary


def summarize_by_approval(
    evaluations: list[ApplicabilityEvaluation],
) -> dict[str, ApplicabilityEvaluation]:
    """Aggregate rule-level evaluations by approval_id.

    When multiple rules share an approval_id, returns the first evaluation
    whose result is APPLIES.  If no rule applies, returns the first
    DOES_NOT_APPLY, then CONDITIONAL, then INSUFFICIENT_DATA.
    """
    from collections import defaultdict

    grouped: dict[str, list[ApplicabilityEvaluation]] = defaultdict(list)
    for e in evaluations:
        grouped[e.approval_id].append(e)

    result_priority = [
        ApprovalResult.APPLIES.value,
        ApprovalResult.DOES_NOT_APPLY.value,
        ApprovalResult.CONDITIONAL.value,
        ApprovalResult.INSUFFICIENT_DATA.value,
    ]

    aggregated: dict[str, ApplicabilityEvaluation] = {}
    for approval_id, evals in grouped.items():
        for priority in result_priority:
            match = [e for e in evals if e.result == priority]
            if match:
                aggregated[approval_id] = match[0]
                break
    return aggregated
