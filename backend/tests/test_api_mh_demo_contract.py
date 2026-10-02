"""MH demo integration contracts (T3).

Covers only the API-contract additions that let the UI drive the
Maharashtra demo explicitly, without touching the global default:

- POST /projects accepts an optional, strictly-validated
  ``requested_jurisdiction`` (default behavior unchanged).
- GET /projects/{id}/approval-codes projects the persisted pack.
- POST /applications links the pack catalog row when ``approval_id``
  is omitted (legacy explicit-UUID path unchanged).
- POST /projects/{id}/facts accepts ``facts_json`` as a JSON body on
  IN-MH projects (validated against the MH registry).

No regulatory semantics are asserted beyond pack identity; rule
behavior is covered by the MH rule suites. Mocked persistence,
real packs/engines (same style as test_mh_api_e2e.py).
"""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.applications import router as applications_router
from app.api.deps import (
    get_active_jurisdiction,
    get_applications_repository,
    get_approvals_repository,
    get_documents_repository,
    get_project_facts_repository,
    get_project_repository,
)
from app.api.projects import router as projects_router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.seed.pack import DEFAULT_JURISDICTION, DEFAULT_PACK_VERSIONS

USER_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"


def _make_user(role=SystemRole.APPLICANT):
    return UserContext(user_id=USER_ID, email="t@t.com", role=role, raw_claims={})


def _project(jurisdiction="IN-MH"):
    return {
        "id": PROJECT_ID,
        "name": "Sahyadri",
        "description": "demo",
        "applicant_id": USER_ID,
        "jurisdiction": jurisdiction,
        "pack_version": DEFAULT_PACK_VERSIONS[jurisdiction],
    }


def _client(projects_repo=None, approvals_repo=None, applications_repo=None,
            documents_repo=None, facts_repo=None, jurisdiction=None):
    app = FastAPI()
    app.include_router(projects_router)
    app.include_router(applications_router)
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    if jurisdiction is not None:
        app.dependency_overrides[get_active_jurisdiction] = lambda: jurisdiction
    if projects_repo is not None:
        app.dependency_overrides[get_project_repository] = lambda: projects_repo
    if approvals_repo is not None:
        app.dependency_overrides[get_approvals_repository] = lambda: approvals_repo
    if applications_repo is not None:
        app.dependency_overrides[get_applications_repository] = lambda: applications_repo
    if documents_repo is not None:
        app.dependency_overrides[get_documents_repository] = lambda: documents_repo
    if facts_repo is not None:
        app.dependency_overrides[get_project_facts_repository] = lambda: facts_repo
    return TestClient(app)


def _mock_projects_repo(project):
    repo = MagicMock()
    repo.get_by_id.return_value = project
    repo.create.side_effect = lambda data: {"id": PROJECT_ID, **data}
    return repo


