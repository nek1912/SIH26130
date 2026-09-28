"""Tests for regulatory API endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.main import app
from app.regulatory.models import (
    Citation,
    EvidenceState,
    RegulatoryExplanation,
)


@pytest.fixture(autouse=True)
def _clear_overrides():
    """Reset dependency overrides between tests."""
    yield
    app.dependency_overrides.clear()


def _make_user() -> UserContext:
    return UserContext(
        user_id=uuid4(),
        email="test@test.com",
        role=SystemRole.ADMIN,
        raw_claims={},
    )


def _make_test_client():
    """Create test client with mocked DB and auth."""
    from app.api.deps import get_db_client, get_sources_repository

    client = MagicMock()
    repo = MagicMock()
    user = _make_user()

    app.dependency_overrides[get_db_client] = lambda: client
    app.dependency_overrides[get_sources_repository] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app), client, repo


class TestListSources:
    """Test GET /sources."""

    def test_returns_200(self):
        """Returns 200 with source list."""
        test_client, _, repo = _make_test_client()
        repo.get_all_sources.return_value = [
            {"id": "S01", "title": "Test"},
            {"id": "S02", "title": "Test 2"},
        ]

        response = test_client.get(
            "/sources",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_returns_401_without_auth(self):
        """Returns 401 without auth token."""
        test_client = TestClient(app)
        response = test_client.get("/sources")
        assert response.status_code == 401

    def test_pagination_params(self):
        """Accepts limit and offset params."""
        test_client, _, repo = _make_test_client()
        repo.get_all_sources.return_value = []

        response = test_client.get(
            "/sources?limit=10&offset=20",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        repo.get_all_sources.assert_called_once_with(limit=10, offset=20)


class TestGetSource:
    """Test GET /sources/{source_id}."""

    def test_returns_source_with_chunks(self):
        """Returns source and its chunks."""
        test_client, _, repo = _make_test_client()
        repo.get_by_id_text.return_value = {"id": "S01", "title": "Test"}
        repo.get_chunks_for_source.return_value = [
            {"chunk_text": "chunk 1", "chunk_index": 0},
        ]

        response = test_client.get(
            "/sources/S01",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "source" in data
        assert "chunks" in data
        assert len(data["chunks"]) == 1

    def test_returns_404_for_unknown_source(self):
        """Returns 404 for unknown source ID."""
        test_client, _, repo = _make_test_client()
        repo.get_by_id_text.return_value = None

        response = test_client.get(
            "/sources/S99",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 404


class TestSeedSources:
    """Test POST /sources/seed."""

    @patch("app.api.regulatory.get_seed_source_dicts")
    @patch("app.api.regulatory.get_seed_chunks")
    def test_seeds_sources(self, mock_chunks, mock_source_dicts):
        """Seeds sources and chunks."""
        test_client, _, repo = _make_test_client()
        mock_source_dicts.return_value = [
            {"id": "S01", "title": "Test"},
        ]
        mock_chunks.return_value = [
            {"source_id": "S01", "chunk_text": "chunk", "chunk_index": 0, "metadata": {}},
        ]
        repo.get_by_id_text.return_value = None
        repo.get_chunks_for_source.return_value = []
        repo.count_sources.return_value = 1
        repo.count_chunks.return_value = 1

        response = test_client.post(
            "/sources/seed",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sources_seeded"] == 1

    @patch("app.api.regulatory.get_seed_source_dicts")
    @patch("app.api.regulatory.get_seed_chunks")
    def test_idempotent(self, mock_chunks, mock_source_dicts):
        """Existing sources are not re-created."""
        test_client, _, repo = _make_test_client()
        mock_source_dicts.return_value = [{"id": "S01"}]
        mock_chunks.return_value = [{"source_id": "S01"}]
        repo.get_by_id_text.return_value = {"id": "S01"}  # already exists
        repo.get_chunks_for_source.return_value = [{"id": "1"}]  # chunks exist
        repo.count_sources.return_value = 32
        repo.count_chunks.return_value = 96

        response = test_client.post(
            "/sources/seed",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sources_seeded"] == 0


class TestExplainRegulatory:
    """Test POST /regulatory/explain."""

    @patch("app.api.regulatory.answer_query")
    def test_returns_explanation(self, mock_answer):
        """Returns explanation for a query."""
        test_client, _, _ = _make_test_client()
        mock_answer.return_value = RegulatoryExplanation(
            answer="Test answer",
            citations=[],
            evidence_state=EvidenceState.INSUFFICIENT,
            query="test query",
        )

        response = test_client.post(
            "/regulatory/explain",
            json={"query": "fire safety requirements"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert "evidence_state" in data

    @patch("app.api.regulatory.answer_query")
    def test_includes_citations(self, mock_answer):
        """Response includes citations."""
        test_client, _, _ = _make_test_client()
        mock_answer.return_value = RegulatoryExplanation(
            answer="Test answer",
            citations=[
                Citation(
                    source_id="S01", title="Fire Regs", authority="Gujarat",
                    url="https://example.com", source_type="Gazette",
                    excerpt="excerpt", relevance_rank=0.9,
                )
            ],
            evidence_state=EvidenceState.SUFFICIENT,
            query="test",
        )

        response = test_client.post(
            "/regulatory/explain",
            json={"query": "fire regulations"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["citations"]) == 1
        assert data["citations"][0]["source_id"] == "S01"


class TestExplainApprovalEndpoint:
    """Test GET /regulatory/approval/{id}/explanation."""

    @patch("app.api.regulatory.explain_approval")
    @patch("app.api.regulatory.load_regulatory_pack")
    def test_returns_explanation(self, mock_pack, mock_explain):
        """Returns explanation for an approval."""
        test_client, _, _ = _make_test_client()
        mock_pack.return_value.approval_rules = []
        mock_explain.return_value = RegulatoryExplanation(
            answer="Approval applies because...",
            citations=[],
            evidence_state=EvidenceState.SUFFICIENT,
            query="applicability:A01",
            approval_id="A01",
        )

        response = test_client.get(
            "/regulatory/approval/A01/explanation?applicability=APPLIES&reason=test",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["approval_id"] == "A01"


class TestOrchestrationCitations:
    """Test GET /regulatory/orchestration/{app_id}/citations."""

    @patch("app.api.regulatory.explain_orchestration_with_citations")
    @patch("app.api.regulatory.load_regulatory_pack")
    def test_returns_citations(self, mock_pack, mock_explain):
        """Returns enriched explanation with citations."""
        test_client, _, _ = _make_test_client()
        mock_pack.return_value.approval_rules = []
        mock_explain.return_value = RegulatoryExplanation(
            answer="Enriched explanation",
            citations=[],
            evidence_state=EvidenceState.INSUFFICIENT,
            query="orchestration:A01",
            approval_id="A01",
        )

        response = test_client.get(
            "/regulatory/orchestration/app-1/citations?approval_id=A01&explanation=test",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200


class TestSourceStatus:
    """Test GET /sources/status."""

    def test_returns_counts(self):
        """Returns source and chunk counts."""
        test_client, _, repo = _make_test_client()
        repo.count_sources.return_value = 32
        repo.count_chunks.return_value = 96

        response = test_client.get(
            "/sources/status",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_count"] == 32
        assert data["chunk_count"] == 96
