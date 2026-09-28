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
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository


class TestConsistencyRepository:
    def _make_repo(self) -> ConsistencyRepository:
        mock_client = MagicMock()
        return ConsistencyRepository(mock_client)

    def test_create_result_calls_insert(self):
        repo = self._make_repo()
        repo.client.insert_one.return_value = {
            "id": "result-1",
            "application_id": "app-1",
        }

        result = repo.create_result("app-1", "VALID", "2026-09-15T10:00:00", "1")
        assert result["id"] == "result-1"
        assert repo.client.insert_one.call_args[0][0] == "consistency_results"

    def test_create_findings_calls_insert(self):
        repo = self._make_repo()
        repo.client.insert_many.return_value = [{"id": "finding-1"}]

        findings_data = [{"result_id": "r1", "rule_id": "C01", "canonical_field": "plot_area_sqm"}]
        result = repo.create_findings(findings_data)
        assert len(result) == 1
        assert repo.client.insert_many.call_args[0][0] == "consistency_findings"

    def test_get_latest_result_returns_none_when_empty(self):
        repo = self._make_repo()
        repo.client.fetch_one.return_value = None

        result = repo.get_latest_result("app-1")
        assert result is None

    def test_get_latest_result_returns_data(self):
        repo = self._make_repo()
        repo.client.fetch_one.return_value = {
            "id": "r1",
            "application_id": "app-1",
            "outcome": "VALID",
        }

        result = repo.get_latest_result("app-1")
        assert result is not None
        assert result["id"] == "r1"

    def test_list_findings_for_result(self):
        repo = self._make_repo()
        repo.client.fetch_all.return_value = [
            {"id": "f1", "rule_id": "C01"},
            {"id": "f2", "rule_id": "C02"},
        ]

        findings = repo.list_findings_for_result("r1")
        assert len(findings) == 2


class TestConsistencyAPI:
    def _make_client(
        self,
        user: UserContext | None = None,
        app_repo: ApplicationsRepository | None = None,
        consistency_repo: ConsistencyRepository | None = None,
    ) -> TestClient:
        app = FastAPI()
        app.include_router(router)

        if user:
            def override_get_user():
                return user
            app.dependency_overrides[get_current_user] = override_get_user

        if app_repo:
            from app.api.deps import get_applications_repository
            app.dependency_overrides[get_applications_repository] = lambda: app_repo

        if consistency_repo:
            from app.api.deps import get_consistency_repository
            app.dependency_overrides[get_consistency_repository] = lambda: consistency_repo

        return TestClient(app)

    def _make_user(self) -> UserContext:
        return UserContext(
            user_id="00000000-0000-0000-0000-000000000001",
            email="test@test.com",
            role=SystemRole.APPLICANT,
            raw_claims={},
        )

    def _make_app_repo(self, mock_app: dict) -> ApplicationsRepository:
        mock_client = MagicMock()
        repo = ApplicationsRepository(mock_client)
        repo.get_by_id = MagicMock(return_value=mock_app)
        return repo

    def _make_consistency_repo(self) -> tuple[ConsistencyRepository, MagicMock]:
        mock_client = MagicMock()
        repo = ConsistencyRepository(mock_client)
        return repo, mock_client

    def test_post_check_returns_200(self):
        user = self._make_user()
        app_id = "00000000-0000-0000-0000-000000000099"
        mock_app = {
            "id": app_id,
            "applicant_id": "00000000-0000-0000-0000-000000000001",
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        }

        app_repo = self._make_app_repo(mock_app)
        cons_repo, mock_client = self._make_consistency_repo()

        # Mock extracted fields and doc map
        cons_repo.get_extracted_fields_for_application = MagicMock(return_value=[])
        cons_repo.get_document_req_map = MagicMock(return_value={})
        cons_repo.delete_previous_results = MagicMock()
        cons_repo.create_result = MagicMock(return_value={"id": "result-1"})
        cons_repo.create_findings = MagicMock(return_value=[])

        client = self._make_client(user, app_repo, cons_repo)

        with patch("app.api.consistency.check_application_consistency") as mock_check:
            mock_check.return_value = ConsistencyResult(
                application_id=app_id,
                outcome=ConsistencyOutcome.VALID,
                findings=[],
            )

            response = client.post(f"/applications/{app_id}/consistency/check")
            assert response.status_code == 200

    def test_get_returns_404_when_no_check(self):
        user = self._make_user()
        app_id = "00000000-0000-0000-0000-000000000099"
        mock_app = {"id": app_id, "applicant_id": "00000000-0000-0000-0000-000000000001"}

        app_repo = self._make_app_repo(mock_app)
        cons_repo, _ = self._make_consistency_repo()
        cons_repo.get_latest_result = MagicMock(return_value=None)

        client = self._make_client(user, app_repo, cons_repo)

        response = client.get(f"/applications/{app_id}/consistency")
        assert response.status_code == 404
