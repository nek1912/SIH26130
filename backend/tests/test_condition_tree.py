"""Tests for the recursive condition tree evaluation engine.

Covers:
- AND node: all TRUE, any FALSE, any INSUFFICIENT_DATA
- OR node: any TRUE, all FALSE, any INSUFFICIENT_DATA
- NOT node: TRUE→FALSE, FALSE→TRUE, INSUFFICIENT_DATA→INSUFFICIENT_DATA
- Deep nesting: NOT(AND(...)), OR(AND(...), NOT(...))
- Mixed INSUFFICIENT_DATA propagation through trees
- Three-valued logic determinism
- Backward compatibility with flat condition lists
"""
from __future__ import annotations

from app.rules.applicability import (
    _evaluate_node,
    evaluate_rule,
)
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
    NotNode,
    OrNode,
    SourceRef,
)


def _leaf(field: str, op: str, value: object) -> ApplicabilityCondition:
    """Shorthand for a leaf condition."""
    return ApplicabilityCondition(field=field, op=ApplicabilityOp(op), value=value)


def _and(*nodes: ApplicabilityCondition | AndNode | OrNode | NotNode) -> AndNode:
    """Shorthand for an AND node."""
    return AndNode(conditions=list(nodes))


def _or(*nodes: ApplicabilityCondition | AndNode | OrNode | NotNode) -> OrNode:
    """Shorthand for an OR node."""
    return OrNode(conditions=list(nodes))


def _not(node: ApplicabilityCondition | AndNode | OrNode | NotNode) -> NotNode:
    """Shorthand for a NOT node."""
    return NotNode(condition=node)


def _rule(*nodes: ApplicabilityCondition | AndNode | OrNode | NotNode) -> ApprovalRule:
    """Create a rule with the given condition trees."""
    return ApprovalRule(
        id="test-rule",
        approval_id="test-approval",
        applicability_conditions=list(nodes),
        source_refs=[SourceRef(source_id="src-1", citation_span="s.1")],
        version="1",
    )


# ─────────────────────────────────────────────────────────────
# AND node
# ─────────────────────────────────────────────────────────────


class TestAndNode:
    def test_all_true(self):
        node = _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 150})
        assert result is True

    def test_any_false(self):
        node = _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 150})
        assert result is False

    def test_both_false(self):
        node = _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 50})
        assert result is False

    def test_one_missing_one_true(self):
        node = _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is None  # INSUFFICIENT_DATA

    def test_one_missing_one_false(self):
        node = _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "textiles"})
        # sector is FALSE, headcount is INSUFFICIENT_DATA → AND: any FALSE → FALSE
        assert result is False

    def test_all_missing(self):
        node = _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {})
        assert result is None  # INSUFFICIENT_DATA

    def test_deep_nesting(self):
        node = _and(
            _leaf("sector", "eq", "chemicals"),
            _and(_leaf("headcount", "gte", 100), _leaf("annual_turnover_inr", "gte", 5000000)),
        )
        facts = {"sector": "chemicals", "headcount": 150, "annual_turnover_inr": 10000000}
        result, _ = _evaluate_node(node, facts)
        assert result is True


# ─────────────────────────────────────────────────────────────
# OR node
# ─────────────────────────────────────────────────────────────


class TestOrNode:
    def test_any_true(self):
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("sector", "eq", "textiles"))
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is True

    def test_both_true(self):
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("sector", "eq", "chemicals"))
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is True

    def test_all_false(self):
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("sector", "eq", "textiles"))
        result, _ = _evaluate_node(node, {"sector": "pharma"})
        assert result is False

    def test_one_missing_one_true(self):
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        # sector is TRUE → OR: any TRUE → TRUE
        assert result is True

    def test_one_missing_one_false(self):
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "textiles"})
        # sector is FALSE, headcount is INSUFFICIENT_DATA → OR: INSUFFICIENT_DATA
        assert result is None  # INSUFFICIENT_DATA

    def test_all_missing(self):
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {})
        assert result is None  # INSUFFICIENT_DATA


