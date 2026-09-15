"""Integration test for applicability evaluation flow."""



from app.rules.engine import evaluate_applicability
from app.rules.models import EntityProfile, Obligation


def test_applicability_evaluation():
    """Test that applicability evaluation works end-to-end."""
    # Create a mock obligation with correct structure
    obligation = Obligation(
        canonical_id="test-obl-1",
        instrument_ref={"instrument_id": "instrument-1", "section": "3"},
        type="filing",
        summary="Test obligation",
        applicability_conditions=[
            {"kind": "condition", "field": "sector", "op": "eq", "value": "chemicals"}
        ],
        frequency="annual",
        deadline_rule={"kind": "fixed-date", "month": 3, "day": 31},
        proof_types=[],
        penalty={"has_imprisonment": False},
        source_refs=[{"source_id": "src-1", "citation_span": "Section 3"}],
        version="1",
        confidence=1.0,
    )

    # Create entity profile that matches
    profile = EntityProfile(
        entity_id="entity-1",
        org_id="org-1",
        entity_type="pvt-ltd",
        sector="chemicals",
        jurisdictions=["IN-GJ"],
        headcount=50,
        annual_turnover_inr=10000000,
    )

    # Evaluate
    results = evaluate_applicability(profile, [obligation])

    # Should be applicable
    assert len(results) == 1
    assert results[0].canonical_id == "test-obl-1"


def test_applicability_no_match():
    """Test that applicability evaluation returns no match when conditions don't match."""
    # Create a mock obligation with correct structure
    obligation = Obligation(
        canonical_id="test-obl-1",
        instrument_ref={"instrument_id": "instrument-1", "section": "3"},
        type="filing",
        summary="Test obligation",
        applicability_conditions=[
            {"kind": "condition", "field": "sector", "op": "eq", "value": "chemicals"}
        ],
        frequency="annual",
        deadline_rule={"kind": "fixed-date", "month": 3, "day": 31},
        proof_types=[],
        penalty={"has_imprisonment": False},
        source_refs=[{"source_id": "src-1", "citation_span": "Section 3"}],
        version="1",
        confidence=1.0,
    )

    # Create entity profile that doesn't match
    profile = EntityProfile(
        entity_id="entity-1",
        org_id="org-1",
        entity_type="pvt-ltd",
        sector="textiles",
        jurisdictions=["IN-GJ"],
        headcount=50,
        annual_turnover_inr=10000000,
    )

    # Evaluate
    results = evaluate_applicability(profile, [obligation])

    # Should not be applicable (empty list)
    assert len(results) == 0