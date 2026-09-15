"""Tests for consistency repository and API endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.consistency import router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.consistency.models import (
    ConsistencyOutcome,
    ConsistencyResult,
)
from app.repositories.consistency import ConsistencyRepository


class TestConsistencyRepository:
    def _make_repo(self) -> ConsistencyRepository:
        mock_client = MagicMock()
        return ConsistencyRepository(mock_client)

    def test_create_result_calls_insert(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [{"id": "result-1", "application_id": "app-1"}]
        repo.client.table.return_value.insert.return_value.execute.return_value = mock_result

        result = repo.create_result("app-1", "VALID", "2026-09-15T10:00:00", "1")
        assert result["id"] == "result-1"
        repo.client.table.assert_called_with("consistency_results")

    def test_create_findings_calls_insert(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [{"id": "finding-1"}]
        repo.client.table.return_value.insert.return_value.execute.return_value = mock_result

        findings_data = [{"result_id": "r1", "rule_id": "C01", "canonical_field": "plot_area_sqm"}]
        result = repo.create_findings(findings_data)
        assert len(result) == 1
        repo.client.table.assert_called_with("consistency_findings")

    def test_get_latest_result_returns_none_when_empty(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = []
        chain = repo.client.table.return_value.select.return_value
        chain = chain.eq.return_value.order.return_value.limit.return_value
        chain.execute.return_value = mock_result

        result = repo.get_latest_result("app-1")
        assert result is None

    def test_get_latest_result_returns_data(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [
            {"id": "r1", "application_id": "app-1", "outcome": "VALID"},
        ]
        chain = repo.client.table.return_value.select.return_value
        chain = chain.eq.return_value.order.return_value.limit.return_value
        chain.execute.return_value = mock_result

        result = repo.get_latest_result("app-1")
        assert result is not None
        assert result["id"] == "r1"

    def test_list_findings_for_result(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [
            {"id": "f1", "rule_id": "C01"},
            {"id": "f2", "rule_id": "C02"},
        ]
        chain = repo.client.table.return_value.select.return_value
        chain = chain.eq.return_value
        chain.execute.return_value = mock_result

        findings = repo.list_findings_for_result("r1")
        assert len(findings) == 2


class TestConsistencyAPI:
    def _make_client(self, user: UserContext | None = None) -> TestClient:
        app = FastAPI()
        app.include_router(router)

        if user:
            def override_get_user():
                return user
            app.dependency_overrides[get_current_user] = override_get_user

        return TestClient(app)

    def _make_user(self) -> UserContext:
        return UserContext(
            user_id="00000000-0000-0000-0000-000000000001",
            email="test@test.com",
            role=SystemRole.APPLICANT,
            raw_claims={},
        )

    def test_post_check_returns_200(self):
        user = self._make_user()
        client = self._make_client(user)

        app_id = "00000000-0000-0000-0000-000000000099"
        mock_app = {"id": app_id, "applicant_id": "00000000-0000-0000-0000-000000000001"}

        with patch("app.api.consistency.get_supabase") as mock_sb, \
             patch("app.api.consistency.check_application_consistency") as mock_check, \
             patch("app.api.consistency.check_application_ownership") as mock_own:
            mock_own.return_value = None

            mock_client = MagicMock()
            mock_sb.return_value = mock_client

            # Return different mock chains based on table name
            app_table = MagicMock()
            app_table.select.return_value.eq.return_value.execute.return_value.data = [mock_app]

            empty_table = MagicMock()
            empty_table.select.return_value.eq.return_value.execute.return_value.data = []

            def table_side_effect(name):
                if name == "applications":
                    return app_table
                return empty_table

            mock_client.table.side_effect = table_side_effect

            mock_check.return_value = ConsistencyResult(
                application_id=app_id,
                outcome=ConsistencyOutcome.VALID,
                findings=[],
            )

            response = client.post(f"/applications/{app_id}/consistency/check")
            assert response.status_code == 200

    def test_get_returns_404_when_no_check(self):
        user = self._make_user()
        client = self._make_client(user)

        app_id = "00000000-0000-0000-0000-000000000099"
        mock_app = {"id": app_id, "applicant_id": "00000000-0000-0000-0000-000000000001"}

        with patch("app.api.consistency.get_supabase") as mock_sb, \
             patch("app.api.consistency.check_application_ownership") as mock_own:
            mock_own.return_value = None

            mock_client = MagicMock()
            mock_sb.return_value = mock_client

            # Return different mock chains based on table name
            app_table = MagicMock()
            app_table.select.return_value.eq.return_value.execute.return_value.data = [mock_app]

            empty_table = MagicMock()
            chain = empty_table.select.return_value
            chain = chain.eq.return_value.order.return_value.limit.return_value
            chain.execute.return_value.data = []

            def table_side_effect(name):
                if name == "applications":
                    return app_table
                return empty_table

            mock_client.table.side_effect = table_side_effect

            response = client.get(f"/applications/{app_id}/consistency")
            assert response.status_code == 404