# ─────────────────────────────────────────────────────────────
# NOT node
# ─────────────────────────────────────────────────────────────


class TestNotNode:
    def test_not_true_is_false(self):
        node = _not(_leaf("sector", "eq", "chemicals"))
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is False

    def test_not_false_is_true(self):
        node = _not(_leaf("sector", "eq", "chemicals"))
        result, _ = _evaluate_node(node, {"sector": "textiles"})
        assert result is True

    def test_not_missing_is_insufficient(self):
        node = _not(_leaf("sector", "eq", "chemicals"))
        result, _ = _evaluate_node(node, {})
        assert result is None  # INSUFFICIENT_DATA

    def test_not_and(self):
        node = _not(_and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)))
        # Both true → AND true → NOT false
        result, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 150})
        assert result is False

    def test_not_and_one_fails(self):
        node = _not(_and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)))
        # One false → AND false → NOT true
        result, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 150})
        assert result is True


# ─────────────────────────────────────────────────────────────
# Deep nesting
# ─────────────────────────────────────────────────────────────


class TestDeepNesting:
    def test_or_of_ands(self):
        """(sector==chemicals AND headcount>=100) OR (sector==textiles AND headcount>=50)"""
        node = _or(
            _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)),
            _and(_leaf("sector", "eq", "textiles"), _leaf("headcount", "gte", 50)),
        )
        # First AND matches
        result, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 150})
        assert result is True

        # Second AND matches
        result, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 60})
        assert result is True

        # Neither matches
        result, _ = _evaluate_node(node, {"sector": "pharma", "headcount": 200})
        assert result is False

    def test_not_of_or(self):
        """NOT(sector==chemicals OR sector==textiles)"""
        node = _not(_or(_leaf("sector", "eq", "chemicals"), _leaf("sector", "eq", "textiles")))
        # OR is true → NOT is false
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is False

        # OR is false → NOT is true
        result, _ = _evaluate_node(node, {"sector": "pharma"})
        assert result is True

    def test_and_of_not_and_leaf(self):
        """NOT(sector==chemicals) AND headcount>=100"""
        node = _and(
            _not(_leaf("sector", "eq", "chemicals")),
            _leaf("headcount", "gte", 100),
        )
        result, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 150})
        assert result is True

        result, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 150})
        assert result is False

    def test_triple_nesting(self):
        """NOT(AND(OR(a, b), c))"""
        node = _not(
            _and(
                _or(_leaf("sector", "eq", "chemicals"), _leaf("sector", "eq", "pharma")),
                _leaf("headcount", "gte", 100),
            )
        )
        # Inner: OR true, AND true → NOT false
        result, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 150})
        assert result is False

        # Inner: OR true, AND false → NOT true
        result, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 50})
        assert result is True

        # Inner: OR false → AND false → NOT true
        result, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 150})
        assert result is True


# ─────────────────────────────────────────────────────────────
# INSUFFICIENT_DATA propagation through nested trees
# ─────────────────────────────────────────────────────────────


class TestInsufficientDataPropagation:
    def test_and_with_one_missing(self):
        """AND(TRUE, INSUFFICIENT_DATA) → INSUFFICIENT_DATA"""
        node = _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is None

    def test_or_with_one_missing_one_false(self):
        """OR(FALSE, INSUFFICIENT_DATA) → INSUFFICIENT_DATA"""
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "textiles"})
        assert result is None

    def test_or_with_one_missing_one_true(self):
        """OR(TRUE, INSUFFICIENT_DATA) → TRUE (short-circuit)"""
        node = _or(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100))
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is True

    def test_not_of_insufficient(self):
        """NOT(INSUFFICIENT_DATA) → INSUFFICIENT_DATA"""
        node = _not(_leaf("sector", "eq", "chemicals"))
        result, _ = _evaluate_node(node, {})
        assert result is None

    def test_nested_insufficient(self):
        """AND(OR(TRUE, INSUFFICIENT), NOT(INSUFFICIENT)) → INSUFFICIENT_DATA"""
        node = _and(
            _or(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)),
            _not(_leaf("registered_state", "eq", "IN-GJ")),
        )
        # sector TRUE, registered_state INSUFFICIENT
        # → NOT(INSUFFICIENT) = INSUFFICIENT → AND: INSUFFICIENT
        result, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert result is None


