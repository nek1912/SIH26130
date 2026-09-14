"""Tests for deadline computation."""
from __future__ import annotations

from datetime import date

from app.rules.deadline import compute_due_date
from app.rules.models import (
    EntityProfile,
    EntityType,
    EventOffsetRule,
    FixedDateRule,
    Frequency,
    InstrumentRef,
    Obligation,
    ObligationType,
    Penalty,
    PeriodOffsetRule,
    SourceRef,
)


def _make_obligation(
    deadline_rule=None,
    frequency: Frequency = Frequency.ANNUAL,
) -> Obligation:
    if deadline_rule is None:
        deadline_rule = FixedDateRule(kind="fixed-date", month=3, day=31)
    return Obligation(
        canonical_id="test||filing",
        instrument_ref=InstrumentRef(instrument_id="IN/test"),
        type=ObligationType.FILING,
        summary="Test",
        applicability_conditions=[],
        frequency=frequency,
        deadline_rule=deadline_rule,
        proof_types=[],
        penalty=Penalty(has_imprisonment=False),
        source_refs=[SourceRef(source_id="s1", citation_span="s.1")],
        version="1",
        confidence=1.0,
    )


def _make_entity(**overrides) -> EntityProfile:
    base = {
        "entity_id": "e1",
        "org_id": "o1",
        "entity_type": EntityType.PVT_LTD,
        "sector": "chem",
        "jurisdictions": ["IN-GJ"],
        "headcount": 10,
        "annual_turnover_inr": 1_000_000,
    }
    base.update(overrides)
    return EntityProfile(**base)


# ─────────────────────────────────────────────────────────────
# fixed-date
# ─────────────────────────────────────────────────────────────


class TestFixedDate:
    def test_same_year_future_date(self):
        obligation = _make_obligation(
            deadline_rule=FixedDateRule(kind="fixed-date", month=6, day=15)
        )
        entity = _make_entity()
        result = compute_due_date(obligation, entity, date(2026, 1, 1))
        assert result == date(2026, 6, 15)

    def test_same_year_past_date_advances(self):
        obligation = _make_obligation(
            deadline_rule=FixedDateRule(kind="fixed-date", month=3, day=31)
        )
        entity = _make_entity()
        # Reference is after March 31 → should advance to next year
        result = compute_due_date(obligation, entity, date(2026, 5, 1))
        assert result == date(2027, 3, 31)

    def test_exact_boundary(self):
        obligation = _make_obligation(
            deadline_rule=FixedDateRule(kind="fixed-date", month=3, day=31)
        )
        entity = _make_entity()
        # Reference is March 31 → candidate is same day, not < reference
        result = compute_due_date(obligation, entity, date(2026, 3, 31))
        assert result == date(2026, 3, 31)

    def test_day_before_boundary(self):
        obligation = _make_obligation(
            deadline_rule=FixedDateRule(kind="fixed-date", month=3, day=31)
        )
        entity = _make_entity()
        result = compute_due_date(obligation, entity, date(2026, 3, 30))
        assert result == date(2026, 3, 31)


# ─────────────────────────────────────────────────────────────
# event-offset
# ─────────────────────────────────────────────────────────────


class TestEventOffset:
    def test_valid_event_date(self):
        obligation = _make_obligation(
            deadline_rule=EventOffsetRule(
                kind="event-offset", days=30, event="incorporation_date"
            )
        )
        entity = _make_entity(incorporation_date=date(2026, 1, 15))
        result = compute_due_date(obligation, entity, date(2026, 6, 1))
        assert result == date(2026, 2, 14)

    def test_missing_event_returns_none(self):
        obligation = _make_obligation(
            deadline_rule=EventOffsetRule(
                kind="event-offset", days=30, event="incorporation_date"
            )
        )
        entity = _make_entity()  # no incorporation_date
        result = compute_due_date(obligation, entity, date(2026, 6, 1))
        assert result is None

    def test_event_date_as_string(self):
        obligation = _make_obligation(
            deadline_rule=EventOffsetRule(
                kind="event-offset", days=15, event="incorporation_date"
            )
        )
        entity_dict = {
            "entity_id": "e1",
            "org_id": "o1",
            "entity_type": EntityType.PVT_LTD,
            "sector": "chem",
            "jurisdictions": ["IN-GJ"],
            "headcount": 10,
            "annual_turnover_inr": 1_000_000,
            "incorporation_date": "2026-06-01",
        }
        entity = EntityProfile(**entity_dict)
        result = compute_due_date(obligation, entity, date(2026, 6, 15))
        assert result == date(2026, 6, 16)


# ─────────────────────────────────────────────────────────────
# period-offset
# ─────────────────────────────────────────────────────────────


class TestPeriodOffset:
    def test_annual_period_offset(self):
        """Indian fiscal year ends March 31. period-offset 30 → April 30."""
        obligation = _make_obligation(
            deadline_rule=PeriodOffsetRule(kind="period-offset", days=30),
            frequency=Frequency.ANNUAL,
        )
        entity = _make_entity()
        # Reference in Jan 2026 → FY ends March 31, 2026
        result = compute_due_date(obligation, entity, date(2026, 1, 15))
        assert result == date(2026, 4, 30)

    def test_monthly_period_offset(self):
        """Monthly: last day of current month + days."""
        obligation = _make_obligation(
            deadline_rule=PeriodOffsetRule(kind="period-offset", days=15),
            frequency=Frequency.MONTHLY,
        )
        entity = _make_entity()
        # January 2026: last day = Jan 31, + 15 = Feb 15
        result = compute_due_date(obligation, entity, date(2026, 1, 10))
        assert result == date(2026, 2, 15)

    def test_one_time_returns_none(self):
        obligation = _make_obligation(
            deadline_rule=PeriodOffsetRule(kind="period-offset", days=10),
            frequency=Frequency.ONE_TIME,
        )
        entity = _make_entity()
        result = compute_due_date(obligation, entity, date(2026, 1, 1))
        assert result is None

    def test_event_driven_returns_none(self):
        obligation = _make_obligation(
            deadline_rule=PeriodOffsetRule(kind="period-offset", days=10),
            frequency=Frequency.EVENT_DRIVEN,
        )
        entity = _make_entity()
        result = compute_due_date(obligation, entity, date(2026, 1, 1))
        assert result is None

    def test_quarterly_period_offset(self):
        """Quarterly: Q1 ends Mar 31, Q2 ends Jun 30, Q3 ends Sep 30, Q4 ends Dec 31."""
        obligation = _make_obligation(
            deadline_rule=PeriodOffsetRule(kind="period-offset", days=0),
            frequency=Frequency.QUARTERLY,
        )
        entity = _make_entity()
        # Jan 2026 → Q1 ends Mar 31
        result = compute_due_date(obligation, entity, date(2026, 1, 15))
        assert result == date(2026, 3, 31)


# ─────────────────────────────────────────────────────────────
# edge cases
# ─────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_zero_days_offset(self):
        obligation = _make_obligation(
            deadline_rule=EventOffsetRule(
                kind="event-offset", days=0, event="incorporation_date"
            )
        )
        entity = _make_entity(incorporation_date=date(2026, 3, 15))
        result = compute_due_date(obligation, entity, date(2026, 6, 1))
        assert result == date(2026, 3, 15)
