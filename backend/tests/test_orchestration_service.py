"""Comprehensive tests for the orchestration service.

Covers:
- Status computation (applicability, dependency, document, consistency, SLA)
- Document readiness (mandatory/conditional, valid/missing/invalid)
- Next action selection
- Full application orchestration (worst-case status, blocker count, next action)
- Edge cases (empty inputs, SLA breach)
"""
from __future__ import annotations

from app.orchestration.models import (
    ApplicationOrchestration,
    ApprovalOrchestration,
    OrchestrationStatus,
)
from app.orchestration.service import orchestrate_application, orchestrate_application_full
from app.rules.dependency_models import ApprovalDependency
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.dependencies import load_approval_dependencies



# Shared fixtures
_FULL_FACTS = {
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


def _rules():
    return load_approval_rules()


def _authorities():
    return load_approval_authorities()


def _deps():
    return load_approval_dependencies()


def _make_doc_req(requirement_key: str, approval_ids: list[str], level: str = "required"):
    return {
        "requirement_key": requirement_key,
        "document_name": f"Doc {requirement_key}",
        "approval_ids": approval_ids,
        "requirement_level": level,
        "source_basis": "test",
        "source_url": "",
    }


def _make_uploaded_doc(requirement_key: str, status: str = "valid"):
    return {
        "requirement_key": requirement_key,
        "status": status,
    }


def _call_orchestrate(
    approval_id: str,
    facts: dict | None = None,
    doc_reqs: list | None = None,
    uploaded: list | None = None,
    extraction: list | None = None,
    validation: list | None = None,
    consistency: dict | None = None,
    sla: dict | None = None,
    obtained: set[str] | None = None,
):
    """Helper to call orchestrate_application with sensible defaults."""
    return orchestrate_application(
        application_id="APP-TEST",
        approval_id=approval_id,
        project_facts=facts if facts is not None else _FULL_FACTS,
        approval_rules=_rules(),
        approval_authorities=_authorities(),
        dependencies=_deps(),
        document_requirements=doc_reqs if doc_reqs is not None else [],
        uploaded_documents=uploaded or [],
        extraction_results=extraction or [],
        validation_results=validation or [],
        consistency_result=consistency,
        sla_info=sla,
        obtained_approvals=obtained or set(),
    )


# ============================================================
# 1. TestOrchestrationStatusComputation
# ============================================================


class TestOrchestrationStatusComputation:
    def test_ready_when_all_clear(self):
        """Approval with applies + no deps + all docs valid = READY."""
        result = _call_orchestrate("A04")
        assert result.status == OrchestrationStatus.READY

    def test_blocked_by_dependency(self):
        """Approval blocked by unmet prerequisite = BLOCKED_BY_DEPENDENCY."""
        result = _call_orchestrate("A03", obtained=set())
        assert result.status == OrchestrationStatus.BLOCKED_BY_DEPENDENCY
        assert result.dependency_readiness == "blocked"
        assert result.next_action == "complete"

    def test_insufficient_data_when_facts_missing(self):
        """Missing project facts = INSUFFICIENT_DATA."""
        result = _call_orchestrate("A01", facts={})
        assert result.status == OrchestrationStatus.INSUFFICIENT_DATA

    def test_blocked_by_documents_when_missing(self):
        """Mandatory docs not uploaded = BLOCKED_BY_DOCUMENTS."""
        doc_reqs = [_make_doc_req("D05", ["A04"], level="required")]
        result = _call_orchestrate("A04", doc_reqs=doc_reqs, uploaded=[])
        assert result.status == OrchestrationStatus.BLOCKED_BY_DOCUMENTS

    def test_review_required_when_consistency_issues(self):
        """Consistency REVIEW_REQUIRED = REVIEW_REQUIRED."""
        result = _call_orchestrate("A04", consistency={"outcome": "REVIEW_REQUIRED"})
        assert result.status == OrchestrationStatus.REVIEW_REQUIRED

    def test_not_applicable_when_does_not_apply(self):
        """Applicability does_not_apply = NOT_APPLICABLE."""
        facts = {"state": "Gujarat", "industry_type": "textile manufacturing", "plot_area_sqm": 12000}
        result = _call_orchestrate("A01", facts=facts)
        assert result.status == OrchestrationStatus.NOT_APPLICABLE

    def test_dependency_chain_progression(self):
        """A04 -> A02 -> A03 chain resolves as approvals are obtained."""
        # A04: no deps, should be READY
        r_a04 = _call_orchestrate("A04")
        assert r_a04.status == OrchestrationStatus.READY

        # A02: depends on A04, with A04 obtained -> READY
        r_a02 = _call_orchestrate("A02", obtained={"A04"})
        assert r_a02.status == OrchestrationStatus.READY

        # A03: depends on A04 and A02, with both obtained -> READY
        r_a03 = _call_orchestrate("A03", obtained={"A04", "A02"})
        assert r_a03.status == OrchestrationStatus.READY
        assert r_a03.dependency_readiness == "ready"
        assert len(r_a03.blockers) == 0


# ============================================================
# 2. TestDocumentReadiness
# ============================================================


class TestDocumentReadiness:
    def test_all_docs_valid(self):
        """When all mandatory docs uploaded and valid."""
        doc_reqs = [_make_doc_req("D05", ["A04"], level="required")]
        uploaded = [_make_uploaded_doc("D05")]
        result = _call_orchestrate("A04", doc_reqs=doc_reqs, uploaded=uploaded)
        assert result.document_readiness == "all_valid"

    def test_mandatory_doc_missing(self):
        """When mandatory doc not uploaded."""
        doc_reqs = [_make_doc_req("D05", ["A04"], level="required")]
        result = _call_orchestrate("A04", doc_reqs=doc_reqs, uploaded=[])
        d05_summary = next(s for s in result.documents if s.requirement_key == "D05")
        assert d05_summary.blocking is True

    def test_conditional_doc_not_blocking(self):
        """Conditional doc missing is not a blocker."""
        doc_reqs = [_make_doc_req("D10", ["A11"], level="conditional")]
        result = _call_orchestrate(
            "A11",
            facts={**_FULL_FACTS, "hazardous_waste_generated": True},
            doc_reqs=doc_reqs,
            uploaded=[],
        )
        d10_summary = next(s for s in result.documents if s.requirement_key == "D10")
        assert d10_summary.blocking is False


# ============================================================
# 3. TestNextAction
# ============================================================


class TestNextAction:
    def test_next_action_upload_document(self):
        """First action is upload when docs missing."""
        doc_reqs = [_make_doc_req("D05", ["A04"], level="required")]
        result = _call_orchestrate("A04", doc_reqs=doc_reqs, uploaded=[])
        assert result.next_action == "upload_document"

    def test_next_action_validate_document(self):
        """After upload, validate."""
        doc_reqs = [_make_doc_req("D05", ["A04"], level="required")]
        uploaded = [_make_uploaded_doc("D05")]
        validation = [{"requirement_key": "D05", "outcome": "INVALID", "findings": []}]
        result = _call_orchestrate(
            "A04", doc_reqs=doc_reqs, uploaded=uploaded, validation=validation
        )
        assert result.next_action == "validate_document"


# ============================================================
# 4. TestApplicationOrchestration
# ============================================================


class TestApplicationOrchestration:
    def test_full_orchestration_overall_status(self):
        """Overall status is worst case across all approvals."""
        result = orchestrate_application_full(
            application_id="APP-TEST",
            project_facts=_FULL_FACTS,
            approval_rules=_rules(),
            approval_authorities=_authorities(),
            dependencies=_deps(),
            all_approval_ids=["A04", "A02", "A03"],
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
        )
        # A03 is blocked by dependency (A04 and A02 not obtained)
        assert result.overall_status == OrchestrationStatus.BLOCKED_BY_DEPENDENCY

    def test_full_orchestration_total_blockers(self):
        """Counts all blockers across approvals."""
        doc_reqs = [
            _make_doc_req("D05", ["A04"], level="required"),
            _make_doc_req("D01", ["A01"], level="required"),
        ]
        result = orchestrate_application_full(
            application_id="APP-TEST",
            project_facts=_FULL_FACTS,
            approval_rules=_rules(),
            approval_authorities=_authorities(),
            dependencies=_deps(),
            all_approval_ids=["A04", "A01"],
            document_requirements=doc_reqs,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
        )
        expected_blockers = 0
        for orch in result.approvals.values():
            expected_blockers += len(orch.blockers)
        assert result.total_blockers == expected_blockers

    def test_full_orchestration_next_action(self):
        """Picks highest priority next action across all approvals."""
        doc_reqs = [
            _make_doc_req("D05", ["A04"], level="required"),
            _make_doc_req("D01", ["A01"], level="required"),
        ]
        result = orchestrate_application_full(
            application_id="APP-TEST",
            project_facts=_FULL_FACTS,
            approval_rules=_rules(),
            approval_authorities=_authorities(),
            dependencies=_deps(),
            all_approval_ids=["A04", "A01"],
            document_requirements=doc_reqs,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
        )
        assert result.next_action is not None
        assert result.next_action.action_type == "upload_document"
        assert result.next_action.affected_approval_id in ("A04", "A01")


# ============================================================
# 5. TestEdgeCases
# ============================================================


class TestEdgeCases:
    def test_empty_inputs(self):
        """Empty everything doesn't crash."""
        result = orchestrate_application_full(
            application_id="APP-EMPTY",
            project_facts={},
            approval_rules=[],
            approval_authorities={},
            dependencies=[],
            all_approval_ids=[],
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
        )
        assert isinstance(result, ApplicationOrchestration)
        assert result.application_id == "APP-EMPTY"

    def test_sla_breached_adds_blocker(self):
        """Breached SLA adds blocker."""
        result = _call_orchestrate("A04", sla={"state": "breached"})
        sla_blockers = [b for b in result.blockers if "SLA" in b.description]
        assert len(sla_blockers) > 0
        assert result.status == OrchestrationStatus.REVIEW_REQUIRED
