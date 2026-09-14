"""Tests for the applicability evaluation engine."""
from __future__ import annotations

from app.rules.engine import evaluate_applicability
from app.rules.models import (
    ApplicabilityCondition,
    ApplicabilityOp,
    EntityType,
    FixedDateRule,
    Frequency,
    InstrumentRef,
    Obligation,
    ObligationType,
    Penalty,
    SourceRef,
)


def _make_obligation(
    *,
    summary: str = "Test obligation",
    conditions: list[dict] | None = None,
    source_id: str = "src-1",
) -> Obligation:
    """Create a test obligation with minimal required fields."""
    return Obligation(
        canonical_id="test|obligation|1",
        instrument_ref=InstrumentRef(instrument_id="IN/test-act-2024"),
        type=ObligationType.FILING,
        summary=summary,
        applicability_conditions=[
            ApplicabilityCondition(
                field=c["field"],
                op=ApplicabilityOp(c["op"]),
                value=c["value"],
            )
            for c in (conditions or [])
        ],
        frequency=Frequency.ANNUAL,
        deadline_rule=FixedDateRule(kind="fixed-date", month=3, day=31),
        proof_types=[],
        penalty=Penalty(has_imprisonment=False),
        source_refs=[SourceRef(source_id=source_id, citation_span="s.1")],
        version="1",
        confidence=0.95,
    )


def _make_entity(**overrides) -> dict:
    """Create entity profile fields."""
    base = {
        "entity_id": "ent-1",
        "org_id": "org-1",
        "entity_type": EntityType.PVT_LTD,
        "sector": "chemicals",
        "jurisdictions": ["IN-GJ"],
        "headcount": 150,
        "annual_turnover_inr": 50_000_000,
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────
# eq operator
# ─────────────────────────────────────────────────────────────


class TestEqOperator:
    def test_matches_exact_value(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(sector="chemicals"))
        obligation = _make_obligation(
            conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1

    def test_rejects_non_matching_value(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(sector="textiles"))
        obligation = _make_obligation(
            conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 0


# ─────────────────────────────────────────────────────────────
# in operator
# ─────────────────────────────────────────────────────────────


class TestInOperator:
    def test_matches_when_value_in_list(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(sector="chemicals"))
        obligation = _make_obligation(
            conditions=[
                {"field": "sector", "op": "in", "value": ["chemicals", "pharma"]}
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1

    def test_rejects_when_value_not_in_list(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(sector="textiles"))
        obligation = _make_obligation(
            conditions=[
                {"field": "sector", "op": "in", "value": ["chemicals", "pharma"]}
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 0

    def test_in_with_array_entity_field(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(
            **_make_entity(jurisdictions=["IN-GJ", "IN-MH"])
        )
        obligation = _make_obligation(
            conditions=[
                {
                    "field": "jurisdictions",
                    "op": "in",
                    "value": ["IN-GJ", "IN-KA"],
                }
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────
# numeric operators
# ─────────────────────────────────────────────────────────────


class TestNumericOperators:
    def test_gte_operator(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(headcount=100))
        obligation = _make_obligation(
            conditions=[{"field": "headcount", "op": "gte", "value": 50}]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1

    def test_gte_exact_boundary(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(headcount=50))
        obligation = _make_obligation(
            conditions=[{"field": "headcount", "op": "gte", "value": 50}]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1

    def test_gte_below_boundary(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(headcount=49))
        obligation = _make_obligation(
            conditions=[{"field": "headcount", "op": "gte", "value": 50}]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 0

    def test_lte_operator(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(annual_turnover_inr=5_000_000))
        obligation = _make_obligation(
            conditions=[
                {
                    "field": "annual_turnover_inr",
                    "op": "lte",
                    "value": 10_000_000,
                }
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1

    def test_gt_operator(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(headcount=101))
        obligation = _make_obligation(
            conditions=[{"field": "headcount", "op": "gt", "value": 100}]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1

    def test_lt_operator(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(headcount=99))
        obligation = _make_obligation(
            conditions=[{"field": "headcount", "op": "lt", "value": 100}]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────
# multiple conditions (AND logic)
# ─────────────────────────────────────────────────────────────


class TestMultipleConditions:
    def test_all_conditions_must_pass(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(sector="chemicals", headcount=150))
        obligation = _make_obligation(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1

    def test_one_condition_fails(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(sector="textiles", headcount=150))
        obligation = _make_obligation(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 0

    def test_empty_conditions_always_applies(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity())
        obligation = _make_obligation(conditions=[])
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1


# ─────────────────────────────────────────────────────────────
# filtering behavior
# ─────────────────────────────────────────────────────────────


class TestFiltering:
    def test_filters_multiple_obligations(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(sector="chemicals"))
        o1 = _make_obligation(
            summary="Chemicals only",
            conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}],
        )
        o2 = _make_obligation(
            summary="Textiles only",
            conditions=[{"field": "sector", "op": "eq", "value": "textiles"}],
        )
        result = evaluate_applicability(entity, [o1, o2])
        assert len(result) == 1
        assert result[0].summary == "Chemicals only"

    def test_no_obligations(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity())
        result = evaluate_applicability(entity, [])
        assert result == []


# ─────────────────────────────────────────────────────────────
# boundary: unknown field
# ─────────────────────────────────────────────────────────────


class TestBoundary:
    def test_unknown_field_returns_none(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity())
        obligation = _make_obligation(
            conditions=[
                {"field": "nonexistent_field", "op": "eq", "value": "anything"}
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        # Unknown field => lookupField returns None, eq check fails
        assert len(result) == 0

    def test_entity_type_matches(self):
        from app.rules.models import EntityProfile

        entity = EntityProfile(**_make_entity(entity_type=EntityType.PVT_LTD))
        obligation = _make_obligation(
            conditions=[
                {"field": "entity_type", "op": "eq", "value": "pvt-ltd"}
            ]
        )
        result = evaluate_applicability(entity, [obligation])
        assert len(result) == 1