# ─────────────────────────────────────────────────────────────
# Rule-level evaluation with trees
# ─────────────────────────────────────────────────────────────


class TestRuleWithTrees:
    def test_single_and_node_applies(self):
        rule = _rule(_and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)))
        result = evaluate_rule(rule, {"sector": "chemicals", "headcount": 150})
        assert result.result == "applies"

    def test_single_and_node_does_not_apply(self):
        rule = _rule(_and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)))
        result = evaluate_rule(rule, {"sector": "textiles", "headcount": 150})
        assert result.result == "does_not_apply"

    def test_single_or_node_applies(self):
        rule = _rule(_or(_leaf("sector", "eq", "chemicals"), _leaf("sector", "eq", "textiles")))
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert result.result == "applies"

    def test_single_or_node_does_not_apply(self):
        rule = _rule(_or(_leaf("sector", "eq", "chemicals"), _leaf("sector", "eq", "textiles")))
        result = evaluate_rule(rule, {"sector": "pharma"})
        assert result.result == "does_not_apply"

    def test_not_node_applies(self):
        rule = _rule(_not(_leaf("sector", "eq", "chemicals")))
        result = evaluate_rule(rule, {"sector": "textiles"})
        assert result.result == "applies"

    def test_not_node_does_not_apply(self):
        rule = _rule(_not(_leaf("sector", "eq", "chemicals")))
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert result.result == "does_not_apply"

    def test_multiple_trees_any_true_applies(self):
        """Multiple top-level trees: if ANY is TRUE, rule APPLIES."""
        rule = _rule(
            _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)),
            _and(_leaf("sector", "eq", "textiles"), _leaf("headcount", "gte", 50)),
        )
        # First tree TRUE, second FALSE → APPLIES
        result = evaluate_rule(rule, {"sector": "chemicals", "headcount": 150})
        assert result.result == "applies"

        # First tree FALSE, second TRUE → APPLIES
        result = evaluate_rule(rule, {"sector": "textiles", "headcount": 60})
        assert result.result == "applies"

        # Both FALSE → DOES_NOT_APPLY
        result = evaluate_rule(rule, {"sector": "pharma", "headcount": 200})
        assert result.result == "does_not_apply"

    def test_multiple_trees_insufficient(self):
        """Multiple trees: if any is INSUFFICIENT_DATA and none TRUE → CONDITIONAL."""
        rule = _rule(
            _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)),
            _and(_leaf("sector", "eq", "textiles"), _leaf("headcount", "gte", 50)),
        )
        # sector=chemicals: first tree INSUFFICIENT (headcount missing), second FALSE → CONDITIONAL
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert result.result == "conditional"

    def test_required_inputs_from_tree(self):
        """Required inputs are collected recursively from the tree."""
        rule = _rule(
            _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)),
            _not(_leaf("registered_state", "eq", "IN-GJ")),
        )
        result = evaluate_rule(rule, {})
        assert set(result.required_inputs) == {"sector", "headcount", "registered_state"}

    def test_missing_inputs_from_tree(self):
        """Missing inputs are collected recursively from the tree."""
        rule = _rule(
            _and(_leaf("sector", "eq", "chemicals"), _leaf("headcount", "gte", 100)),
            _not(_leaf("registered_state", "eq", "IN-GJ")),
        )
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert set(result.missing_inputs) == {"headcount", "registered_state"}


# ─────────────────────────────────────────────────────────────
# Backward compatibility: flat conditions still work
# ─────────────────────────────────────────────────────────────


