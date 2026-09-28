"""Tests for regulatory explanation service."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.regulatory.explanation import (
    _build_applicability_explanation,
    _extract_source_ids_from_rules,
    _source_refs_to_ids,
    answer_query,
    explain_approval,
    explain_orchestration_with_citations,
)
from app.regulatory.models import Citation, EvidenceState, RegulatoryExplanation
from app.rules.models import ApprovalRule, SourceRef


class TestSourceRefExtraction:
    """Test source ID extraction helpers."""

    def test_source_refs_to_ids(self):
        """Extracts source IDs from SourceRef objects."""
        refs = [
            SourceRef(source_id="S01", citation_span="test"),
            SourceRef(source_id="S02", citation_span="test2"),
        ]
        result = _source_refs_to_ids(refs)
        assert result == ["S01", "S02"]

    def test_empty_refs(self):
        """Empty refs returns empty list."""
        result = _source_refs_to_ids([])
        assert result == []

    def test_extract_from_rules(self):
        """Extract source IDs from approval rules."""
        rules = [
            ApprovalRule(
                id="R1", approval_id="A01",
                source_refs=[SourceRef(source_id="S01", citation_span="test")],
                applicability_conditions=[], version="1",
            ),
            ApprovalRule(
                id="R2", approval_id="A01",
                source_refs=[SourceRef(source_id="S02", citation_span="test")],
                applicability_conditions=[], version="1",
            ),
            ApprovalRule(
                id="R3", approval_id="A02",
                source_refs=[SourceRef(source_id="S03", citation_span="test")],
                applicability_conditions=[], version="1",
            ),
        ]
        result = _extract_source_ids_from_rules(rules, "A01")
        assert "S01" in result
        assert "S02" in result
        assert "S03" not in result

    def test_extract_deduplicates(self):
        """Extracted IDs are deduplicated."""
        rules = [
            ApprovalRule(
                id="R1", approval_id="A01",
                source_refs=[SourceRef(source_id="S01", citation_span="test")],
                applicability_conditions=[], version="1",
            ),
            ApprovalRule(
                id="R2", approval_id="A01",
                source_refs=[SourceRef(source_id="S01", citation_span="test2")],
                applicability_conditions=[], version="1",
            ),
        ]
        result = _extract_source_ids_from_rules(rules, "A01")
        assert result.count("S01") == 1


class TestBuildApplicabilityExplanation:
    """Test deterministic explanation builder."""

    def test_applies_with_citations(self):
        """APPLIES result with citations produces sufficient explanation."""
        refs = [SourceRef(source_id="S01", citation_span="test")]
        citations = [
            Citation(
                source_id="S01", title="Test Source", authority="Auth",
                url="https://example.com", source_type="portal",
                excerpt="test excerpt", relevance_rank=0.9,
            )
        ]
        answer, evidence = _build_applicability_explanation(
            "A01", "APPLIES", "Triggered by fact X", refs, citations,
        )
        assert "APPLIES" not in answer.upper() or "applies" in answer.lower()
        assert "Test Source" in answer
        assert evidence == EvidenceState.SUFFICIENT

    def test_does_not_apply(self):
        """DOES_NOT_APPLY result produces explanation."""
        answer, evidence = _build_applicability_explanation(
            "A01", "DOES_NOT_APPLY", "Not triggered", [], [],
        )
        assert "does not apply" in answer.lower()
        assert evidence == EvidenceState.SUFFICIENT

    def test_conditional(self):
        """CONDITIONAL result produces partial evidence."""
        answer, evidence = _build_applicability_explanation(
            "A01", "CONDITIONAL", "Needs more data", [], [],
        )
        assert "conditionally" in answer.lower()
        assert evidence == EvidenceState.PARTIAL

    def test_insufficient_data(self):
        """INSUFFICIENT_DATA produces insufficient evidence."""
        answer, evidence = _build_applicability_explanation(
            "A01", "INSUFFICIENT_DATA", "Missing facts", [], [],
        )
        assert "insufficient" in answer.lower()
        assert evidence == EvidenceState.INSUFFICIENT


class TestExplainApproval:
    """Test explain_approval with mocked client."""

    def test_returns_explanation(self):
        """Returns a RegulatoryExplanation."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = []

        rules = [
            ApprovalRule(
                id="R1", approval_id="A01",
                source_refs=[SourceRef(source_id="S01", citation_span="test")],
                applicability_conditions=[], version="1",
            ),
        ]

        result = explain_approval(
            db, "A01", rules, "APPLIES", "Triggered by industry type",
        )
        assert isinstance(result, RegulatoryExplanation)
        assert result.approval_id == "A01"
        assert result.evidence_state in (
            EvidenceState.SUFFICIENT, EvidenceState.PARTIAL, EvidenceState.INSUFFICIENT,
        )

    def test_no_sources_returns_explanation(self):
        """Works when no source IDs found."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        result = explain_approval(db, "A99", [], "UNKNOWN", "")
        assert isinstance(result, RegulatoryExplanation)
        assert result.approval_id == "A99"


class TestAnswerQuery:
    """Test answer_query with mocked client."""

    def test_empty_query(self):
        """Empty query returns insufficient evidence."""
        client = MagicMock()
        result = answer_query(client, "")
        assert result.evidence_state == EvidenceState.INSUFFICIENT

    def test_whitespace_query(self):
        """Whitespace-only query returns insufficient evidence."""
        client = MagicMock()
        result = answer_query(client, "   ")
        assert result.evidence_state == EvidenceState.INSUFFICIENT

    def test_no_results(self):
        """No search results returns insufficient evidence."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = []

        result = answer_query(db, "nonexistent topic xyz")
        assert result.evidence_state == EvidenceState.INSUFFICIENT
        assert "No relevant" in result.answer

    def test_with_results(self):
        """Search results produce citations."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.side_effect = [
            [{
                "id": "1", "source_id": "S01",
                "chunk_text": "Fire safety regulations",
                "chunk_index": 0, "metadata": {}, "rank": 0.9,
            }],
            [{
                "id": "S01", "title": "Fire Regulations", "authority": "Gujarat",
                "source_type": "Gazette", "url": "https://example.com",
                "jurisdiction": "IN-GJ", "source_class": "Official",
                "notes": "", "checked_date": "2026-09-15", "trust_tier": "govt-portal",
                "content_hash": "hash",
            }],
            [{"chunk_text": "Fire safety", "chunk_index": 0}],
        ]

        result = answer_query(db, "fire safety regulations")
        assert isinstance(result, RegulatoryExplanation)
        assert len(result.citations) >= 1


class TestExplainOrchestrationWithCitations:
    """Test orchestration citation enrichment."""

    def test_with_citations(self):
        """Adds citation summary to orchestration explanation."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.side_effect = [
            [{
                "id": "S01", "title": "Fire Regulations",
                "authority": "Gujarat", "source_type": "Gazette",
                "url": "https://example.com",
                "jurisdiction": "IN-GJ", "source_class": "Official",
                "notes": "", "checked_date": "2026-09-15",
                "trust_tier": "govt-portal", "content_hash": "hash",
            }],
            [{"chunk_text": "Fire safety rules", "chunk_index": 0}],
        ]

        rules = [
            ApprovalRule(
                id="R1", approval_id="A01",
                source_refs=[SourceRef(source_id="S01", citation_span="test")],
                applicability_conditions=[], version="1",
            ),
        ]

        result = explain_orchestration_with_citations(
            db, "A01", rules, "Status: READY",
        )
        assert isinstance(result, RegulatoryExplanation)
        assert "Fire Regulations" in result.answer

    def test_no_citations(self):
        """Handles missing citations gracefully."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = []

        result = explain_orchestration_with_citations(
            db, "A99", [], "Status: READY",
        )
        assert isinstance(result, RegulatoryExplanation)
        assert result.evidence_state == EvidenceState.INSUFFICIENT
