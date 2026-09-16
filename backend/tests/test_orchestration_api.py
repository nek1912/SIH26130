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
        from app.api.deps import get_db_client

        client = MagicMock()
        app.dependency_overrides[get_db_client] = lambda: client

        user = self._make_user()
        app.dependency_overrides[get_current_user] = lambda: user

        return TestClient(app), client

    @patch("app.api.orchestration.orchestrate_application_full")
    def test_orchestration_endpoint_returns_200(self, mock_orchestrate):
        """Orchestration endpoint returns 200 with valid application."""
        test_client, db_client = self._make_client()
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

        # Mock application
        mock_app = MagicMock()
        mock_app.data = [{
            "id": app_id,
            "project_id": project_id,
            "approval_id": "A01",
            "status": "under_review",
        }]

        # Mock project facts
        mock_facts = MagicMock()
        mock_facts.data = [{
            "id": str(uuid4()),
            "project_id": project_id,
            "project_name": "Test Project",
        }]

        # Mock documents (empty)
        mock_docs = MagicMock()
        mock_docs.data = []

        def side_effect(table_name):
            m = MagicMock()
            if table_name == "applications":
                m.select.return_value.eq.return_value.execute.return_value = mock_app
            elif table_name == "project_facts":
                m.select.return_value.eq.return_value.execute.return_value = mock_facts
            elif table_name == "documents":
                chain = m.select.return_value.eq.return_value.order
                chain.return_value.execute.return_value = mock_docs
            return m

        db_client.table.side_effect = side_effect

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
        test_client, db_client = self._make_client()
        app_id = str(uuid4())

        mock_app = MagicMock()
        mock_app.data = []

        table_mock = MagicMock()
        db_client.table.return_value = table_mock
        table_mock.select.return_value.eq.return_value.execute.return_value = mock_app

        response = test_client.get(
            f"/applications/{app_id}/orchestration",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 404
