"""UNKNOWN-token fail-closed semantics for supplied fact values (MH audit).

The IN-MH registry (app/rules/facts.py) accepts the "UNKNOWN" token for
76 unknown-tolerant facts and as an enum member for 18 more, with the
contract "UNKNOWN is always a permitted value and is never coerced to
FALSE". The engine must therefore treat a supplied "UNKNOWN" (or an
explicit None) exactly like a missing key: INSUFFICIENT_DATA, never
DOES_NOT_APPLY — for trigger rules and exemption rules alike.
"""
from __future__ import annotations

from app.rules.applicability import evaluate_rule
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
)


def _leaf(field, op, value):
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


class TestUnknownTokenFailClosed:
    def test_trigger_rule_unknown_string_is_insufficient(self):
        # R-018 shape: HW authorisation trigger on F-HW-01 == True.
        rule = _rule(_leaf("F-HW-01", "eq", True))
        result = evaluate_rule(rule, {"F-HW-01": "UNKNOWN"})
        assert result.result == "insufficient_data"
        assert "F-HW-01" in result.missing_inputs

    def test_trigger_rule_explicit_none_is_insufficient(self):
        rule = _rule(_leaf("F-HW-01", "eq", True))
        result = evaluate_rule(rule, {"F-HW-01": None})
        assert result.result == "insufficient_data"
        assert "F-HW-01" in result.missing_inputs

    def test_exemption_rule_unknown_is_insufficient_not_does_not_apply(self):
        # R-030 shape: Class-B exemption triple. UNKNOWN petroleum class
        # must not conclude "exemption does not apply".
        rule = _rule(
            AndNode(
                conditions=[
                    _leaf("F-PET-01", "eq", "B"),
                    _leaf("F-PET-02", "lte", 2500),
                    _leaf("F-PET-04", "lte", 1000),
                ]
            )
        )
        result = evaluate_rule(
            rule,
            {"F-PET-01": "UNKNOWN", "F-PET-02": 1000, "F-PET-04": 500},
        )
        assert result.result == "insufficient_data"
        assert "F-PET-01" in result.missing_inputs

    def test_known_values_still_decide(self):
        rule = _rule(_leaf("F-HW-01", "eq", True))
        assert evaluate_rule(rule, {"F-HW-01": True}).result == "applies"
        assert (
            evaluate_rule(rule, {"F-HW-01": False}).result
            == "does_not_apply"
        )

    def test_enum_unknown_member_is_insufficient(self):
        # F-PET-01 carries "UNKNOWN" as an allowed enum member; supplying
        # it must fail closed, not coerce to FALSE.
        rule = _rule(_leaf("F-PET-01", "eq", "B"))
        result = evaluate_rule(rule, {"F-PET-01": "UNKNOWN"})
        assert result.result == "insufficient_data"

    def test_gj_legacy_path_unchanged(self):
        # Ordinary GJ-vocabulary facts keep exact three-valued behavior:
        # present values decide, absent keys are insufficient.
        rule = _rule(_leaf("sector", "eq", "chemical"))
        assert (
            evaluate_rule(rule, {"sector": "chemical"}).result == "applies"
        )
        assert (
            evaluate_rule(rule, {"sector": "textiles"}).result
            == "does_not_apply"
        )
        assert (
            evaluate_rule(rule, {}).result == "insufficient_data"
        )
