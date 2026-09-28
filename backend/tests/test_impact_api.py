"""API tests for POST /regulatory/changes/rehearse (staff-only)."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.regulatory import router
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


def _make_user(role=SystemRole.REVIEWER, user_id=USER_ID):
    return UserContext(user_id=user_id, email="staff@t.com", role=role, raw_claims={})


def _make_app(**over):
    app = {
        "id": APP_ID,
        "project_id": PROJECT_ID,
        "applicant_id": USER_ID,
        "status": "draft",
        "approval_id": "00000000-0000-0000-0000-000000000100",
        "approval_code": "A05",
        "reference_number": "APP-IMPACT",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    }
    app.update(over)
    return app


def _rule_change_payload():
    from app.seed.approvals import load_approval_rules

    old = next(r for r in load_approval_rules() if r.id == "R-EIA-001").model_dump()
    new = dict(old)
    new["applicability_conditions"] = [
        {
            "kind": "and",
            "conditions": [
                {
                    "kind": "condition",
                    "field": "industry_type",
                    "op": "eq",
                    "value": "synthetic organic / specialty chemical manufacturing",
                },
                {"kind": "condition", "field": "production_capacity", "op": "gte", "value": 30000},
            ],
        }
    ]
    return {
        "change_kind": "RULE_CHANGE",
        "rule_id": "R-EIA-001",
        "old_value": old,
        "new_value": new,
    }


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


class TestImpactRehearseEndpoint:
    def test_staff_returns_200_with_verdict(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={"application_id": APP_ID, "change": _rule_change_payload()},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["application_id"] == APP_ID
        assert data["classification"] == "RESULT_CHANGED"
        assert "A05" in [d["approval_id"] for d in data["diffs"]]
        assert data["new_results"]["A05"]["applicability"] == "does_not_apply"
        assert "baseline_results" in data and "evidence_caveats" in data

    def test_applicant_forbidden(self):
        client, _ = _build_client(
            _make_app(), _make_user(role=SystemRole.APPLICANT), dict(_DAHEJ_FACTS)
        )
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={"application_id": APP_ID, "change": _rule_change_payload()},
        )
        assert resp.status_code == 403

    def test_requires_auth(self):
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={"application_id": APP_ID, "change": _rule_change_payload()},
        )
        assert resp.status_code in (401, 403)

    def test_malformed_change_422(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {"change_kind": "RULE_CHANGE", "rule_id": "R-EIA-001"},
            },
        )
        assert resp.status_code == 422

    def test_unknown_rule_422(self):
        client, _ = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        payload = _rule_change_payload()
        payload["rule_id"] = "R-NOPE-000"
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={"application_id": APP_ID, "change": payload},
        )
        assert resp.status_code == 422

    def test_404_for_missing_application(self):
        client, repos = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        repos["app"].get_by_id.return_value = None
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={"application_id": APP_ID, "change": _rule_change_payload()},
        )
        assert resp.status_code == 404

    def test_never_writes_database(self):
        client, repos = _build_client(_make_app(), _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={"application_id": APP_ID, "change": _rule_change_payload()},
        )
        assert resp.status_code == 200
        for repo in repos.values():
            for method in ("upsert", "update", "create", "delete", "insert"):
                mock = getattr(repo, method, None)
                if mock is not None and isinstance(mock, MagicMock):
                    mock.assert_not_called()

    def test_staff_bypass_ownership(self):
        other_app = _make_app(applicant_id=str(uuid4()))
        client, _ = _build_client(other_app, _make_user(), dict(_DAHEJ_FACTS))
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={"application_id": APP_ID, "change": _rule_change_payload()},
        )
        # REVIEWER bypasses ownership per check_application_ownership.
        assert resp.status_code == 200
