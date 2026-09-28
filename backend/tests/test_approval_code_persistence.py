"""Approval-code persistence contract.

Proves the real persisted relationship: POST /applications stores the
workbook approval code it already requires, and the orchestration endpoint
resolves scope from a row shaped exactly like created output (UUID
approval_id alongside the code) — no second mapping, no duplication.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import applications as applications_api
from app.api.orchestration import router as orchestration_router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.workflow_events import WorkflowEventsRepository

USER_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"
APP_ID = "00000000-0000-0000-0000-000000000099"
APPROVAL_UUID = "00000000-0000-0000-0000-000000000100"


def _make_user() -> UserContext:
    return UserContext(
        user_id=USER_ID,
        email="test@test.com",
        role=SystemRole.APPLICANT,
        raw_claims={},
    )


def _gj_project():
    return {
        "id": PROJECT_ID,
        "name": "GJ project",
        "applicant_id": USER_ID,
        "status": "active",
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    }


def _build_create_client(app_repo, docs_repo, project) -> TestClient:
    app = FastAPI()
    app.include_router(applications_api.router)

    def override_get_user():
        return _make_user()

    app.dependency_overrides[get_current_user] = override_get_user

    from app.api.deps import (
        get_applications_repository,
        get_documents_repository,
        get_project_repository,
    )

    project_repo = MagicMock(spec=ProjectRepository)
    project_repo.get_by_id.return_value = project

    app.dependency_overrides[get_applications_repository] = lambda: app_repo
    app.dependency_overrides[get_documents_repository] = lambda: docs_repo
    app.dependency_overrides[get_project_repository] = lambda: project_repo
    return TestClient(app)


def _build_orchestration_client(app_repo) -> TestClient:
    app = FastAPI()
    app.include_router(orchestration_router)

    def override_get_user():
        return _make_user()

    app.dependency_overrides[get_current_user] = override_get_user

    from app.api.deps import (
        get_applications_repository,
        get_consistency_repository,
        get_documents_repository,
        get_project_facts_repository,
        get_workflow_events_repository,
    )

    empty_docs = MagicMock(spec=DocumentsRepository)
    empty_docs.list_documents_for_application.return_value = []
    empty_facts = MagicMock(spec=ProjectFactsRepository)
    empty_facts.get_by_project.return_value = None
    empty_events = MagicMock(spec=WorkflowEventsRepository)
    empty_events.list_for_application.return_value = []
    empty_consistency = MagicMock(spec=ConsistencyRepository)
    empty_consistency.get_latest_result.return_value = None

    app.dependency_overrides[get_applications_repository] = lambda: app_repo
    app.dependency_overrides[get_documents_repository] = lambda: empty_docs
    app.dependency_overrides[get_project_facts_repository] = lambda: empty_facts
    app.dependency_overrides[get_workflow_events_repository] = lambda: empty_events
    app.dependency_overrides[get_consistency_repository] = lambda: empty_consistency
    return TestClient(app)


class TestApprovalCodePersistence:
    def test_create_application_persists_approval_code(self):
        """POST /applications stores approval_code and seeds A03 documents."""
        captured: dict = {}
        created = {
            "id": APP_ID,
            "project_id": PROJECT_ID,
            "approval_id": APPROVAL_UUID,
            "approval_code": "A03",
            "status": "draft",
            "applicant_id": USER_ID,
            "reference_number": "APP-TEST001",
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        }

        def fake_create(data):
            captured.update(data)
            return created

        app_repo = MagicMock(spec=ApplicationsRepository)
        app_repo.create_with_reference.side_effect = fake_create
        docs_repo = MagicMock(spec=DocumentsRepository)
        docs_repo.create_requirements_bulk.return_value = 3

        client = _build_create_client(app_repo, docs_repo, _gj_project())
        response = client.post(
            f"/applications?project_id={PROJECT_ID}"
            f"&approval_id={APPROVAL_UUID}&approval_code=A03"
        )
        assert response.status_code == 200, response.text
        assert captured["approval_code"] == "A03"
        assert captured["approval_id"] == APPROVAL_UUID
        assert captured["jurisdiction"] == "IN-GJ"
        assert captured["pack_version"] == "gj-legacy-unversioned"
        # Document seeding still fires for the code's requirements.
        assert docs_repo.create_requirements_bulk.called
        seeded = docs_repo.create_requirements_bulk.call_args[0][0]
        assert len(seeded) > 0
        assert {r["approval_id"] for r in seeded} == {"A03"}

    def test_orchestration_scopes_from_persisted_shape_row(self):
        """A row shaped like create output (UUID + code) scopes correctly."""
        persisted_shape = {
            "id": APP_ID,
            "project_id": PROJECT_ID,
            "approval_id": APPROVAL_UUID,
            "approval_code": "A03",
            "status": "draft",
            "applicant_id": USER_ID,
            "reference_number": "APP-TEST001",
            "current_stage": None,
            "submitted_at": None,
            "created_at": "2026-09-15T10:00:00Z",
            "jurisdiction": "IN-GJ",
            "pack_version": "gj-legacy-unversioned",
        }
        app_repo = MagicMock(spec=ApplicationsRepository)
        app_repo.get_by_id.return_value = persisted_shape
        app_repo.get_by_project.return_value = [persisted_shape]
        app_repo.get_approval_stages.return_value = []

        client = _build_orchestration_client(app_repo)
        response = client.get(f"/applications/{APP_ID}/orchestration")
        assert response.status_code == 200, response.text
        assessed = set(response.json()["approvals"].keys())
        assert assessed == {"A02", "A03", "A04"}