class TestBackwardCompatibility:
    def test_single_flat_condition(self):
        """A single leaf condition works as before."""
        rule = ApprovalRule(
            id="flat-1",
            approval_id="a1",
            applicability_conditions=[_leaf("sector", "eq", "chemicals")],
            source_refs=[SourceRef(source_id="src-1", citation_span="s.1")],
            version="1",
        )
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert result.result == "applies"

    def test_empty_conditions(self):
        """No conditions → always applies."""
        rule = ApprovalRule(
            id="flat-2",
            approval_id="a1",
            applicability_conditions=[],
            source_refs=[SourceRef(source_id="src-1", citation_span="s.1")],
            version="1",
        )
        result = evaluate_rule(rule, {})
        assert result.result == "applies"


# ─────────────────────────────────────────────────────────────
# Three-valued logic determinism
# ─────────────────────────────────────────────────────────────


class TestThreeValuedLogic:
    def test_and_truth_table(self):
        """Verify the complete AND truth table."""
        a = _leaf("sector", "eq", "chemicals")
        b = _leaf("headcount", "gte", 100)
        node = _and(a, b)

        # TRUE AND TRUE → TRUE
        r, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 150})
        assert r is True

        # TRUE AND FALSE → FALSE
        r, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 50})
        assert r is False

        # FALSE AND TRUE → FALSE
        r, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 150})
        assert r is False

        # FALSE AND FALSE → FALSE
        r, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 50})
        assert r is False

        # TRUE AND INSUFFICIENT → INSUFFICIENT
        r, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert r is None

        # FALSE AND INSUFFICIENT → FALSE
        r, _ = _evaluate_node(node, {"sector": "textiles"})
        assert r is False

        # INSUFFICIENT AND TRUE → INSUFFICIENT
        r, _ = _evaluate_node(node, {"headcount": 150})
        assert r is None

        # INSUFFICIENT AND FALSE → FALSE
        r, _ = _evaluate_node(node, {"headcount": 50})
        assert r is False

        # INSUFFICIENT AND INSUFFICIENT → INSUFFICIENT
        r, _ = _evaluate_node(node, {})
        assert r is None

    def test_or_truth_table(self):
        """Verify the complete OR truth table."""
        a = _leaf("sector", "eq", "chemicals")
        b = _leaf("headcount", "gte", 100)
        node = _or(a, b)

        # TRUE OR TRUE → TRUE
        r, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 150})
        assert r is True

        # TRUE OR FALSE → TRUE
        r, _ = _evaluate_node(node, {"sector": "chemicals", "headcount": 50})
        assert r is True

        # FALSE OR TRUE → TRUE
        r, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 150})
        assert r is True

        # FALSE OR FALSE → FALSE
        r, _ = _evaluate_node(node, {"sector": "textiles", "headcount": 50})
        assert r is False

        # TRUE OR INSUFFICIENT → TRUE
        r, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert r is True

        # FALSE OR INSUFFICIENT → INSUFFICIENT
        r, _ = _evaluate_node(node, {"sector": "textiles"})
        assert r is None

        # INSUFFICIENT OR TRUE → TRUE
        r, _ = _evaluate_node(node, {"headcount": 150})
        assert r is True

        # INSUFFICIENT OR FALSE → INSUFFICIENT
        r, _ = _evaluate_node(node, {"headcount": 50})
        assert r is None

        # INSUFFICIENT OR INSUFFICIENT → INSUFFICIENT
        r, _ = _evaluate_node(node, {})
        assert r is None

    def test_not_truth_table(self):
        """Verify the complete NOT truth table."""
        a = _leaf("sector", "eq", "chemicals")
        node = _not(a)

        # NOT TRUE → FALSE
        r, _ = _evaluate_node(node, {"sector": "chemicals"})
        assert r is False

        # NOT FALSE → TRUE
        r, _ = _evaluate_node(node, {"sector": "textiles"})
        assert r is True

        # NOT INSUFFICIENT → INSUFFICIENT
        r, _ = _evaluate_node(node, {})
        assert r is None
