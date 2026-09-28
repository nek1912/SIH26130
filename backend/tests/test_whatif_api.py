"""API tests for POST /applications/{id}/orchestration/what-if."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.orchestration import router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.workflow_events import WorkflowEventsRepository

APP_ID = "00000000-0000-0000-0000-000000000099"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"
USER_ID = "00000000-0000-0000-0000-000000000001"

_DAHEJ_FACTS = {
    "id": "facts-1",
    "project_id": PROJECT_ID,
    "entity_type": "pvt-ltd",
    "sector": "chemical",
    "jurisdictions": ["IN-GJ"],
    "headcount": 60,
    "annual_turnover_inr": 0,
    "facts_json": {
        "state": "Gujarat",
        "industry_type": "synthetic organic / specialty chemical manufacturing",
        "plot_area_sqm": 12000,
        "effluent_generation": 70,
        "ETP_capacity": 80,
        "hazardous_process": True,
        "building_height": 18,
        "workers_total": 60,
        "new_project": True,
        "power_demand": 1000,
        "hazardous_waste_generated": True,
        "hazardous_chemicals_handled": True,
        "production_capacity": 20000,
        "lift_present": True,
        "boiler_present": True,
        "groundwater_use": False,
    },
    "created_at": "2026-09-15T10:00:00Z",
    "updated_at": "2026-09-15T10:00:00Z",
}


def _make_user(role=SystemRole.APPLICANT, user_id=USER_ID):
    return UserContext(user_id=user_id, email="t@t.com", role=role, raw_claims={})


def _make_app(**over):
    app = {
        "id": APP_ID,
        "project_id": PROJECT_ID,
        "applicant_id": USER_ID,
        "status": "draft",
        "approval_id": "00000000-0000-0000-0000-000000000100",
        "approval_code": "A04",
        "reference_number": "APP-WHATIF",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    }
    app.update(over)
    return app


def _build_client(app_dict, user, facts_record=None):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: user

    from app.api.deps import (
        get_applications_repository,
        get_consistency_repository,
        get_documents_repository,
        get_project_facts_repository,
        get_workflow_events_repository,
    )

    app_repo = MagicMock(spec=ApplicationsRepository)
    app_repo.get_by_id.return_value = app_dict
    app_repo.get_by_project.return_value = [app_dict]
    app_repo.get_approval_stages.return_value = []

    facts_repo = MagicMock(spec=ProjectFactsRepository)
    facts_repo.get_by_project.return_value = facts_record

    docs_repo = MagicMock(spec=DocumentsRepository)
    docs_repo.list_documents_for_application.return_value = []
    docs_repo.get_extraction_result_for_document.return_value = None
    docs_repo.get_validation_result_for_document.return_value = None

    events_repo = MagicMock(spec=WorkflowEventsRepository)
    events_repo.list_for_application.return_value = []

    consistency_repo = MagicMock(spec=ConsistencyRepository)
    consistency_repo.get_latest_result.return_value = None

    app.dependency_overrides[get_applications_repository] = lambda: app_repo
    app.dependency_overrides[get_project_facts_repository] = lambda: facts_repo
    app.dependency_overrides[get_documents_repository] = lambda: docs_repo
    app.dependency_overrides[get_workflow_events_repository] = lambda: events_repo
    app.dependency_overrides[get_consistency_repository] = lambda: consistency_repo
    return TestClient(app), {"app": app_repo, "facts": facts_repo}


class TestWhatIfEndpoint:
    def test_returns_200_with_diff(self):
        client, _ = _build_client(
            _make_app(approval_code="A05"), _make_user(), dict(_DAHEJ_FACTS)
        )
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"production_capacity": 10000}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["application_id"] == APP_ID
        assert data["applied_overrides"] == {"production_capacity": 10000}
        assert "baseline" in data and "what_if" in data and "diff" in data
        changed = {c["approval_id"] for c in data["diff"]["changed_approvals"]}
        assert "A05" in changed
        assert data["diff"]["no_change"] is False

    def test_no_change_scenario(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"village": "Dahej"}},
        )
        assert resp.status_code == 200
        assert resp.json()["diff"]["no_change"] is True

    def test_never_writes_persisted_facts(self):
        client, repos = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"production_capacity": 10000}},
        )
        assert resp.status_code == 200
        facts_repo = repos["facts"]
        assert not hasattr(facts_repo, "upsert") or True
        # Spec'd write methods must never be invoked.
        for method in ("upsert", "update", "create", "delete"):
            mock = getattr(facts_repo, method, None)
            if mock is not None and isinstance(mock, MagicMock):
                mock.assert_not_called()

    def test_unknown_field_422(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"is_admin": True}},
        )
        assert resp.status_code == 422

    def test_invalid_type_422(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"power_demand": "lots"}},
        )
        assert resp.status_code == 422

    def test_none_override_accepted(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"power_demand": None}},
        )
        assert resp.status_code == 200

    def test_groundwater_true_fails_closed(self):
        client, _ = _build_client(
            _make_app(approval_code="A18"), _make_user(), dict(_DAHEJ_FACTS)
        )
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"groundwater_use": True}},
        )
        assert resp.status_code == 200
        data = resp.json()
        a18 = data["what_if"]["approvals"]["A18"]
        assert a18["applicability_result"] == "applies"
        assert a18["status"] == "insufficient_data"

    def test_requires_auth(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {}},
        )
        assert resp.status_code in (401, 403)

    def test_ownership_enforced(self):
        other_app = _make_app(applicant_id=str(uuid4()))
        client, _ = _build_client(other_app, _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {}},
        )
        assert resp.status_code == 403

    def test_staff_can_access(self):
        from app.auth.models import SystemRole as R

        client, _ = _build_client(
            _make_app(), _make_user(role=R.ADMIN), dict(_DAHEJ_FACTS)
        )
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {}},
        )
        assert resp.status_code == 200

    def test_404_for_missing_application(self):
        app = FastAPI()
        app.include_router(router)
        user = _make_user(role=SystemRole.ADMIN)
        app.dependency_overrides[get_current_user] = lambda: user

        from app.api.deps import (
            get_applications_repository,
            get_consistency_repository,
            get_documents_repository,
            get_project_facts_repository,
            get_workflow_events_repository,
        )

        app_repo = MagicMock(spec=ApplicationsRepository)
        app_repo.get_by_id.return_value = None
        app.dependency_overrides[get_applications_repository] = lambda: app_repo
        app.dependency_overrides[get_project_facts_repository] = lambda: MagicMock(
            spec=ProjectFactsRepository
        )
        app.dependency_overrides[get_documents_repository] = lambda: MagicMock(
            spec=DocumentsRepository
        )
        app.dependency_overrides[get_workflow_events_repository] = lambda: MagicMock(
            spec=WorkflowEventsRepository
        )
        app.dependency_overrides[get_consistency_repository] = lambda: MagicMock(
            spec=ConsistencyRepository
        )
        client = TestClient(app)
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {}},
        )
        assert resp.status_code == 404
