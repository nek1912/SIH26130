"""Tests for Pydantic regulatory models."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.rules.models import (
    FixedDateRule,
    Frequency,
    InstrumentRef,
    MinMax,
    Obligation,
    ObligationCandidate,
    ObligationType,
    Penalty,
    SourceRef,
)


class TestObligation:
    def test_valid_obligation(self):
        o = Obligation(
            canonical_id="IN/test||filing",
            instrument_ref=InstrumentRef(instrument_id="IN/test"),
            type=ObligationType.FILING,
            summary="Must file annual return",
            applicability_conditions=[],
            frequency=Frequency.ANNUAL,
            deadline_rule=FixedDateRule(kind="fixed-date", month=3, day=31),
            proof_types=["annual_return.pdf"],
            penalty=Penalty(has_imprisonment=False),
            source_refs=[SourceRef(source_id="s1", citation_span="s.1")],
            version="1",
            confidence=0.95,
        )
        assert o.canonical_id == "IN/test||filing"
        assert o.type == ObligationType.FILING

    def test_source_refs_min_length(self):
        with pytest.raises(ValidationError):
            Obligation(
                canonical_id="test",
                instrument_ref=InstrumentRef(instrument_id="IN/test"),
                type=ObligationType.FILING,
                summary="Test",
                applicability_conditions=[],
                frequency=Frequency.ANNUAL,
                deadline_rule=FixedDateRule(kind="fixed-date", month=3, day=31),
                proof_types=[],
                penalty=Penalty(has_imprisonment=False),
                source_refs=[],  # empty → should fail
                version="1",
                confidence=1.0,
            )

    def test_confidence_range(self):
        with pytest.raises(ValidationError):
            Obligation(
                canonical_id="test",
                instrument_ref=InstrumentRef(instrument_id="IN/test"),
                type=ObligationType.FILING,
                summary="Test",
                applicability_conditions=[],
                frequency=Frequency.ANNUAL,
                deadline_rule=FixedDateRule(kind="fixed-date", month=3, day=31),
                proof_types=[],
                penalty=Penalty(has_imprisonment=False),
                source_refs=[SourceRef(source_id="s1", citation_span="s.1")],
                version="1",
                confidence=1.5,  # > 1 → should fail
            )


class TestMinMax:
    def test_valid(self):
        m = MinMax(min=10, max=20)
        assert m.max >= m.min

    def test_invalid_max_lt_min(self):
        with pytest.raises(ValidationError):
            MinMax(min=20, max=10)

    def test_equal(self):
        m = MinMax(min=5, max=5)
        assert m.min == m.max


class TestPenalty:
    def test_imprisonment_with_range(self):
        p = Penalty(
            has_imprisonment=True,
            imprisonment_months=MinMax(min=6, max=24),
            fine_inr=MinMax(min=10000, max=50000),
        )
        assert p.has_imprisonment is True
        assert p.imprisonment_months is not None


class TestObligationCandidate:
    def test_no_canonical_id(self):
        c = ObligationCandidate(
            instrument_ref=InstrumentRef(instrument_id="IN/test"),
            type=ObligationType.FILING,
            summary="Test",
            applicability_conditions=[],
            frequency=Frequency.ONE_TIME,
            deadline_rule=FixedDateRule(kind="fixed-date", month=1, day=1),
            proof_types=[],
            penalty=Penalty(has_imprisonment=False),
            source_refs=[SourceRef(source_id="s1", citation_span="s.1")],
            confidence=0.8,
        )
        # Should not have canonical_id or version
        d = c.model_dump()
        assert "canonical_id" not in d
        assert "version" not in d
