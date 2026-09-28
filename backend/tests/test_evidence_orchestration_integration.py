"""Integration: verified G0-R5 evidence boundary in the approval path.

Covers the orchestration-path integration (not the boundary itself,
which is locked by test_evidence_gaps.py):
- B: relevant CONFLICTING gap -> INSUFFICIENT_DATA
- C: relevant NOT_ESTABLISHED gap -> INSUFFICIENT_DATA
- D: unrelated gaps never block unrelated approvals (hint mapping +
  per-approval surfacing, including the live endpoint)
- G: blockers carry machine-readable evidence traceability
- Endpoint: GET /applications/{id}/orchestration surfaces relevant gaps
"""
from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.orchestration import router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.orchestration.service import (
    evidence_gaps_to_blockers,
    orchestrate_application,
    orchestrate_application_full,
)
from app.regulatory.evidence import EvidenceStatus
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.dependencies import load_approval_dependencies
from app.seed.evidence_gaps import get_gaps_for_approval, load_evidence_gaps

_FIRE_FACTS = {"hazardous_process": True, "building_height": 10}
_CHEMICAL_FACTS = {"hazardous_chemicals_handled": True}
_A04_FACTS = {
    "industry_type": "synthetic organic / specialty chemical manufacturing",
}


def _gap(evidence_id: str):
    return next(g for g in load_evidence_gaps() if g.evidence_id == evidence_id)


def _orchestrate(approval_id: str, facts: dict, gaps: list | None, uploaded: list | None = None):
    return orchestrate_application(
        application_id="APP-INT",
        approval_id=approval_id,
        project_facts=facts,
        approval_rules=load_approval_rules(),
        approval_authorities=load_approval_authorities(),
        dependencies=load_approval_dependencies(),
        document_requirements=[],
        uploaded_documents=uploaded or [],
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=set(),
        evidence_gaps=gaps,
    )


class TestConflictingGapIntegration:
    def test_conflicting_gap_forces_insufficient_data(self):
        """B: relevant CONFLICTING gap -> INSUFFICIENT_DATA (A06/FIRE-RENEWAL)."""
        baseline = _orchestrate("A06", dict(_FIRE_FACTS), None)
        assert baseline.status.value == "ready"
        result = _orchestrate("A06", dict(_FIRE_FACTS), [_gap("G0R5-FIRE-RENEWAL")])
        assert result.status.value == "insufficient_data"
        assert any(
            b.blocker_type.value == "insufficient_data" for b in result.blockers
        )


class TestNotEstablishedGapIntegration:
    def test_not_established_gap_forces_insufficient_data(self):
        """C: relevant NOT_ESTABLISHED gap -> INSUFFICIENT_DATA (A12/MSIHC)."""
        uploaded = [{"requirement_key": "D11"}]
        baseline = _orchestrate("A12", dict(_CHEMICAL_FACTS), None, uploaded)
        assert baseline.status.value == "ready"
        result = _orchestrate(
            "A12", dict(_CHEMICAL_FACTS), [_gap("G0R5-MSIHC-AUTHORITY")], uploaded
        )
        assert result.status.value == "insufficient_data"


class TestHintMappingRelevance:
    def test_unmapped_approval_has_no_gaps(self):
        """D: hint mapping returns nothing for approvals without gaps (A04)."""
        assert get_gaps_for_approval("A04") == []

    def test_mapped_approval_returns_only_its_gaps(self):
        """D: A06 sees exactly the two fire gaps, nothing else."""
        ids = {g.evidence_id for g in get_gaps_for_approval("A06")}
        assert ids == {"G0R5-FIRE-R25", "G0R5-FIRE-RENEWAL"}

    def test_unmapped_gap_ids_stay_unsurfaced(self):
        """D: EODB/VGIP gaps map to no approval (hint-only, no invention)."""
        all_mapped = {
            g.evidence_id
            for code in ("A0" + str(n) for n in range(1, 10))
            for g in get_gaps_for_approval(code)
        } | {
            g.evidence_id
            for code in ("A10", "A11", "A12", "A13", "A14", "A15", "A16", "A17", "A18")
            for g in get_gaps_for_approval(code)
        }
        assert "G0R5-EODB-2026" not in all_mapped
        assert "G0R5-VGIP-2026" not in all_mapped

    def test_full_orchestration_only_affects_mapped_approvals(self):
        """D: hint-built map leaves A04 READY while A06 goes INSUFFICIENT."""
        facts = dict(_A04_FACTS) | dict(_FIRE_FACTS)
        uploaded = [
            {"requirement_key": "D05"},
            {"requirement_key": "D07"},
            {"requirement_key": "D08"},
        ]
        gaps_by_approval = {
            aid: get_gaps_for_approval(aid) for aid in ("A04", "A06")
        }
        result = orchestrate_application_full(
            application_id="APP-INT",
            project_facts=facts,
            approval_rules=load_approval_rules(),
            approval_authorities=load_approval_authorities(),
            dependencies=load_approval_dependencies(),
            all_approval_ids=["A04", "A06"],
            document_requirements=[],
            uploaded_documents=uploaded,
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval=gaps_by_approval,
        )
        assert result.approvals["A04"].status.value == "ready"
        assert all(
            b.blocker_type.value != "insufficient_data"
            for b in result.approvals["A04"].blockers
        )
        assert result.approvals["A06"].status.value == "insufficient_data"


