"""UNKNOWN / NOT_APPLICABLE literal nodes (Phase 2).

UNKNOWN must never become DOES_NOT_APPLY. Missing input must never
evaluate as false. NOT_APPLICABLE is explicit and distinct from
Python False. Existing three-valued behavior for old trees is
preserved.
"""
from __future__ import annotations

from app.rules.applicability import (
    _collect_fields_from_node,
    _evaluate_node,
    evaluate_rule,
)
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
    LiteralNode,
    NotNode,
    OrNode,
)
from app.rules.validation import validate_applicability_conditions


def _leaf(field="F-PRD-01", op="eq", value=True):
    return ApplicabilityCondition(
        field=field, op=ApplicabilityOp(op), value=value
    )


def _rule(*conditions, rule_id="R-T", approval_id="APR-T"):
    return ApprovalRule(
        id=rule_id,
        approval_id=approval_id,
        applicability_conditions=list(conditions),
        version="1",
    )


UNK = LiteralNode(value="unknown")
NA = LiteralNode(value="not_applicable")


class TestLiteralEvaluation:
    def test_unknown_literal_is_insufficient(self):
        result, _ = _evaluate_node(UNK, {})
        assert result is None

    def test_not_applicable_literal_is_explicit(self):
        from app.rules.models import NOT_APPLICABLE

        result, reason = _evaluate_node(NA, {})
        assert result == NOT_APPLICABLE
        assert result is not False
        assert result is not None
        assert result is not True
        assert "not applicable" in reason.lower()

    def test_unknown_and_true_is_unknown(self):
        result, _ = _evaluate_node(
            AndNode(conditions=[UNK, _leaf()]), {"F-PRD-01": True}
        )
        assert result is None

    def test_unknown_and_false_is_false(self):
        result, _ = _evaluate_node(
            AndNode(conditions=[UNK, _leaf()]), {"F-PRD-01": False}
        )
        assert result is False

    def test_unknown_or_true_is_true(self):
        result, _ = _evaluate_node(
            OrNode(conditions=[UNK, _leaf()]), {"F-PRD-01": True}
        )
        assert result is True

    def test_unknown_or_false_is_unknown(self):
        result, _ = _evaluate_node(
            OrNode(conditions=[UNK, _leaf()]), {"F-PRD-01": False}
        )
        assert result is None

    def test_not_unknown_is_unknown(self):
        result, _ = _evaluate_node(NotNode(condition=UNK), {})
        assert result is None

    def test_not_applicable_and_true(self):
        from app.rules.models import NOT_APPLICABLE

        result, _ = _evaluate_node(
            AndNode(conditions=[NA, _leaf()]), {"F-PRD-01": True}
        )
        assert result == NOT_APPLICABLE

    def test_not_applicable_and_false_is_false(self):
        result, _ = _evaluate_node(
            AndNode(conditions=[NA, _leaf()]), {"F-PRD-01": False}
        )
        assert result is False

    def test_not_applicable_or_false_is_explicit(self):
        from app.rules.models import NOT_APPLICABLE

        result, _ = _evaluate_node(
            OrNode(conditions=[NA, _leaf()]), {"F-PRD-01": False}
        )
        assert result == NOT_APPLICABLE

    def test_not_not_applicable_stays_explicit(self):
        from app.rules.models import NOT_APPLICABLE

        result, _ = _evaluate_node(NotNode(condition=NA), {})
        assert result == NOT_APPLICABLE


class TestLiteralRuleResults:
    def test_unknown_literal_rule_is_insufficient_data(self):
        ev = evaluate_rule(_rule(UNK), {"F-PRD-01": True})
        assert ev.result == "insufficient_data"

    def test_unknown_never_becomes_does_not_apply(self):
        ev = evaluate_rule(_rule(UNK), {})
        assert ev.result == "insufficient_data"
        assert ev.result != "does_not_apply"

    def test_missing_input_never_becomes_does_not_apply(self):
        ev = evaluate_rule(_rule(_leaf("F-PRD-01")), {})
        assert ev.result == "insufficient_data"

    def test_not_applicable_literal_rule_is_does_not_apply(self):
        ev = evaluate_rule(_rule(NA), {"F-PRD-01": True})
        assert ev.result == "does_not_apply"
        assert "explicitly not applicable" in ev.reason.lower()

    def test_mixed_false_and_na_is_does_not_apply(self):
        ev = evaluate_rule(
            _rule(_leaf("F-PRD-01"), NA), {"F-PRD-01": False}
        )
        assert ev.result == "does_not_apply"

    def test_true_dominates_na(self):
        ev = evaluate_rule(
            _rule(_leaf("F-PRD-01"), NA), {"F-PRD-01": True}
        )
        assert ev.result == "applies"

    def test_na_plus_missing_is_insufficient(self):
        ev = evaluate_rule(_rule(_leaf("F-PRD-01"), NA), {})
        assert ev.result == "insufficient_data"


class TestLiteralPlumbing:
    def test_collect_fields_ignores_literals(self):
        assert _collect_fields_from_node(UNK) == set()
        assert _collect_fields_from_node(NA) == set()
        node = AndNode(conditions=[UNK, _leaf("F-PRD-01")])
        assert _collect_fields_from_node(node) == {"F-PRD-01"}

    def test_validation_accepts_literals(self):
        result = validate_applicability_conditions([UNK, NA])
        assert result.ok is True
