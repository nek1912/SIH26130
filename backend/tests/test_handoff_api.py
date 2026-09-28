"""API tests for manual government handoff routes."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.handoffs import router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.handoffs import HandoffsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.workflow_events import WorkflowEventsRepository

APP_ID = "00000000-0000-0000-0000-000000000099"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"
USER_ID = "00000000-0000-0000-0000-000000000001"

_BASE_JSON = {
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
}

_DAHEJ_FACTS = {
    "id": "facts-1",
    "project_id": PROJECT_ID,
    "entity_type": "pvt-ltd",
    "sector": "chemical",
    "jurisdictions": ["IN-GJ"],
    "headcount": 60,
    "annual_turnover_inr": 0,
    "facts_json": dict(_BASE_JSON),
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
        "approval_code": "A05",
        "reference_number": "APP-HANDOFF",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    }
    app.update(over)
    return app


class _HandoffStore:
    """In-memory HandoffsRepository double backed by a dict."""

    def __init__(self):
        self.rows: dict[str, dict] = {}
        self.mock = MagicMock(spec=HandoffsRepository)
        self.mock.list_for_application.side_effect = (
            lambda app_id: [r for r in self.rows.values() if r["application_id"] == str(app_id)]
        )
        self.mock.get_active_for_approval.side_effect = self._active
        self.mock.get_by_id.side_effect = lambda hid: self.rows.get(str(hid))
        self.mock.create.side_effect = self._create
        self.mock.update.side_effect = self._update

    def _active(self, app_id, code):
        from app.handoff.models import ACTIVE_STATUSES

        active = {s.value for s in ACTIVE_STATUSES}
        for row in self.rows.values():
            if (
                row["application_id"] == str(app_id)
                and row["approval_code"] == code
                and row["status"] in active
            ):
                return row
        return None

    def _create(self, data):
        import uuid as _uuid

        row = dict(data)
        row.setdefault("id", str(_uuid.uuid4()))
        self.rows[row["id"]] = row
        return row

    def _update(self, hid, data):
        row = self.rows.get(str(hid))
        if not row:
            return None
        row.update(data)
        return row


def _build_client(app_dict, user, facts_record=None, store=None, events=None):
    from fastapi import FastAPI as _FastAPI

    app = _FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: user

    from app.api.deps import (
        get_applications_repository,
        get_consistency_repository,
        get_documents_repository,
        get_handoffs_repository,
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
    created_events: list[dict] = []
    events_repo.create.side_effect = lambda data: created_events.append(data) or data

    consistency_repo = MagicMock(spec=ConsistencyRepository)
    consistency_repo.get_latest_result.return_value = None

    store = store or _HandoffStore()

    app.dependency_overrides[get_applications_repository] = lambda: app_repo
    app.dependency_overrides[get_project_facts_repository] = lambda: facts_repo
    app.dependency_overrides[get_documents_repository] = lambda: docs_repo
    app.dependency_overrides[get_workflow_events_repository] = lambda: events_repo
    app.dependency_overrides[get_consistency_repository] = lambda: consistency_repo
    app.dependency_overrides[get_handoffs_repository] = lambda: store.mock
    return TestClient(app), {
        "app": app_repo,
        "facts": facts_repo,
        "events": events_repo,
        "created_events": created_events,
        "store": store,
    }


def _facts_with(patch: dict) -> dict:
    facts = {k: v for k, v in _DAHEJ_FACTS.items()}
    merged_json = dict(_BASE_JSON)
    merged_json.update(patch)
    facts["facts_json"] = merged_json
    return facts


class TestInitiate:
    def test_ready_approval_can_initiate(self):
        client, ctx = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "handed_off"
        assert data["approval_code"] == "A05"
        assert "parivesh.nic.in" in data["portal_url"]
        assert data["external_reference"] is None
        assert data["verification"] == "user_reported"
        # Workflow event created.
        assert any(
            e.get("action") == "handoff.initiate" for e in ctx["created_events"]
        )

    def test_not_applicable_cannot_initiate(self):
        client, _ = _build_client(
            _make_app(approval_code="A18"), _make_user(), dict(_DAHEJ_FACTS)
        )
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A18"}
        )
        assert resp.status_code == 409

    def test_insufficient_data_cannot_initiate(self):
        facts = _facts_with({})
        facts["facts_json"] = {}
        facts["entity_type"] = "pvt-ltd"
        client, _ = _build_client(_make_app(), _make_user(), facts)
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        assert resp.status_code == 409

    def test_blocked_by_documents_cannot_initiate(self):
        client, _ = _build_client(
            _make_app(approval_code="A04"), _make_user(), dict(_DAHEJ_FACTS)
        )
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A04"}
        )
        assert resp.status_code == 409

    def test_blocked_by_dependency_cannot_initiate(self):
        client, _ = _build_client(
            _make_app(approval_code="A03"), _make_user(), dict(_DAHEJ_FACTS)
        )
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A03"}
        )
        assert resp.status_code == 409

    def test_duplicate_active_handoff_409(self):
        store = _HandoffStore()
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS), store)
        first = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        assert first.status_code == 200
        second = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        assert second.status_code == 409

    def test_unknown_approval_code_422(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A99"}
        )
        assert resp.status_code in (404, 422)


class TestSubmissionAndStatus:
    def _initiated(self):
        store = _HandoffStore()
        client, ctx = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS), store)
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        assert resp.status_code == 200
        return client, ctx, resp.json()["id"]

    def test_submission_records_reference(self):
        client, ctx, hid = self._initiated()
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/record-submission",
            json={"external_reference": "PARIVESH/2026/1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "submitted_externally"
        assert data["external_reference"] == "PARIVESH/2026/1"
        assert data["submitted_at"] is not None
        assert any(
            e.get("action") == "handoff.record_submission" for e in ctx["created_events"]
        )

    def test_invalid_transition_409(self):
        client, _, hid = self._initiated()
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/report-status",
            json={"to_status": "under_external_review"},
        )
        assert resp.status_code == 409

    def test_user_reported_approval_not_authoritative(self):
        client, _, hid = self._initiated()
        client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/record-submission",
            json={"external_reference": "REF-1"},
        )
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/report-status",
            json={"to_status": "approved_external"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved_external"
        assert data["verification"] == "user_reported"
        assert data["verified_by"] is None

    def test_get_handoffs_does_not_write(self):
        store = _HandoffStore()
        client, ctx = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS), store)
        resp = client.get(f"/applications/{APP_ID}/handoffs")
        assert resp.status_code == 200
        assert resp.json()["handoffs"] == []
        store.mock.create.assert_not_called()

    def test_application_status_unchanged(self):
        client, ctx, hid = self._initiated()
        client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/record-submission",
            json={"external_reference": "REF-1"},
        )
        ctx["app"].update.assert_not_called()

    def test_handoff_belongs_to_url_application(self):
        other_id = "00000000-0000-0000-0000-000000000077"
        store = _HandoffStore()
        store.rows[other_id] = {
            "id": other_id,
            "application_id": "00000000-0000-0000-0000-000000000078",
            "approval_code": "A05",
            "status": "handed_off",
        }
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS), store)
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/{other_id}/record-submission",
            json={"external_reference": "REF-X"},
        )
        assert resp.status_code == 404


class TestAuth:
    def test_unauthenticated_401(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        assert resp.status_code in (401, 403)

    def test_other_applicant_403(self):
        other = _make_app(applicant_id=str(uuid4()))
        client, _ = _build_client(other, _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        assert resp.status_code == 403

    def test_applicant_cannot_verify(self):
        store = _HandoffStore()
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS), store)
        init = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        hid = init.json()["id"]
        resp = client.post(f"/applications/{APP_ID}/handoffs/{hid}/verify",
                           json={"verified_status": "approved_external"})
        assert resp.status_code == 403

    def test_spoof_verified_by_422(self):
        store = _HandoffStore()
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS), store)
        init = client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        hid = init.json()["id"]
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/record-submission",
            json={"external_reference": "REF-1", "verified_by": "user-1"},
        )
        assert resp.status_code == 422

    def test_staff_can_verify(self):
        from app.auth.models import SystemRole as R

        store = _HandoffStore()
        applicant_client, _ = _build_client(
            _make_app(), _make_user(), dict(_DAHEJ_FACTS), store
        )
        init = applicant_client.post(
            f"/applications/{APP_ID}/handoffs/initiate", json={"approval_code": "A05"}
        )
        hid = init.json()["id"]
        applicant_client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/record-submission",
            json={"external_reference": "REF-1"},
        )
        staff_client, _ = _build_client(
            _make_app(), _make_user(role=R.ADMIN), dict(_DAHEJ_FACTS), store
        )
        resp = staff_client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/verify",
            json={"verified_status": "approved_external"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["verification"] == "staff_verified"
        assert data["verified_by"] is not None
