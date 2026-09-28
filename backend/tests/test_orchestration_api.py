"""Tests for orchestration API endpoint."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.main import app


@pytest.fixture(autouse=True)
def _clear_overrides():
    """Reset dependency overrides between tests."""
    yield
    app.dependency_overrides.clear()


class TestOrchestrationEndpoint:
    """Test GET /applications/{id}/orchestration."""

    def _make_user(self) -> UserContext:
        return UserContext(
            user_id=uuid4(),
            email="test@test.com",
            role=SystemRole.ADMIN,
            raw_claims={},
        )

    def _make_client(self):
        """Create a test client with mocked dependencies."""
        from app.api.deps import (
            get_applications_repository,
            get_consistency_repository,
            get_documents_repository,
            get_project_facts_repository,
            get_workflow_events_repository,
        )
        from app.repositories.applications import ApplicationsRepository
        from app.repositories.consistency import ConsistencyRepository
        from app.repositories.documents import DocumentsRepository
        from app.repositories.project_facts import ProjectFactsRepository
        from app.repositories.workflow_events import WorkflowEventsRepository

        app_repo = MagicMock(spec=ApplicationsRepository)
        facts_repo = MagicMock(spec=ProjectFactsRepository)
        facts_repo.get_by_project.return_value = None
        docs_repo = MagicMock(spec=DocumentsRepository)
        docs_repo.list_documents_for_application.return_value = []
        events_repo = MagicMock(spec=WorkflowEventsRepository)
        events_repo.list_for_application.return_value = []
        consistency_repo = MagicMock(spec=ConsistencyRepository)
        consistency_repo.get_latest_result.return_value = None
        app.dependency_overrides[get_applications_repository] = lambda: app_repo
        app.dependency_overrides[get_project_facts_repository] = (
            lambda: facts_repo
        )
        app.dependency_overrides[get_documents_repository] = lambda: docs_repo
        app.dependency_overrides[get_workflow_events_repository] = (
            lambda: events_repo
        )
        app.dependency_overrides[get_consistency_repository] = (
            lambda: consistency_repo
        )

        user = self._make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        return TestClient(app), app_repo

    @patch("app.api.orchestration.orchestrate_application_full")
    def test_orchestration_endpoint_returns_200(self, mock_orchestrate):
        """Orchestration endpoint returns 200 with valid application."""
        test_client = TestClient(app)
        app_id = str(uuid4())
        project_id = str(uuid4())

        mock_orch_result = MagicMock()
        mock_orch_result.model_dump.return_value = {
            "application_id": app_id,
            "overall_status": "ready",
            "approvals": {},
            "total_blockers": 0,
            "next_action": None,
            "stage_number": None,
            "explanation": "Test explanation",
        }
        mock_orchestrate.return_value = mock_orch_result

        # Mock application (persisted GJ identity resolves the GJ pack)
        test_client, app_repo = self._make_client()
        app_repo.get_by_id.return_value = {
            "id": app_id,
            "project_id": project_id,
            "approval_id": "A01",
            "approval_code": "A01",
            "status": "under_review",
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        }

        response = test_client.get(
            f"/applications/{app_id}/orchestration",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200

        data = response.json()
        assert "application_id" in data
        assert "overall_status" in data
        assert "approvals" in data
        assert "total_blockers" in data

    def test_orchestration_endpoint_returns_401(self):
        """Orchestration endpoint returns 401 without auth token."""
        test_client = TestClient(app)
        app_id = str(uuid4())

        response = test_client.get(f"/applications/{app_id}/orchestration")

        assert response.status_code == 401

    def test_orchestration_endpoint_returns_404(self):
        """Orchestration endpoint returns 404 for non-existent application."""
        test_client, _ = self._make_client()
        app_id = str(uuid4())

        from app.api.deps import get_applications_repository

        app_repo = MagicMock()
        app_repo.get_by_id.return_value = None
        app.dependency_overrides[get_applications_repository] = lambda: app_repo

        response = test_client.get(
            f"/applications/{app_id}/orchestration",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 404