class TestEvidenceTraceability:
    def test_gap_blocker_carries_structured_evidence_fields(self):
        """G: blocker exposes id, status, scope, question, source, action."""
        record = _gap("G0R5-FIRE-RENEWAL")
        assert record.status == EvidenceStatus.CONFLICTING
        (blocker,) = evidence_gaps_to_blockers([record], approval_id="A06")
        assert blocker.blocker_type.value == "insufficient_data"
        assert blocker.affected_approval_id == "A06"
        assert blocker.evidence_id == "G0R5-FIRE-RENEWAL"
        assert blocker.evidence_status == "CONFLICTING"
        assert blocker.unresolved_question == record.unresolved_question
        assert blocker.unresolved_question.strip() != ""
        assert blocker.source_ref == record.source_reference
        assert blocker.evidence == record.verified_scope
        assert "G0R5-FIRE-RENEWAL" in blocker.action_required


def _make_user() -> UserContext:
    return UserContext(
        user_id="00000000-0000-0000-0000-000000000001",
        email="test@test.com",
        role=SystemRole.APPLICANT,
        raw_claims={},
    )


def _make_app(approval_code: str = "A06") -> dict:
    return {
        "id": "00000000-0000-0000-0000-000000000099",
        "project_id": "00000000-0000-0000-0000-000000000050",
        "applicant_id": "00000000-0000-0000-0000-000000000001",
        "status": "draft",
        "approval_id": "00000000-0000-0000-0000-000000000100",
        "approval_code": approval_code,
        "reference_number": "APP-INT001",
        "current_stage": None,
        "submitted_at": None,
        "created_at": "2026-09-15T10:00:00Z",
        "jurisdiction": "IN-GJ",
        "pack_version": "gj-legacy-unversioned",
    }


def _build_client(
    app_dict: dict | None = None, facts: dict | None = None
) -> TestClient:
    from app.api.deps import (
        get_applications_repository,
        get_consistency_repository,
        get_documents_repository,
        get_project_facts_repository,
        get_workflow_events_repository,
    )

    fastapi_app = FastAPI()
    fastapi_app.include_router(router)
    fastapi_app.dependency_overrides[get_current_user] = _make_user

    app_repo = MagicMock(spec=ApplicationsRepository)
    app_repo.get_by_id.return_value = app_dict or _make_app()
    app_repo.get_by_project.return_value = [app_dict or _make_app()]
    app_repo.get_approval_stages.return_value = []

    facts_repo = MagicMock(spec=ProjectFactsRepository)
    facts_repo.get_by_project.return_value = facts

    docs_repo = MagicMock(spec=DocumentsRepository)
    docs_repo.list_documents_for_application.return_value = []

    events_repo = MagicMock(spec=WorkflowEventsRepository)
    events_repo.list_for_application.return_value = []

    consistency_repo = MagicMock(spec=ConsistencyRepository)
    consistency_repo.get_latest_result.return_value = None

    fastapi_app.dependency_overrides[get_applications_repository] = lambda: app_repo
    fastapi_app.dependency_overrides[get_project_facts_repository] = (
        lambda: facts_repo
    )
    fastapi_app.dependency_overrides[get_documents_repository] = lambda: docs_repo
    fastapi_app.dependency_overrides[get_workflow_events_repository] = (
        lambda: events_repo
    )
    fastapi_app.dependency_overrides[get_consistency_repository] = (
        lambda: consistency_repo
    )
    return TestClient(fastapi_app)


class TestEndpointEvidenceSurfacing:
    """The live orchestration path surfaces relevant gaps (A06) and
    leaves unmapped approvals (A04) unchanged."""

    _APP_ID = "00000000-0000-0000-0000-000000000099"

    def test_endpoint_surfaces_relevant_gap_as_insufficient_data(self):
        client = _build_client(_make_app("A06"), dict(_FIRE_FACTS))
        response = client.get(f"/applications/{self._APP_ID}/orchestration")
        assert response.status_code == 200
        approval = response.json()["approvals"]["A06"]
        assert approval["status"] == "insufficient_data"
        gap_blockers = [
            b
            for b in approval["blockers"]
            if b["blocker_type"] == "insufficient_data"
        ]
        assert len(gap_blockers) == 2
        assert {
            b["evidence_id"] for b in gap_blockers
        } == {"G0R5-FIRE-R25", "G0R5-FIRE-RENEWAL"}

    def test_endpoint_leaves_unmapped_approval_unchanged(self):
        client = _build_client(_make_app("A04"), dict(_A04_FACTS))
        response = client.get(f"/applications/{self._APP_ID}/orchestration")
        assert response.status_code == 200
        approvals = response.json()["approvals"]
        assert set(approvals.keys()) == {"A04"}
        assert approvals["A04"]["status"] != "insufficient_data"
        assert all(
            b["blocker_type"] != "insufficient_data"
            for b in approvals["A04"]["blockers"]
        )
