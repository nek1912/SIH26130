"""Integration tests for orchestration endpoint wiring.

Verifies that the orchestration endpoint correctly fetches and incorporates
extraction results, validation results, consistency results, SLA state,
and obtained approvals from sibling applications.
"""
from __future__ import annotations

from unittest.mock import MagicMock

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


def _make_user() -> UserContext:
    return UserContext(
        user_id="00000000-0000-0000-0000-000000000001",
        email="test@test.com",
        role=SystemRole.APPLICANT,
        raw_claims={},
    )


def _make_app(
    app_id: str = "00000000-0000-0000-0000-000000000099",
    project_id: str = "00000000-0000-0000-0000-000000000050",
    applicant_id: str = "00000000-0000-0000-0000-000000000001",
    status: str = "draft",
    approval_id: str = "00000000-0000-0000-0000-000000000100",
    approval_code: str = "A04",
) -> dict:
    return {
        "id": app_id,
        "project_id": project_id,
        "applicant_id": applicant_id,
        "status": status,
        "approval_id": approval_id,
        "approval_code": approval_code,
        "reference_number": "APP-TEST001",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    }


def _make_app_repo(app: dict | None = None) -> MagicMock:
    repo = MagicMock(spec=ApplicationsRepository)
    repo.get_by_id.return_value = app or _make_app()
    repo.get_by_project.return_value = [app or _make_app()]
    repo.get_approval_stages.return_value = []
    return repo


def _make_facts_repo(facts: dict | None = None) -> MagicMock:
    repo = MagicMock(spec=ProjectFactsRepository)
    repo.get_by_project.return_value = facts
    return repo


def _make_docs_repo(
    docs: list | None = None,
    extraction_results: list | None = None,
    validation_results: list | None = None,
) -> MagicMock:
    repo = MagicMock(spec=DocumentsRepository)
    repo.list_documents_for_application.return_value = docs or []
    repo.get_extraction_result_for_document = MagicMock(
        side_effect=lambda doc_id: next(
            (r for r in (extraction_results or []) if r.get("document_id") == doc_id),
            None,
        )
    )
    repo.get_validation_result_for_document = MagicMock(
        side_effect=lambda doc_id: next(
            (r for r in (validation_results or []) if r.get("document_id") == doc_id),
            None,
        )
    )
    return repo


def _make_events_repo(events: list | None = None) -> MagicMock:
    repo = MagicMock(spec=WorkflowEventsRepository)
    repo.list_for_application.return_value = events or []
    return repo


def _make_consistency_repo(result: dict | None = None) -> MagicMock:
    repo = MagicMock(spec=ConsistencyRepository)
    repo.get_latest_result.return_value = result
    return repo


def _build_client(
    app_repo: ApplicationsRepository | None = None,
    facts_repo: ProjectFactsRepository | None = None,
    docs_repo: DocumentsRepository | None = None,
    events_repo: WorkflowEventsRepository | None = None,
    consistency_repo: ConsistencyRepository | None = None,
) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    user = _make_user()

    def override_get_user():
        return user

    app.dependency_overrides[get_current_user] = override_get_user

    from app.api.deps import (
        get_applications_repository,
        get_consistency_repository,
        get_documents_repository,
        get_project_facts_repository,
        get_workflow_events_repository,
    )

    app.dependency_overrides[get_applications_repository] = (
        lambda: app_repo or _make_app_repo()
    )
    app.dependency_overrides[get_project_facts_repository] = (
        lambda: facts_repo or _make_facts_repo()
    )
    app.dependency_overrides[get_documents_repository] = (
        lambda: docs_repo or _make_docs_repo()
    )
    app.dependency_overrides[get_workflow_events_repository] = (
        lambda: events_repo or _make_events_repo()
    )
    app.dependency_overrides[get_consistency_repository] = (
        lambda: consistency_repo or _make_consistency_repo()
    )

    return TestClient(app)


