"""MH end-to-end FastAPI verification (Phase 7).

IN-MH is selectable ONLY via ``dependency_overrides`` on
``get_active_jurisdiction`` (test-only; per-app instances, no global
state, production default untouched). The regulatory decision path
is real in every test: real packs, real engines, mocked persistence.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.applications import router as applications_router
from app.api.deps import (
    get_active_jurisdiction,
    get_applications_repository,
    get_consistency_repository,
    get_documents_repository,
    get_handoffs_repository,
    get_project_facts_repository,
    get_workflow_events_repository,
)
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.handoffs import HandoffsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, IN_MH

APP_ID = "00000000-0000-0000-0000-000000000099"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"
USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_ID = "00000000-0000-0000-0000-000000000002"

GJ_RULE_IDS = {
    "R-GIDC-001", "R-GIDC-003", "R-GIDC-005", "R-IFP-001",
    "R-EIA-001", "R-FIRE-001", "R-FIRE-004", "R-LAB-001",
    "R-BOCW-001", "R-GERC-002", "R-CEA-001", "R-HW-001",
    "R-MSIHC-001", "R-CA-001", "R-BU-001", "R-LIFT-001",
    "R-BOILER-001", "R-PESO-001", "R-CGWA-001",
}
GJ_IDS = (
    {f"A{i:02d}" for i in range(1, 19)}
    | {f"D{i:02d}" for i in range(1, 18)}
    | {f"S{i:02d}" for i in list(range(1, 32)) + [33]}
    | GJ_RULE_IDS
    | {"GIDC", "ShramSetu", "GPCB", "CEICED", "BOCW", "Dahej", "G0R5",
       "IFP"}
)
MH_RULE_IDS = {
    "R-002", "R-007", "R-009", "R-011", "R-012", "R-018", "R-026",
    "R-028", "R-030", "R-035", "R-043", "R-044", "R-046", "R-056",
    "R-067", "R-070", "R-089", "R-093", "R-094",
}


def _strings(payload):
    found = set()

    def walk(value):
        if isinstance(value, str):
            found.add(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return found


def _make_user(role=SystemRole.APPLICANT, user_id=USER_ID):
    return UserContext(
        user_id=user_id, email="t@t.com", role=role, raw_claims={}
    )


def _mh_facts_record(facts_json):
    return {
        "id": "facts-mh",
        "project_id": PROJECT_ID,
        "entity_type": "pvt-ltd",
        "sector": "chemical",
        "jurisdictions": ["IN-MH"],
        "headcount": 0,
        "annual_turnover_inr": 0,
        "facts_json": dict(facts_json),
        "created_at": "2026-09-15T10:00:00Z",
        "updated_at": "2026-09-15T10:00:00Z",
    }


def _make_app(approval_code, **over):
    app = {
        "id": APP_ID,
        "project_id": PROJECT_ID,
        "applicant_id": USER_ID,
        "status": "draft",
        "approval_id": "00000000-0000-0000-0000-000000000100",
        "approval_code": approval_code,
        "reference_number": "APP-MH-E2E",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        "jurisdiction": "IN-MH",
        "pack_version": "mh-v5-batch1",
    }
    app.update(over)
    return app


def _repos(app_dict, facts_record, handoff_store=None):
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
    store = None
    if handoff_store is not None:
        store = MagicMock(spec=HandoffsRepository)
        store.list_for_application.side_effect = handoff_store["list"]
        store.get_active_for_approval.side_effect = handoff_store["active"]
        store.get_by_id.side_effect = handoff_store["get"]
        store.create.side_effect = handoff_store["create"]
        store.update.side_effect = handoff_store["update"]
    return {
        "app_repo": app_repo,
        "facts_repo": facts_repo,
        "docs_repo": docs_repo,
        "events_repo": events_repo,
        "consistency_repo": consistency_repo,
        "store": store,
    }


def _client(router, repos, user):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_applications_repository] = (
        lambda: repos["app_repo"]
    )
    app.dependency_overrides[get_project_facts_repository] = (
        lambda: repos["facts_repo"]
    )
    app.dependency_overrides[get_documents_repository] = (
        lambda: repos["docs_repo"]
    )
    app.dependency_overrides[get_workflow_events_repository] = (
        lambda: repos["events_repo"]
    )
    app.dependency_overrides[get_consistency_repository] = (
        lambda: repos["consistency_repo"]
    )
    if repos["store"] is not None:
        app.dependency_overrides[get_handoffs_repository] = (
            lambda: repos["store"]
        )
    # NOTE: no get_active_jurisdiction override. Persisted application
    # identity selects the pack; request-scoped overrides must not.
    return TestClient(app), repos


def _handoff_store():
    rows: dict[str, dict] = {}

    def _active(app_id, code):
        from app.handoff.models import ACTIVE_STATUSES

        active = {s.value for s in ACTIVE_STATUSES}
        return next(
            (
                r for r in rows.values()
                if r["application_id"] == str(app_id)
                and r["approval_code"] == code
                and r["status"] in active
            ),
            None,
        )

    def _create(data):
        row = dict(data)
        row.setdefault("id", str(uuid4()))
        rows[row["id"]] = row
        return row

    def _update(hid, data):
        row = rows.get(str(hid))
        if not row:
            return None
        row.update(data)
        return row

    return {
        "list": lambda app_id: [
            r for r in rows.values() if r["application_id"] == str(app_id)
        ],
        "active": _active,
        "get": lambda hid: rows.get(str(hid)),
        "create": _create,
        "update": _update,
        "rows": rows,
    }


class TestDefaultRegression:
    def test_default_jurisdiction_is_gj(self):
        from app.api.deps import get_active_jurisdiction as resolve

        assert DEFAULT_JURISDICTION == IN_GJ
        assert resolve() == IN_GJ

    def test_gj_baseline_orchestration_unchanged(self):
        from app.api.orchestration import router

        facts = {
            "industry_type": (
                "synthetic organic / specialty chemical manufacturing"
            ),
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
        app_dict = _make_app(
            "A04",
            reference_number="APP-GJ-BASE",
            jurisdiction="IN-GJ",
            pack_version="gj-legacy-unversioned",
        )
        repos = _repos(app_dict, _mh_facts_record(facts))
        repos["facts_repo"].get_by_project.return_value = {
            **_mh_facts_record({}),
            "jurisdictions": ["IN-GJ"],
            "facts_json": dict(facts),
        }
        client, _ = _client(router, repos, _make_user())
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 200
        body = resp.json()
        assert body["approvals"]["A04"]["applicability_result"] == "applies"
        assert _strings(body).isdisjoint(MH_RULE_IDS)
        assert "APR-001" not in _strings(body)


class TestMHOrchestrationAPI:
    def _mh_client(self, facts_json, approval_code, role=SystemRole.APPLICANT):
        from app.api.orchestration import router

        repos = _repos(
            _make_app(approval_code), _mh_facts_record(facts_json)
        )
        return _client(router, repos, _make_user(role))

    def test_a_apr006_ready(self):
        client, _ = self._mh_client(
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]}, "APR-006"
        )
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 200
        body = resp.json()
        orch = body["approvals"]["APR-006"]
        assert orch["applicability_result"] == "applies"
        assert orch["status"] == "ready"
        assert orch["blockers"] == []
        assert _strings(body).isdisjoint(GJ_IDS)

    def test_b_apr010_dependency_blocked(self):
        client, _ = self._mh_client({"F-HW-01": True}, "APR-010")
        body = client.get(
            f"/applications/{APP_ID}/orchestration"
        ).json()
        orch = body["approvals"]["APR-010"]
        assert orch["applicability_result"] == "applies"
        assert orch["status"] == "blocked_by_dependency"

    def test_c_apr026_evidence_fail_closed(self):
        client, _ = self._mh_client(
            {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 900},
            "APR-026",
        )
        orch = client.get(
            f"/applications/{APP_ID}/orchestration"
        ).json()["approvals"]["APR-026"]
        # STOP verdict (audit_mh_r030_exemption_migration): R-030 stays
        # TRIGGER with APR-026 uncomposed, so petroleum Class-B facts
        # evaluate to APPLIES; DOC-008 required and unuploaded, so the
        # approval is BLOCKED_BY_DOCUMENTS (document-blocked contract).
        assert orch["applicability_result"] == "applies"
        assert orch["status"] == "blocked_by_documents"

    def test_d_apr001_evidence_fail_closed(self):
        client, _ = self._mh_client(
            {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False},
            "APR-001",
        )
        orch = client.get(
            f"/applications/{APP_ID}/orchestration"
        ).json()["approvals"]["APR-001"]
        # P0 exception-role migration (deliberate re-pin): R-002 is now
        # CLASSIFICATION, so small-unit facts alone compose to
        # INSUFFICIENT_DATA (never APPLIES) even before the UR-06
        # evidence overlay below.
        assert orch["applicability_result"] == "insufficient_data"
        assert orch["status"] == "insufficient_data"
        assert any(
            b.get("evidence_id") == "UR-06" for b in orch["blockers"]
        )

    def test_e_apr003_does_not_apply(self):
        client, _ = self._mh_client({"F-BLD-01": 1000}, "APR-003")
        orch = client.get(
            f"/applications/{APP_ID}/orchestration"
        ).json()["approvals"]["APR-003"]
        assert orch["applicability_result"] == "does_not_apply"
        assert orch["status"] == "not_applicable"
        assert orch["blockers"] == []

    def test_f_empty_facts_insufficient(self):
        client, _ = self._mh_client({}, "APR-010")
        orch = client.get(
            f"/applications/{APP_ID}/orchestration"
        ).json()["approvals"]["APR-010"]
        assert orch["applicability_result"] == "insufficient_data"

    def test_404_unknown_application(self):
        from app.api.orchestration import router

        repos = _repos(None, None)
        repos["app_repo"].get_by_id.return_value = None
        client, _ = _client(router, repos, _make_user())
        resp = client.get(
            f"/applications/{uuid4()}/orchestration"
        )
        assert resp.status_code == 404

    def test_401_unauthenticated(self):
        from app.api.orchestration import router as orch_router

        bare = FastAPI()
        bare.include_router(orch_router)
        resp = TestClient(bare).get(
            f"/applications/{APP_ID}/orchestration"
        )
        assert resp.status_code == 401


class TestMHWhatIfAPI:
    def _mh_client(self, facts_json):
        from app.api.orchestration import router

        repos = _repos(
            _make_app("APR-003"), _mh_facts_record(facts_json)
        )
        return _client(router, repos, _make_user())

    def test_valid_override_changes_decision(self):
        client, repos = self._mh_client({"F-BLD-01": 30000})
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"F-BLD-01": 1000}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["baseline"]["approvals"]["APR-003"][
            "applicability_result"
        ] == "applies"
        assert body["what_if"]["approvals"]["APR-003"][
            "applicability_result"
        ] == "does_not_apply"
        assert body["diff"]["no_change"] is False
        assert _strings(body).isdisjoint(GJ_IDS)

    def test_unknown_field_422(self):
        client, _ = self._mh_client({"F-BLD-01": 30000})
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"industry_type": "textiles"}},
        )
        assert resp.status_code == 422

    def test_wrong_type_422(self):
        client, _ = self._mh_client({"F-BLD-01": 30000})
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"F-BLD-01": "big"}},
        )
        assert resp.status_code == 422

    def test_invalid_enum_422(self):
        client, _ = self._mh_client({"F-BLD-01": 30000})
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"F-PRD-03": "ALCHEMY"}},
        )
        assert resp.status_code == 422

    def test_none_removal_and_no_persistence(self):
        client, repos = self._mh_client(
            {"F-BLD-01": 30000, "F-PRD-01": True}
        )
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"F-BLD-01": None}},
        )
        assert resp.status_code == 200
        assert resp.json()["applied_overrides"] == {"F-BLD-01": None}
        assert [
            c[0] for c in repos["facts_repo"].mock_calls
        ] == ["get_by_project"]


class TestMHRehearseAPI:
    def _mh_client(self, facts_json, approval_code, role):
        from app.api.regulatory import router

        repos = _repos(
            _make_app(approval_code), _mh_facts_record(facts_json)
        )
        return _client(router, repos, _make_user(role))

    def _rule_change(self, value):
        from app.seed.mh.approvals import load_mh_approval_rules

        current = next(
            r for r in load_mh_approval_rules() if r.id == "R-007"
        )
        old = current.model_dump(mode="json")
        new = json.loads(json.dumps(old))
        new["applicability_conditions"][0]["conditions"][0]["value"] = value
        return {"old": old, "new": new}

    def test_staff_rule_change_result_changed(self):
        client, _ = self._mh_client(
            {"F-BLD-01": 22000}, "APR-003", SystemRole.REVIEWER
        )
        change = self._rule_change(25000)
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {
                    "change_kind": "RULE_CHANGE",
                    "rule_id": "R-007",
                    "old_value": change["old"],
                    "new_value": change["new"],
                },
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["classification"] == "RESULT_CHANGED"
        assert body["affected_approvals"] == ["APR-003"]
        assert _strings(body).isdisjoint(GJ_IDS)

    def test_unknown_rule_422(self):
        client, _ = self._mh_client(
            {"F-BLD-01": 22000}, "APR-003", SystemRole.REVIEWER
        )
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {
                    "change_kind": "RULE_CHANGE",
                    "rule_id": "R-999",
                    "old_value": {"id": "R-999"},
                    "new_value": {"id": "R-999"},
                },
            },
        )
        assert resp.status_code == 422

    def test_evidence_change_result_changed(self):
        client, _ = self._mh_client(
            {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False},
            "APR-001",
            SystemRole.REVIEWER,
        )
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {
                    "change_kind": "EVIDENCE_STATUS_CHANGE",
                    "evidence_id": "UR-06",
                    "old_status": "NOT_ESTABLISHED",
                    "new_status": "VERIFIED",
                },
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["classification"] == "RESULT_CHANGED"
        assert body["affected_approvals"] == ["APR-001"]

    def test_source_metadata_relevant(self):
        client, _ = self._mh_client(
            {"F-BLD-01": 22000}, "APR-003", SystemRole.REVIEWER
        )
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {
                    "change_kind": "SOURCE_METADATA_CHANGE",
                    "source_id": "SRC-001",
                    "old_value": {"title": "a"},
                    "new_value": {"title": "b"},
                },
            },
        )
        assert resp.status_code == 200
        assert resp.json()["classification"] == "SOURCE_RELEVANT"

    def test_applicant_forbidden_and_stateless(self):
        client, repos = self._mh_client(
            {"F-BLD-01": 22000}, "APR-003", SystemRole.APPLICANT
        )
        change = self._rule_change(25000)
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {
                    "change_kind": "RULE_CHANGE",
                    "rule_id": "R-007",
                    "old_value": change["old"],
                    "new_value": change["new"],
                },
            },
        )
        assert resp.status_code == 403
        for name in ("app_repo", "facts_repo", "docs_repo"):
            for call in repos[name].mock_calls:
                assert call[0].startswith(("get_", "list_")), call


class TestMHHandoffAPI:
    def _mh_client(self, facts_json, approval_code,
                   role=SystemRole.APPLICANT, store=None):
        from app.api.handoffs import router

        repos = _repos(
            _make_app(approval_code),
            _mh_facts_record(facts_json),
            store or _handoff_store(),
        )
        return _client(router, repos, _make_user(role))

    def test_list_shows_mh_ready_approvals(self):
        client, _ = self._mh_client(
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]}, "APR-006"
        )
        resp = client.get(f"/applications/{APP_ID}/handoffs")
        assert resp.status_code == 200
        body = resp.json()
        ready = {
            r["approval_code"]: r for r in body["ready_approvals"]
        }
        assert "APR-006" in ready
        assert ready["APR-006"]["portal_url"] == "https://parivesh.nic.in/"
        assert _strings(body).isdisjoint(GJ_IDS)

    def test_initiate_verify_and_events(self):
        store = _handoff_store()
        client, repos = self._mh_client(
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]},
            "APR-006",
            SystemRole.APPLICANT,
            store,
        )
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate",
            json={"approval_code": "APR-006"},
        )
        assert resp.status_code == 200
        created = resp.json()
        assert created["external_system"] == "MoEFCC / PARIVESH"
        assert created["verification"] == "user_reported"
        assert repos["events_repo"].create.called
        hid = created["id"]
        # Duplicate active handoff -> 409.
        dup = client.post(
            f"/applications/{APP_ID}/handoffs/initiate",
            json={"approval_code": "APR-006"},
        )
        assert dup.status_code == 409
        # Applicant cannot verify (staff-only).
        denied = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/verify",
            json={"verified_status": "submitted_externally"},
        )
        assert denied.status_code == 403
        # Record submission, then staff verifies.
        sub = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/record-submission",
            json={"external_reference": "EXT-1"},
        )
        assert sub.status_code == 200
        staff_client, _ = self._mh_client(
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]},
            "APR-006",
            SystemRole.REVIEWER,
            store,
        )
        ok = staff_client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/verify",
            json={"verified_status": "submitted_externally"},
        )
        assert ok.status_code == 200
        assert ok.json()["verification"] == "staff_verified"

    def test_non_ready_rejected_and_unknown_code_422(self):
        client, _ = self._mh_client({"F-HW-01": True}, "APR-010")
        resp = client.post(
            f"/applications/{APP_ID}/handoffs/initiate",
            json={"approval_code": "APR-010"},
        )
        assert resp.status_code == 409
        unknown = client.post(
            f"/applications/{APP_ID}/handoffs/initiate",
            json={"approval_code": "ZZZ"},
        )
        assert unknown.status_code == 422

    def test_ownership_enforced(self):
        from app.api.handoffs import router

        repos = _repos(
            _make_app("APR-006", applicant_id=OTHER_ID),
            _mh_facts_record({"F-PRD-02": ["PESTICIDE_TECHNICAL"]}),
            _handoff_store(),
        )
        client, _ = _client(router, repos, _make_user())
        resp = client.get(f"/applications/{APP_ID}/handoffs")
        assert resp.status_code == 403


class TestMHDocumentSeedingAPI:
    def test_apr010_seeds_doc_requirements(self):
        from app.repositories.projects import ProjectRepository

        app_dict = _make_app("APR-010")
        app_repo = MagicMock(spec=ApplicationsRepository)
        app_repo.create_with_reference.return_value = app_dict
        docs_repo = MagicMock(spec=DocumentsRepository)
        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = {
            "id": PROJECT_ID,
            "applicant_id": USER_ID,
            "jurisdiction": "IN-MH",
            "pack_version": "mh-v5-batch1",
        }
        app = FastAPI()
        app.include_router(applications_router)
        app.dependency_overrides[get_current_user] = lambda: _make_user()
        app.dependency_overrides[get_applications_repository] = (
            lambda: app_repo
        )
        app.dependency_overrides[get_documents_repository] = (
            lambda: docs_repo
        )
        from app.api.deps import get_project_repository

        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        resp = client.post(
            "/applications",
            params={
                "project_id": PROJECT_ID,
                "approval_id": app_dict["approval_id"],
                "approval_code": "APR-010",
            },
        )
        assert resp.status_code == 200
        assert docs_repo.create_requirements_bulk.called
        seeded = docs_repo.create_requirements_bulk.call_args[0][0]
        assert {r["requirement_key"] for r in seeded} == {
            "DOC-001", "DOC-002", "DOC-003"
        }
        assert _strings(seeded).isdisjoint(GJ_IDS)


class TestIsolationAndDefaults:
    def test_unscoped_record_rejected_no_fallback(self):
        from app.api.orchestration import router

        unscoped = _make_app("APR-006")
        del unscoped["jurisdiction"]
        del unscoped["pack_version"]
        repos = _repos(unscoped, _mh_facts_record({}))
        client, _ = _client(router, repos, _make_user())
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 422

    def test_request_override_cannot_hijack_persisted_record(self):
        from app.api.orchestration import router

        # GJ-persisted record resolves the GJ pack even with an MH
        # request override active: R-IFP-001 still applies, no MH IDs.
        repos = _repos(
            _make_app(
                "A04",
                reference_number="APP-GJ-HIJACK",
                jurisdiction="IN-GJ",
                pack_version="gj-legacy-unversioned",
            ),
            _mh_facts_record({
                "industry_type": (
                    "synthetic organic / specialty chemical "
                    "manufacturing"
                ),
            }),
        )
        client, _ = _client(router, repos, _make_user())
        client.app.dependency_overrides[get_active_jurisdiction] = (
            lambda: IN_MH
        )
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 200
        body = resp.json()
        assert body["approvals"]["A04"]["applicability_result"] == "applies"
        assert _strings(body).isdisjoint(MH_RULE_IDS)
        assert "APR-001" not in _strings(body)

    def test_zz_default_still_gj_after_mh_tests(self):
        assert DEFAULT_JURISDICTION == IN_GJ
        from app.api.deps import get_active_jurisdiction as resolve

        assert resolve() == IN_GJ
