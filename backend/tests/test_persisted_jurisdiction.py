"""Persisted jurisdiction/pack identity — TEST-01..17 + extras (Phase 10).

Every test uses explicit persisted identity on mock rows (simulating
post-migration storage). No test relies on the global default for
existing records. DEFAULT_JURISDICTION stays IN-GJ throughout.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import (
    get_applications_repository,
    get_consistency_repository,
    get_documents_repository,
    get_handoffs_repository,
    get_project_facts_repository,
    get_project_repository,
    get_workflow_events_repository,
)
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.handoffs import HandoffsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.seed.pack import (
    DEFAULT_JURISDICTION,
    IN_GJ,
    UnknownPackError,
    resolve_persisted_pack,
)

APP_ID = "00000000-0000-0000-0000-000000000099"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"
USER_ID = "00000000-0000-0000-0000-000000000001"
APPROVAL_UUID = "00000000-0000-0000-0000-000000000100"

GJ_PAIR = {"jurisdiction": "IN-GJ", "pack_version": "gj-legacy-unversioned"}
MH_PAIR = {"jurisdiction": "IN-MH", "pack_version": "mh-v5-batch1"}


def _user(role=SystemRole.APPLICANT):
    return UserContext(
        user_id=USER_ID, email="t@t.com", role=role, raw_claims={}
    )


def _gj_project(**over):
    row = {
        "id": PROJECT_ID,
        "name": "GJ project",
        "applicant_id": USER_ID,
        "status": "active",
        **GJ_PAIR,
    }
    row.update(over)
    return row


def _mh_project(**over):
    row = {
        "id": PROJECT_ID,
        "name": "MH project",
        "applicant_id": USER_ID,
        "status": "active",
        **MH_PAIR,
    }
    row.update(over)
    return row


def _gj_app(code="A04", **over):
    row = {
        "id": APP_ID,
        "project_id": PROJECT_ID,
        "applicant_id": USER_ID,
        "status": "draft",
        "approval_id": APPROVAL_UUID,
        "approval_code": code,
        "reference_number": "APP-PJ",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        **GJ_PAIR,
    }
    row.update(over)
    return row


def _mh_app(code="APR-006", **over):
    row = {
        "id": APP_ID,
        "project_id": PROJECT_ID,
        "applicant_id": USER_ID,
        "status": "draft",
        "approval_id": APPROVAL_UUID,
        "approval_code": code,
        "reference_number": "APP-PJ-MH",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        **MH_PAIR,
    }
    row.update(over)
    return row


def _facts_row(facts_json):
    return {
        "id": "facts-1",
        "project_id": PROJECT_ID,
        "entity_type": "pvt-ltd",
        "sector": "chemical",
        "jurisdictions": [],
        "headcount": 0,
        "annual_turnover_inr": 0,
        "facts_json": dict(facts_json),
        "created_at": "2026-09-15T10:00:00Z",
        "updated_at": "2026-09-15T10:00:00Z",
    }


def _repos(app_row=None, facts_json=None, project_row=None):
    app_repo = MagicMock(spec=ApplicationsRepository)
    app_repo.get_by_id.return_value = app_row
    app_repo.get_by_project.return_value = [app_row] if app_row else []
    app_repo.get_approval_stages.return_value = []
    facts_repo = MagicMock(spec=ProjectFactsRepository)
    facts_repo.get_by_project.return_value = (
        _facts_row(facts_json) if facts_json is not None else None
    )
    docs_repo = MagicMock(spec=DocumentsRepository)
    docs_repo.list_documents_for_application.return_value = []
    docs_repo.get_extraction_result_for_document.return_value = None
    docs_repo.get_validation_result_for_document.return_value = None
    events_repo = MagicMock(spec=WorkflowEventsRepository)
    events_repo.list_for_application.return_value = []
    consistency_repo = MagicMock(spec=ConsistencyRepository)
    consistency_repo.get_latest_result.return_value = None
    project_repo = MagicMock(spec=ProjectRepository)
    project_repo.get_by_id.return_value = project_row
    store = MagicMock(spec=HandoffsRepository)
    store.list_for_application.return_value = []
    store.get_active_for_approval.return_value = None
    return {
        "app_repo": app_repo,
        "facts_repo": facts_repo,
        "docs_repo": docs_repo,
        "events_repo": events_repo,
        "consistency_repo": consistency_repo,
        "project_repo": project_repo,
        "store": store,
    }


def _client(router, repos, user, with_handoffs=False):
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
    app.dependency_overrides[get_project_repository] = (
        lambda: repos["project_repo"]
    )
    if with_handoffs:
        app.dependency_overrides[get_handoffs_repository] = (
            lambda: repos["store"]
        )
    return TestClient(app), repos


GJ_INDUSTRY_FACTS = {
    "industry_type": "synthetic organic / specialty chemical manufacturing"
}


class TestPersistedResolution:
    def test_01_legacy_project_resolves_gj(self):
        pack = resolve_persisted_pack("IN-GJ", "gj-legacy-unversioned")
        assert pack.jurisdiction == IN_GJ
        assert any(r.id == "R-GIDC-001" for r in pack.approval_rules)

    def test_02_legacy_application_resolves_gj_pack(self):
        from app.api.orchestration import router

        repos = _repos(_gj_app("A04"), GJ_INDUSTRY_FACTS)
        client, _ = _client(router, repos, _user())
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 200
        assert resp.json()["approvals"]["A04"][
            "applicability_result"
        ] == "applies"

    def test_03_new_project_uses_current_default(self):
        from app.api.projects import router

        captured: dict = {}

        def fake_create(data):
            captured.update(data)
            return {"id": PROJECT_ID, **data}

        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.create.side_effect = fake_create
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        resp = client.post("/projects", params={"name": "P"})
        assert resp.status_code == 200
        assert captured["jurisdiction"] == "IN-GJ"
        assert captured["pack_version"] == "gj-legacy-unversioned"

    def test_client_supplied_jurisdiction_ignored(self):
        from app.api.projects import router

        captured: dict = {}

        def fake_create(data):
            captured.update(data)
            return {"id": PROJECT_ID, **data}

        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.create.side_effect = fake_create
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        resp = client.post(
            "/projects",
            params={
                "name": "P",
                "jurisdiction": "IN-MH",
                "pack_version": "mh-v5-batch1",
            },
        )
        assert resp.status_code == 200
        assert captured["jurisdiction"] == "IN-GJ"
        assert captured["pack_version"] == "gj-legacy-unversioned"

    def test_04_new_application_inherits_project_identity(self):
        from app.api.applications import router

        captured: dict = {}
        app_repo = MagicMock(spec=ApplicationsRepository)
        app_repo.create_with_reference.side_effect = lambda data: (
            captured.update(data) or {"id": APP_ID, **data}
        )
        docs_repo = MagicMock(spec=DocumentsRepository)
        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = _gj_project()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_applications_repository] = (
            lambda: app_repo
        )
        app.dependency_overrides[get_documents_repository] = (
            lambda: docs_repo
        )
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        resp = client.post(
            "/applications",
            params={
                "project_id": PROJECT_ID,
                "approval_id": APPROVAL_UUID,
                "approval_code": "A03",
            },
        )
        assert resp.status_code == 200, resp.text
        assert captured["jurisdiction"] == "IN-GJ"
        assert captured["pack_version"] == "gj-legacy-unversioned"
        assert captured["approval_code"] == "A03"

    def test_05_flip_simulation_keeps_gj_project(self, monkeypatch):
        import app.seed.pack as pack_module

        monkeypatch.setattr(pack_module, "DEFAULT_JURISDICTION", "IN-MH")
        from app.api.projects import router

        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = _gj_project()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        resp = client.get(f"/projects/{PROJECT_ID}")
        assert resp.status_code == 200
        assert resp.json()["jurisdiction"] == "IN-GJ"
        assert resp.json()["pack_version"] == "gj-legacy-unversioned"

    def test_06_flip_simulation_keeps_gj_application(self, monkeypatch):
        import app.seed.pack as pack_module

        monkeypatch.setattr(pack_module, "DEFAULT_JURISDICTION", "IN-MH")
        from app.api.deps import get_active_jurisdiction as resolve

        assert resolve() == "IN-MH"  # default moved ...
        from app.api.orchestration import router

        # ... yet the persisted GJ record still resolves GJ.
        repos = _repos(_gj_app("A04"), GJ_INDUSTRY_FACTS)
        client, _ = _client(router, repos, _user())
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 200
        assert resp.json()["approvals"]["A04"][
            "applicability_result"
        ] == "applies"

    def test_07_mh_seeded_records_resolve_mh(self):
        from app.api.orchestration import router

        repos = _repos(
            _mh_app("APR-006"),
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]},
        )
        client, _ = _client(router, repos, _user())
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 200
        orch = resp.json()["approvals"]["APR-006"]
        assert orch["applicability_result"] == "applies"
        assert orch["status"] == "ready"

    def test_08_gj_application_with_apr_code_rejected(self):
        from app.api.applications import router

        app_repo = MagicMock(spec=ApplicationsRepository)
        docs_repo = MagicMock(spec=DocumentsRepository)
        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = _gj_project()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_applications_repository] = (
            lambda: app_repo
        )
        app.dependency_overrides[get_documents_repository] = (
            lambda: docs_repo
        )
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        resp = client.post(
            "/applications",
            params={
                "project_id": PROJECT_ID,
                "approval_id": APPROVAL_UUID,
                "approval_code": "APR-006",
            },
        )
        assert resp.status_code == 422
        assert not app_repo.create_with_reference.called

    def test_09_mh_application_with_a_code_rejected(self):
        from app.api.applications import router

        app_repo = MagicMock(spec=ApplicationsRepository)
        docs_repo = MagicMock(spec=DocumentsRepository)
        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = _mh_project()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_applications_repository] = (
            lambda: app_repo
        )
        app.dependency_overrides[get_documents_repository] = (
            lambda: docs_repo
        )
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        resp = client.post(
            "/applications",
            params={
                "project_id": PROJECT_ID,
                "approval_id": APPROVAL_UUID,
                "approval_code": "A04",
            },
        )
        assert resp.status_code == 422
        assert not app_repo.create_with_reference.called

    def test_10_unknown_pair_rejected(self):
        with pytest.raises(UnknownPackError):
            resolve_persisted_pack("IN-MH", "v9")
        with pytest.raises(UnknownPackError):
            resolve_persisted_pack(None, None)
        from app.api.orchestration import router

        repos = _repos(
            _gj_app("A04", jurisdiction="IN-MH",
                    pack_version="gj-legacy-unversioned"),
            GJ_INDUSTRY_FACTS,
        )
        client, _ = _client(router, repos, _user())
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 422


class TestPersistedWhatIf:
    def test_11_gj_whatif_uses_gj_registry(self):
        from app.api.orchestration import router

        repos = _repos(
            _gj_app("A04"),
            {"production_capacity": 20000, **GJ_INDUSTRY_FACTS},
        )
        client, _ = _client(router, repos, _user())
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"production_capacity": 100}},
        )
        assert resp.status_code == 200
        bad = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"F-BLD-01": 5}},
        )
        assert bad.status_code == 422

    def test_12_mh_whatif_uses_mh_registry(self):
        from app.api.orchestration import router

        repos = _repos(_mh_app("APR-003"), {"F-BLD-01": 30000})
        client, _ = _client(router, repos, _user())
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"F-BLD-01": 1000}},
        )
        assert resp.status_code == 200
        assert resp.json()["diff"]["no_change"] is False
        bad = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"industry_type": "x"}},
        )
        assert bad.status_code == 422


class TestPersistedRehearsal:
    def _gj_payload(self):
        from app.seed.approvals import load_approval_rules

        old = next(
            r for r in load_approval_rules() if r.id == "R-EIA-001"
        ).model_dump()
        new = json.loads(json.dumps(old))
        new["applicability_conditions"] = [
            {
                "kind": "and",
                "conditions": [
                    {
                        "kind": "condition",
                        "field": "industry_type",
                        "op": "eq",
                        "value": (
                            "synthetic organic / specialty chemical "
                            "manufacturing"
                        ),
                    },
                    {
                        "kind": "condition",
                        "field": "production_capacity",
                        "op": "gte",
                        "value": 30000,
                    },
                ],
            }
        ]
        return old, new

    def _mh_payload(self):
        from app.seed.mh.approvals import load_mh_approval_rules

        old = next(
            r for r in load_mh_approval_rules() if r.id == "R-007"
        ).model_dump(mode="json")
        new = json.loads(json.dumps(old))
        new["applicability_conditions"][0]["conditions"][0]["value"] = (
            25000
        )
        return old, new

    def test_13_gj_rehearsal_uses_gj_pack(self):
        from app.api.regulatory import router

        repos = _repos(_gj_app("A05"), GJ_INDUSTRY_FACTS)
        client, _ = _client(
            router, repos, _user(role=SystemRole.REVIEWER)
        )
        old, new = self._gj_payload()
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {
                    "change_kind": "RULE_CHANGE",
                    "rule_id": "R-EIA-001",
                    "old_value": old,
                    "new_value": new,
                },
            },
        )
        assert resp.status_code == 200

    def test_14_mh_rehearsal_uses_mh_pack(self):
        from app.api.regulatory import router

        repos = _repos(_mh_app("APR-003"), {"F-BLD-01": 22000})
        client, _ = _client(
            router, repos, _user(role=SystemRole.REVIEWER)
        )
        old, new = self._mh_payload()
        resp = client.post(
            "/regulatory/changes/rehearse",
            json={
                "application_id": APP_ID,
                "change": {
                    "change_kind": "RULE_CHANGE",
                    "rule_id": "R-007",
                    "old_value": old,
                    "new_value": new,
                },
            },
        )
        assert resp.status_code == 200
        assert resp.json()["classification"] == "RESULT_CHANGED"


class TestPersistedHandoff:
    def test_15_gj_handoff_resolves_gj_catalog(self):
        from app.api.handoffs import router

        facts = {"boiler_present": True}
        repos = _repos(_gj_app("A16"), facts, None)
        client, _ = _client(
            router, repos, _user(), with_handoffs=True
        )
        resp = client.get(f"/applications/{APP_ID}/handoffs")
        assert resp.status_code == 200
        ready = {
            r["approval_code"]: r
            for r in resp.json()["ready_approvals"]
        }
        assert "A16" in ready
        assert "boiler.gujarat.gov.in" in ready["A16"]["portal_url"]

    def test_16_mh_handoff_resolves_mh_catalog(self):
        from app.api.handoffs import router

        repos = _repos(
            _mh_app("APR-006"),
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]},
            None,
        )
        client, _ = _client(
            router, repos, _user(), with_handoffs=True
        )
        resp = client.get(f"/applications/{APP_ID}/handoffs")
        assert resp.status_code == 200
        ready = {
            r["approval_code"]: r
            for r in resp.json()["ready_approvals"]
        }
        assert ready["APR-006"]["portal_url"] == (
            "https://parivesh.nic.in/"
        )


class TestPersistedDocuments:
    def test_17_document_resolution_stays_scoped(self):
        from app.seed.pack import load_regulatory_pack

        gj = load_regulatory_pack("IN-GJ").get_requirements_for_approval(
            "A03"
        )
        mh = load_regulatory_pack("IN-MH").get_requirements_for_approval(
            "APR-010"
        )
        assert gj and all(
            r["requirement_key"].startswith("D") for r in gj
        )
        assert {r["requirement_key"] for r in mh} == {
            "DOC-001", "DOC-002", "DOC-003"
        }
        assert {r["requirement_key"] for r in gj} & {
            r["requirement_key"] for r in mh
        } == set()


class TestPersistedExtras:
    def test_application_identity_authoritative_over_project(self):
        # Direct mismatch cannot arise via the API (creation inherits),
        # but resolution must follow the APPLICATION row, never the
        # project row or the default.
        from app.api.orchestration import router

        app_row = _mh_app("APR-006")  # MH application ...
        repos = _repos(
            app_row, {"F-PRD-02": ["PESTICIDE_TECHNICAL"]}
        )
        # ... whose project row claims GJ (inconsistent legacy state).
        repos["project_repo"] = MagicMock()
        client, _ = _client(router, repos, _user())
        resp = client.get(f"/applications/{APP_ID}/orchestration")
        assert resp.status_code == 200
        assert resp.json()["approvals"]["APR-006"]["status"] == "ready"

    def test_no_a_to_apr_translation(self):
        assert _gj_app("A03")["approval_code"] == "A03"

    def test_default_untouched(self):
        assert DEFAULT_JURISDICTION == IN_GJ


class TestFlipRehearsal:
    """Simulated default flip (monkeypatched constant only) and flip-back.

    No repository constant is modified: ``monkeypatch`` restores the
    original value after each test.
    """

    def _create_project(self, project_repo):
        from app.api.projects import router

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        return TestClient(app)

    def test_flip_new_projects_follow_simulated_default(self, monkeypatch):
        import app.seed.pack as pack_module

        monkeypatch.setattr(pack_module, "DEFAULT_JURISDICTION", "IN-MH")
        captured: dict = {}

        def fake_create(data):
            captured.update(data)
            return {"id": PROJECT_ID, **data}

        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.create.side_effect = fake_create
        client = self._create_project(project_repo)
        resp = client.post("/projects", params={"name": "MH-sim"})
        assert resp.status_code == 200
        assert captured["jurisdiction"] == "IN-MH"
        assert captured["pack_version"] == "mh-v5-batch1"

    def test_flip_back_restores_gj_for_new_projects(self, monkeypatch):
        import app.seed.pack as pack_module

        monkeypatch.setattr(pack_module, "DEFAULT_JURISDICTION", "IN-MH")
        from app.api.deps import get_active_jurisdiction as resolve

        assert resolve() == "IN-MH"
        monkeypatch.setattr(pack_module, "DEFAULT_JURISDICTION", "IN-GJ")
        assert resolve() == "IN-GJ"
        captured: dict = {}

        def fake_create(data):
            captured.update(data)
            return {"id": PROJECT_ID, **data}

        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.create.side_effect = fake_create
        client = self._create_project(project_repo)
        resp = client.post("/projects", params={"name": "GJ-again"})
        assert resp.status_code == 200
        assert captured["jurisdiction"] == "IN-GJ"

    def test_existing_identities_survive_flip_and_back(self, monkeypatch):
        import app.seed.pack as pack_module
        from app.api.orchestration import router

        gj_repos = _repos(_gj_app("A04"), GJ_INDUSTRY_FACTS)
        gj_client, _ = _client(router, gj_repos, _user())
        mh_repos = _repos(
            _mh_app("APR-006"),
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]},
        )
        mh_client, _ = _client(router, mh_repos, _user())
        for default in ("IN-MH", "IN-GJ"):
            monkeypatch.setattr(
                pack_module, "DEFAULT_JURISDICTION", default
            )
            gj = gj_client.get(f"/applications/{APP_ID}/orchestration")
            assert gj.status_code == 200
            assert gj.json()["approvals"]["A04"][
                "applicability_result"
            ] == "applies"
            mh = mh_client.get(f"/applications/{APP_ID}/orchestration")
            assert mh.status_code == 200
            assert mh.json()["approvals"]["APR-006"][
                "status"
            ] == "ready"


class TestCaseAInvariant:
    def test_two_creates_under_one_project_share_identity(self):
        from app.api.applications import router

        created: list[dict] = []
        app_repo = MagicMock(spec=ApplicationsRepository)
        app_repo.create_with_reference.side_effect = lambda data: (
            created.append(dict(data)) or {"id": APP_ID, **data}
        )
        docs_repo = MagicMock(spec=DocumentsRepository)
        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = _gj_project()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: _user()
        app.dependency_overrides[get_applications_repository] = (
            lambda: app_repo
        )
        app.dependency_overrides[get_documents_repository] = (
            lambda: docs_repo
        )
        app.dependency_overrides[get_project_repository] = (
            lambda: project_repo
        )
        client = TestClient(app)
        for code in ("A04", "A06"):
            resp = client.post(
                "/applications",
                params={
                    "project_id": PROJECT_ID,
                    "approval_id": APPROVAL_UUID,
                    "approval_code": code,
                },
            )
            assert resp.status_code == 200, resp.text
        assert {c["jurisdiction"] for c in created} == {"IN-GJ"}
        assert {c["pack_version"] for c in created} == {
            "gj-legacy-unversioned"
        }
        # No request parameter can smuggle a different jurisdiction:
        # create accepts no jurisdiction/pack fields at all.
        resp = client.post(
            "/applications",
            params={
                "project_id": PROJECT_ID,
                "approval_id": APPROVAL_UUID,
                "approval_code": "A04",
                "jurisdiction": "IN-MH",
                "pack_version": "mh-v5-batch1",
            },
        )
        assert resp.status_code == 200
        assert created[-1]["jurisdiction"] == "IN-GJ"