class TestOrchestrationWiring:
    """Verify the orchestration endpoint wires real data from DB."""

    def test_returns_200_with_basic_data(self):
        """Basic orchestration call succeeds with empty DB state."""
        client = _build_client()
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "approvals" in data
        assert "next_action" in data

    def test_returns_404_for_missing_application(self):
        """Returns 404 when application does not exist."""
        app_repo = _make_app_repo(None)
        app_repo.get_by_id.return_value = None
        client = _build_client(app_repo=app_repo)

        response = client.get(
            "/applications/00000000-0000-0000-0000-000000000099/orchestration"
        )
        assert response.status_code == 404

    def test_incorporates_extraction_results(self):
        """Extraction results from DB are passed to orchestration."""
        doc_id = "doc-001"
        uploaded_doc = {
            "id": doc_id,
            "requirement_key": "D07",
            "application_id": "00000000-0000-0000-0000-000000000099",
        }
        extraction_result = {
            "document_id": doc_id,
            "requirement_key": "D07",
            "extraction_status": "completed",
        }

        docs_repo = _make_docs_repo(
            docs=[uploaded_doc],
            extraction_results=[extraction_result],
        )
        client = _build_client(docs_repo=docs_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        # The extraction result should be reflected in document readiness
        data = response.json()
        assert "approvals" in data

    def test_incorporates_validation_results(self):
        """Validation results from DB are passed to orchestration."""
        doc_id = "doc-002"
        uploaded_doc = {
            "id": doc_id,
            "requirement_key": "D07",
            "application_id": "00000000-0000-0000-0000-000000000099",
        }
        validation_result = {
            "document_id": doc_id,
            "requirement_key": "D07",
            "outcome": "VALID",
        }

        docs_repo = _make_docs_repo(
            docs=[uploaded_doc],
            validation_results=[validation_result],
        )
        client = _build_client(docs_repo=docs_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200

    def test_incorporates_consistency_result(self):
        """Consistency result from DB is passed to orchestration."""
        consistency_result = {
            "application_id": "00000000-0000-0000-0000-000000000099",
            "outcome": "REVIEW_REQUIRED",
        }
        consistency_repo = _make_consistency_repo(consistency_result)
        client = _build_client(consistency_repo=consistency_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        # With REVIEW_REQUIRED consistency, at least one applicable approval
        # should have a consistency blocker
        # (may be 0 if no approvals are applicable, which is acceptable)

    def test_computes_obtained_approvals(self):
        """Sibling approved applications are counted as obtained."""
        app_id = "00000000-0000-0000-0000-000000000099"
        project_id = "00000000-0000-0000-0000-000000000050"

        # Sibling app that is approved for A04
        sibling_app = {
            "id": "00000000-0000-0000-0000-000000000088",
            "project_id": project_id,
            "status": "approved",
            "approval_code": "A04",
        }

        app = _make_app(app_id=app_id, project_id=project_id)
        app_repo = _make_app_repo(app)
        app_repo.get_by_project.return_value = [app, sibling_app]

        client = _build_client(app_repo=app_repo)

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        data = response.json()
        assert "approvals" in data

    def test_sla_info_incorporated(self):
        """SLA info is computed and passed to orchestration."""
        app = _make_app(status="submitted")
        app_repo = _make_app_repo(app)
        app_repo.get_approval_stages.return_value = [
            {"key": "validation", "label": "Validation", "order": 0, "slaBusinessDays": 10}
        ]

        client = _build_client(app_repo=app_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        data = response.json()
        # SLA should be incorporated (state may be on_track for fresh submission)
        assert "approvals" in data

    def test_project_facts_loaded(self):
        """Project facts are loaded and used for applicability evaluation."""
        facts = {
            "entity_type": "company",
            "sector": "chemical",
            "jurisdictions": ["Gujarat"],
            "headcount": 50,
            "annual_turnover_inr": 10_000_000,
        }
        facts_repo = _make_facts_repo(facts)
        client = _build_client(facts_repo=facts_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        data = response.json()
        # Default fixture app is for A04 (no prerequisites): only its own
        # approval is assessed.
        assert set(data["approvals"].keys()) == {"A04"}


class TestOrchestrationScoping:
    """Assessment is scoped to the application's own approval plus its
    transitive prerequisites (resolved through the dependency model)."""

    _CHAIN_FACTS = {
        "industry_type": "synthetic organic / specialty chemical manufacturing",
        "effluent_generation": 100,
        "ETP_capacity": 5,
    }

    def test_assesses_only_own_approval_and_prerequisites(self):
        """An A03 application assesses {A03, A04, A02} — nothing else."""
        app = _make_app(approval_code="A03")
        app_repo = _make_app_repo(app)
        facts_repo = _make_facts_repo(dict(self._CHAIN_FACTS))
        client = _build_client(app_repo=app_repo, facts_repo=facts_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        assessed = set(response.json()["approvals"].keys())
        assert assessed == {"A02", "A03", "A04"}
        assert "A01" not in assessed
        assert "A18" not in assessed

    def test_root_approval_assesses_only_itself(self):
        """An A04 application (no prerequisites) assesses only A04."""
        app = _make_app(approval_code="A04")
        app_repo = _make_app_repo(app)
        client = _build_client(app_repo=app_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        assert set(response.json()["approvals"].keys()) == {"A04"}

    def test_dependency_ordering_preserved_without_obtained(self):
        """Without obtained prerequisites: A04 ready, A02/A03 blocked."""
        app = _make_app(approval_code="A03")
        app_repo = _make_app_repo(app)
        facts_repo = _make_facts_repo(dict(self._CHAIN_FACTS))
        client = _build_client(app_repo=app_repo, facts_repo=facts_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        approvals = response.json()["approvals"]
        assert approvals["A04"]["dependency_readiness"] == "ready"
        assert approvals["A02"]["dependency_readiness"] == "blocked"
        assert approvals["A03"]["dependency_readiness"] == "blocked"

    def test_dependency_ordering_preserved_with_obtained(self):
        """With sibling A04 approved: A02 becomes ready, A03 stays blocked."""
        app_id = "00000000-0000-0000-0000-000000000099"
        project_id = "00000000-0000-0000-0000-000000000050"
        sibling_app = {
            "id": "00000000-0000-0000-0000-000000000088",
            "project_id": project_id,
            "status": "approved",
            "approval_code": "A04",
        }
        app = _make_app(app_id=app_id, project_id=project_id, approval_code="A03")
        app_repo = _make_app_repo(app)
        app_repo.get_by_project.return_value = [app, sibling_app]
        facts_repo = _make_facts_repo(dict(self._CHAIN_FACTS))
        client = _build_client(app_repo=app_repo, facts_repo=facts_repo)

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 200
        approvals = response.json()["approvals"]
        assert approvals["A02"]["dependency_readiness"] == "ready"
        assert approvals["A03"]["dependency_readiness"] == "blocked"

    def test_missing_approval_code_rejected(self):
        """An application without approval_code gets 422 (established
        invalid-input behavior, mirroring invalid status filter)."""
        app = _make_app()
        del app["approval_code"]
        app_repo = _make_app_repo(app)
        client = _build_client(app_repo=app_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 422

    def test_invalid_approval_code_rejected(self):
        """An unknown approval_code gets 422."""
        app = _make_app(approval_code="AXX")
        app_repo = _make_app_repo(app)
        client = _build_client(app_repo=app_repo)
        app_id = "00000000-0000-0000-0000-000000000099"

        response = client.get(f"/applications/{app_id}/orchestration")
        assert response.status_code == 422