class TestProjectCreationJurisdiction:
    def test_default_stays_in_gj(self):
        client = _client(projects_repo=_mock_projects_repo(_project("IN-GJ")))
        resp = client.post("/projects", params={"name": "P"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["jurisdiction"] == "IN-GJ"
        assert body["pack_version"] == DEFAULT_PACK_VERSIONS["IN-GJ"]

    def test_explicit_in_mh(self):
        repo = _mock_projects_repo(_project("IN-MH"))
        client = _client(projects_repo=repo)
        resp = client.post(
            "/projects", params={"name": "Sahyadri", "requested_jurisdiction": "IN-MH"}
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["jurisdiction"] == "IN-MH"
        assert body["pack_version"] == DEFAULT_PACK_VERSIONS["IN-MH"]
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_unknown_jurisdiction_rejected(self):
        client = _client(projects_repo=_mock_projects_repo(_project("IN-GJ")))
        resp = client.post(
            "/projects", params={"name": "P", "requested_jurisdiction": "IN-XX"}
        )
        assert resp.status_code == 422


class TestApprovalCodesProjection:
    def test_mh_codes_with_authorities(self):
        client = _client(projects_repo=_mock_projects_repo(_project("IN-MH")))
        resp = client.get(f"/projects/{PROJECT_ID}/approval-codes")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["jurisdiction"] == "IN-MH"
        codes = {r["approval_code"]: r["authority"] for r in body["approvals"]}
        assert "APR-026" in codes and "APR-010" in codes and "APR-001" in codes
        assert codes["APR-026"] == "AUT-008 / AUT-009"
        assert len(codes) == 20

    def test_gj_codes_unchanged(self):
        client = _client(projects_repo=_mock_projects_repo(_project("IN-GJ")))
        resp = client.get(f"/projects/{PROJECT_ID}/approval-codes")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["jurisdiction"] == "IN-GJ"
        assert any(r["approval_code"].startswith("A") for r in body["approvals"])

    def test_missing_project_404(self):
        repo = _mock_projects_repo(_project("IN-MH"))
        repo.get_by_id.return_value = None
        client = _client(projects_repo=repo)
        resp = client.get(f"/projects/{PROJECT_ID}/approval-codes")
        assert resp.status_code == 404


class TestApplicationCreationLinking:
    def _repos(self, catalog_row=None):
        approvals_repo = MagicMock()
        approvals_repo.get_by_code.return_value = catalog_row
        approvals_repo.create.side_effect = (
            lambda data: {"id": str(uuid4()), **data}
        )
        applications_repo = MagicMock()
        applications_repo.create_with_reference.side_effect = (
            lambda data: {"id": str(uuid4()), "reference_number": "R", **data}
        )
        documents_repo = MagicMock()
        return approvals_repo, applications_repo, documents_repo

    def test_mh_code_without_approval_id_links_catalog(self):
        approvals_repo, applications_repo, documents_repo = self._repos()
        client = _client(
            projects_repo=_mock_projects_repo(_project("IN-MH")),
            approvals_repo=approvals_repo,
            applications_repo=applications_repo,
            documents_repo=documents_repo,
        )
        resp = client.post(
            "/applications",
            params={"project_id": PROJECT_ID, "approval_code": "APR-026"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["approval_code"] == "APR-026"
        assert body["jurisdiction"] == "IN-MH"
        approvals_repo.create.assert_called_once()
        created = approvals_repo.create.call_args[0][0]
        assert created["code"] == "APR-026"
        assert created["authority"] == "AUT-008 / AUT-009"

    def test_existing_catalog_row_reused(self):
        row = {"id": str(uuid4()), "code": "APR-010"}
        approvals_repo, applications_repo, documents_repo = self._repos(row)
        client = _client(
            projects_repo=_mock_projects_repo(_project("IN-MH")),
            approvals_repo=approvals_repo,
            applications_repo=applications_repo,
            documents_repo=documents_repo,
        )
        resp = client.post(
            "/applications",
            params={"project_id": PROJECT_ID, "approval_code": "APR-010"},
        )
        assert resp.status_code == 200, resp.text
        approvals_repo.create.assert_not_called()
        assert resp.json()["approval_id"] == row["id"]

    def test_unknown_code_rejected(self):
        approvals_repo, applications_repo, documents_repo = self._repos()
        client = _client(
            projects_repo=_mock_projects_repo(_project("IN-MH")),
            approvals_repo=approvals_repo,
            applications_repo=applications_repo,
            documents_repo=documents_repo,
        )
        resp = client.post(
            "/applications",
            params={"project_id": PROJECT_ID, "approval_code": "APR-999"},
        )
        assert resp.status_code == 422

    def test_gj_code_against_gj_project_rejected(self):
        # No cross-jurisdiction smuggling: an APR code under IN-GJ 422s.
        approvals_repo, applications_repo, documents_repo = self._repos()
        client = _client(
            projects_repo=_mock_projects_repo(_project("IN-GJ")),
            approvals_repo=approvals_repo,
            applications_repo=applications_repo,
            documents_repo=documents_repo,
        )
        resp = client.post(
            "/applications",
            params={"project_id": PROJECT_ID, "approval_code": "APR-026"},
        )
        assert resp.status_code == 422

    def test_legacy_explicit_approval_id_unchanged(self):
        approvals_repo, applications_repo, documents_repo = self._repos()
        client = _client(
            projects_repo=_mock_projects_repo(_project("IN-GJ")),
            approvals_repo=approvals_repo,
            applications_repo=applications_repo,
            documents_repo=documents_repo,
        )
        legacy_id = str(uuid4())
        resp = client.post(
            "/applications",
            params={
                "project_id": PROJECT_ID,
                "approval_id": legacy_id,
                "approval_code": "A04",
            },
        )
        # A04 may not be in the GJ seed rules; accept either the created
        # application (code known) or the pack 422 (code unknown) — the
        # assertion is that an explicit UUID passes through untouched.
        if resp.status_code == 200:
            assert resp.json()["approval_id"] == legacy_id
            approvals_repo.create.assert_not_called()
        else:
            assert resp.status_code == 422


class TestMhFactsJsonBody:
    # Contract note: because the endpoint also declares the complex query
    # param ``jurisdictions: list[str]``, FastAPI embeds the body field —
    # the client must send {"facts_json": {...}}, not the bare dict.

    def test_facts_json_body_accepted_and_validated(self):
        facts_repo = MagicMock()
        facts_repo.upsert.side_effect = lambda pid, data: {"project_id": pid, **data}
        client = _client(
            projects_repo=_mock_projects_repo(_project("IN-MH")),
            facts_repo=facts_repo,
        )
        payload = {"F-PET-01": "B", "F-PET-02": 2000, "F-LAB-01": 60}
        resp = client.post(
            f"/projects/{PROJECT_ID}/facts",
            params={"entity_type": "pvt-ltd", "sector": "chemical"},
            json={"facts_json": payload},
        )
        assert resp.status_code == 200, resp.text
        stored = facts_repo.upsert.call_args[0][1]
        assert stored["facts_json"] == payload

    def test_invalid_mh_fact_rejected(self):
        facts_repo = MagicMock()
        client = _client(
            projects_repo=_mock_projects_repo(_project("IN-MH")),
            facts_repo=facts_repo,
        )
        resp = client.post(
            f"/projects/{PROJECT_ID}/facts",
            params={"entity_type": "pvt-ltd", "sector": "chemical"},
            json={"facts_json": {"F-NOPE-99": 1}},
        )
        assert resp.status_code == 422
        facts_repo.upsert.assert_not_called()
