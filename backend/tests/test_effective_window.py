"""Effective-window pre-check semantics (Phase 2).

Mechanism only: no legal dates are invented. Rules without dates, or
evaluations without an evaluation_date, behave exactly as before.
"""
from __future__ import annotations

from datetime import date

from app.rules.applicability import (
    evaluate_approval_applicability,
    evaluate_rule,
)
from app.rules.models import (
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
)


def _rule(**kwargs):
    base = {
        "id": "R-T",
        "approval_id": "APR-T",
        "applicability_conditions": [
            ApplicabilityCondition(
                field="F-PRD-01", op=ApplicabilityOp("eq"), value=True
            )
        ],
        "version": "1",
    }
    base.update(kwargs)
    return ApprovalRule(**base)


FACTS = {"F-PRD-01": True}


class TestEffectiveWindow:
    def test_before_effective_from_is_not_in_force(self):
        rule = _rule(effective_from=date(2026, 1, 27))
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2026, 1, 26))
        assert ev.result == "does_not_apply"
        assert "not in force" in ev.reason

    def test_on_effective_from_is_active(self):
        rule = _rule(effective_from=date(2026, 1, 27))
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2026, 1, 27))
        assert ev.result == "applies"

    def test_inside_window_is_active(self):
        rule = _rule(
            effective_from=date(2025, 1, 1), effective_to=date(2027, 12, 31)
        )
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2026, 6, 15))
        assert ev.result == "applies"

    def test_on_effective_to_is_active(self):
        rule = _rule(effective_to=date(2026, 12, 31))
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2026, 12, 31))
        assert ev.result == "applies"

    def test_after_effective_to_is_inactive(self):
        rule = _rule(effective_to=date(2026, 12, 31))
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2027, 1, 1))
        assert ev.result == "does_not_apply"
        assert "no longer in force" in ev.reason

    def test_open_ended_effective_to(self):
        rule = _rule(effective_from=date(2020, 1, 1))
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2030, 5, 5))
        assert ev.result == "applies"

    def test_open_ended_effective_from(self):
        rule = _rule(effective_to=date(2030, 1, 1))
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(1999, 5, 5))
        assert ev.result == "applies"

    def test_no_dates_preserves_behavior(self):
        rule = _rule()
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2026, 6, 15))
        assert ev.result == "applies"
        ev_missing = evaluate_rule(rule, {}, evaluation_date=date(2026, 6, 15))
        assert ev_missing.result == "insufficient_data"

    def test_no_evaluation_date_preserves_behavior(self):
        rule = _rule(
            effective_from=date(2026, 1, 27), effective_to=date(2026, 12, 31)
        )
        ev = evaluate_rule(rule, FACTS)
        assert ev.result == "applies"

    def test_window_precheck_keeps_traceability(self):
        rule = _rule(effective_from=date(2026, 1, 27))
        ev = evaluate_rule(rule, FACTS, evaluation_date=date(2026, 1, 1))
        assert ev.rule_id == "R-T"
        assert ev.approval_id == "APR-T"
        assert ev.required_inputs == ["F-PRD-01"]

    def test_threaded_through_batch_evaluation(self):
        rule = _rule(effective_from=date(2026, 1, 27))
        before = evaluate_approval_applicability(
            [rule], FACTS, evaluation_date=date(2026, 1, 1)
        )
        inside = evaluate_approval_applicability(
            [rule], FACTS, evaluation_date=date(2026, 6, 1)
        )
        assert before[0].result == "does_not_apply"
        assert inside[0].result == "applies"
