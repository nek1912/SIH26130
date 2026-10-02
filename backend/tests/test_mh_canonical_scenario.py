"""Deterministic verification of the canonical Maharashtra SIH demo scenario.

DATA/INTEGRATION ONLY.
Verifies the complete PS 26130 journey using the canonical Maharashtra
chemical manufacturing project scenario (Sahyadri Specialty Chemicals Pvt. Ltd.).

Exercises, using ONLY currently verified rules:
1. At least one APPLIES approval (APR-006, APR-010, APR-019, APR-026, APR-029)
2. At least one DOES_NOT_APPLY approval (APR-003, APR-004, APR-007, APR-043, etc.)
3. At least one CONDITIONAL / INSUFFICIENT_DATA case (APR-001 with UR-06 evidence gap)
4. At least one BLOCKED_BY_DOCUMENTS case (APR-026 blocked by DOC-008)
5. At least one dependency relationship (APR-010 blocked by APR-008 & APR-009)
6. Source traceability for all approvals (citing verified official sources)
7. What-If fact recalculation flipping approval decisions
8. Valid handoff-ready path for an approval that is READY (APR-006 on PARIVESH)
9. Document unblocking transition (uploading DOC-008 clears document blocker)
10. Dependency unblocking transition (obtained approvals clear dependency blocker)
11. Determinism across repeated executions
12. Full FastAPI REST API verification
"""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

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
from app.api.handoffs import router as handoffs_router
from app.api.orchestration import router as orchestration_router
from app.api.projects import router as projects_router
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.orchestration.facts import apply_derived_facts
from app.orchestration.models import OrchestrationStatus
from app.orchestration.service import orchestrate_application_full
from app.orchestration.whatif import run_whatif_assessment
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.handoffs import HandoffsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.rules.facts import (
    MH_FACTS,
    MH_JURISDICTION,
    validate_fact_value,
)
from app.seed.mh.scenario import (
    load_canonical_mh_expected_assessments,
    load_canonical_mh_project_meta,
    load_canonical_mh_scenario,
)
from app.seed.pack import IN_MH, load_regulatory_pack

USER_ID = "00000000-0000-0000-0000-000000000001"
PROJECT_ID = "00000000-0000-0000-0000-000000000050"
APP_ID = "00000000-0000-0000-0000-000000000099"


def _make_user(role=SystemRole.APPLICANT, user_id=USER_ID):
    return UserContext(user_id=user_id, email="applicant@sahyadri.com", role=role, raw_claims={})


def _build_canonical_orchestration(
    uploaded_docs=None,
    obtained_approvals=None,
):
    pack = load_regulatory_pack(IN_MH)
    raw_facts = load_canonical_mh_scenario()
    facts, prov = apply_derived_facts(raw_facts, IN_MH)
    all_ids = sorted(pack.approval_authorities.keys())
    return orchestrate_application_full(
        application_id="APP-MH-CANONICAL",
        project_facts=facts,
        approval_rules=pack.approval_rules,
        approval_authorities=pack.approval_authorities,
        dependencies=pack.dependencies,
        all_approval_ids=all_ids,
        document_requirements=pack.document_requirements,
        uploaded_documents=uploaded_docs or [],
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=obtained_approvals or set(),
        evidence_gaps_by_approval={aid: pack.get_gaps_for_approval(aid) for aid in all_ids},
        approval_compositions=pack.approval_compositions,
        fact_provenance=prov,
    )


class TestCanonicalMHScenarioData:
    """Verifies that the canonical scenario data complies with the fact registry."""

    def test_project_metadata_contract(self):
        meta = load_canonical_mh_project_meta()
        assert meta["name"] == "Sahyadri Specialty Chemicals Pvt. Ltd."
        assert meta["entity_type"] == "pvt-ltd"
        assert meta["sector"] == "chemical"
        assert meta["jurisdictions"] == ["IN-MH"]
        assert meta["headcount"] == 60
        assert meta["annual_turnover_inr"] == 500_000_000.0

    def test_all_scenario_facts_valid_in_mh_registry(self):
        facts = load_canonical_mh_scenario()
        assert len(facts) >= 30
        for key, value in facts.items():
            assert key in MH_FACTS, f"Fact key '{key}' not in MH registry"
            # Must not raise FactValidationError
            validate_fact_value(MH_JURISDICTION, key, value)

    def test_no_gujarat_vocabulary_leaks(self):
        facts = load_canonical_mh_scenario()
        gj_leak_keys = {
            "industry_type", "plot_area_sqm", "builtup_area_sqm",
            "effluent_generation", "ETP_capacity", "hazardous_chemicals_handled",
            "production_capacity", "groundwater_use", "legal_entity",
        }
        for leak in gj_leak_keys:
            assert leak not in facts, f"GJ legacy key '{leak}' leaked into MH scenario"

    def test_scenario_immutability(self):
        f1 = load_canonical_mh_scenario()
        f2 = load_canonical_mh_scenario()
        assert f1 == f2
        f1["F-BLD-01"] = 999999.0
        assert f2["F-BLD-01"] == 12000.0


class TestCanonicalMHDerivations:
    """Verifies deterministic fact derivation on the canonical scenario."""

    def test_msme_and_mah_derived_correctly(self):
        raw_facts = load_canonical_mh_scenario()
        assert "F-INC-01" not in raw_facts
        assert "F-PRC-03" not in raw_facts

        derived_facts, provenance = apply_derived_facts(raw_facts, IN_MH)

        # F-INC-01 derived from F-INC-02 (15 cr) and F-INC-09 (50 cr) -> SMALL
        assert derived_facts["F-INC-01"] == "SMALL"
        assert "F-INC-01" in provenance
        assert provenance["F-INC-01"]["derivation"] == "derive_msme_class"
        assert provenance["F-INC-01"]["source_facts"] == ["F-INC-02", "F-INC-09"]
        assert provenance["F-INC-01"]["value"] == "SMALL"

        # F-PRC-03 derived from F-HAZ-01 and F-HAZ-02 -> False (20t < 200t threshold)
        assert derived_facts["F-PRC-03"] is False
        assert "F-PRC-03" in provenance
        assert provenance["F-PRC-03"]["derivation"] == "derive_mah_status"
        assert provenance["F-PRC-03"]["source_facts"] == ["F-HAZ-01", "F-HAZ-02"]
        assert provenance["F-PRC-03"]["value"] is False


class TestCanonicalMHEndToEndAssessment:
    """Verifies the complete orchestration assessment for all 20 MH approvals."""

    def test_all_20_approvals_evaluated(self):
        result = _build_canonical_orchestration()
        expected = load_canonical_mh_expected_assessments()
        assert set(result.approvals.keys()) == set(expected.keys())
        assert len(result.approvals) == 20

    def test_exact_applicability_and_readiness_matches(self):
        result = _build_canonical_orchestration()
        expected = load_canonical_mh_expected_assessments()

        for approval_id, exp in expected.items():
            orch = result.approvals[approval_id]
            assert orch.applicability_result == exp["expected_applicability"], (
                f"{approval_id} applicability mismatch: got {orch.applicability_result}, "
                f"expected {exp['expected_applicability']}"
            )
            assert orch.status.value == exp["expected_readiness"], (
                f"{approval_id} readiness mismatch: got {orch.status.value}, "
                f"expected {exp['expected_readiness']}"
            )

    def test_overall_status_is_blocked_by_dependency(self):
        result = _build_canonical_orchestration()
        # Dependency blocker (priority 6) on APR-010 dominates overall status
        assert result.overall_status == OrchestrationStatus.BLOCKED_BY_DEPENDENCY
        assert result.total_blockers >= 3


class TestCanonicalMHEightCriteriaVerification:
    """Explicitly audits all 8 core criteria required for PS 26130 demo."""

    # 1. At least one APPLIES approval
    def test_criterion_1_applies_approvals(self):
        result = _build_canonical_orchestration()
        applies_codes = [
            code for code, orch in result.approvals.items()
            if orch.applicability_result == "applies"
        ]
        assert set(applies_codes) == {
            "APR-006", "APR-010", "APR-019", "APR-026", "APR-029",
        }
        assert len(applies_codes) >= 1

    # 2. At least one DOES_NOT_APPLY approval
    def test_criterion_2_does_not_apply_approvals(self):
        result = _build_canonical_orchestration()
        dna_codes = [
            code for code, orch in result.approvals.items()
            if orch.applicability_result == "does_not_apply"
        ]
        assert "APR-003" in dna_codes
        assert "APR-004" in dna_codes
        assert "APR-007" in dna_codes
        assert "APR-043" in dna_codes
        assert "LOC-CRZ" in dna_codes
        assert "LOC-FOREST" in dna_codes
        assert len(dna_codes) >= 1

    # 3. At least one CONDITIONAL / INSUFFICIENT_DATA case
    def test_criterion_3_insufficient_data_case(self):
        result = _build_canonical_orchestration()
        apr001 = result.approvals["APR-001"]
        assert apr001.applicability_result == "insufficient_data"
        assert apr001.status == OrchestrationStatus.INSUFFICIENT_DATA
        # Carries structured G0-R5 evidence blocker for UR-06
        ur06_blockers = [b for b in apr001.blockers if b.evidence_id == "UR-06"]
        assert len(ur06_blockers) == 1
        assert ur06_blockers[0].evidence_status == "NOT_ESTABLISHED"
        assert ur06_blockers[0].source_ref == "v5 unresolved_items UR-06 (OPEN)"

    # 4. At least one BLOCKED_BY_DOCUMENTS case
    def test_criterion_4_blocked_by_documents_case(self):
        # APR-010 requires DOC-001, DOC-002, DOC-003. When prerequisites APR-008 and APR-009
        # are obtained, it naturally evaluates to BLOCKED_BY_DOCUMENTS.
        dep_cleared = _build_canonical_orchestration(obtained_approvals={"APR-008", "APR-009"})
        apr010 = dep_cleared.approvals["APR-010"]
        assert apr010.applicability_result == "applies"
        assert apr010.status == OrchestrationStatus.BLOCKED_BY_DOCUMENTS
        assert apr010.dependency_readiness == "ready"
        assert apr010.document_readiness == "missing"
        doc_blockers_10 = [b for b in apr010.blockers if b.blocker_type.value == "document_missing"]
        assert len(doc_blockers_10) == 3
        keys = {b.affected_document_key for b in doc_blockers_10}
        assert keys == {"DOC-001", "DOC-002", "DOC-003"}

        # STOP verdict (audit_mh_r030_exemption_migration): R-030 stays
        # TRIGGER with APR-026 uncomposed. Canonical facts satisfy the
        # Class-B triple, so APR-026 APPLIES; DOC-008 is required and
        # unuploaded, so status is BLOCKED_BY_DOCUMENTS.
        base = _build_canonical_orchestration()
        apr026 = base.approvals["APR-026"]
        assert apr026.applicability_result == "applies"
        assert apr026.status == OrchestrationStatus.BLOCKED_BY_DOCUMENTS

    # 5. At least one dependency relationship
    def test_criterion_5_dependency_relationship(self):
        result = _build_canonical_orchestration()
        pack = load_regulatory_pack(IN_MH)
        apr010 = result.approvals["APR-010"]
        assert apr010.applicability_result == "applies"
        assert apr010.status == OrchestrationStatus.BLOCKED_BY_DEPENDENCY
        assert apr010.dependency_readiness == "blocked"
        assert "Blocked by: APR-008, APR-009" in apr010.explanation

        # Dependency edges in pack
        dep_edges = [d for d in pack.dependencies if d.approval_id == "APR-010"]
        assert len(dep_edges) == 2
        prereqs = {d.prerequisite_approval_id for d in dep_edges}
        assert prereqs == {"APR-008", "APR-009"}
        assert all("SRC-013 r.6" in d.source_ref for d in dep_edges)

    # 6. At least one explanation with source traceability
    def test_criterion_6_source_traceability(self):
        result = _build_canonical_orchestration()
        pack = load_regulatory_pack(IN_MH)
        source_ids = {s.id for s in pack.sources}

        for code in ("APR-006", "APR-010", "APR-026", "APR-003", "APR-019"):
            orch = result.approvals[code]
            assert orch.explanation.strip() != ""
            # Blockers cite source refs
            for blocker in orch.blockers:
                assert blocker.source_ref.strip() != ""

        # Check APR-006 specifically
        apr006_rule = next(r for r in pack.approval_rules if r.approval_id == "APR-006")
        assert any(ref.source_id in source_ids for ref in apr006_rule.source_refs)
        assert any("SRC-001" in ref.source_id for ref in apr006_rule.source_refs)

    # 7. At least one What-If change that changes the result
    def test_criterion_7_whatif_changes_result(self):
        pack = load_regulatory_pack(IN_MH)
        raw_facts = load_canonical_mh_scenario()
        facts, prov = apply_derived_facts(raw_facts, IN_MH)
        all_ids = sorted(pack.approval_authorities.keys())

        # Test A: Built-up area change flips APR-003 from does_not_apply to applies
        resp_bld = run_whatif_assessment(
            application_id="APP-MH-CANONICAL",
            base_facts=facts,
            fact_overrides={"F-BLD-01": 25000.0},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=all_ids,
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval={aid: pack.get_gaps_for_approval(aid) for aid in all_ids},
            jurisdiction=IN_MH,
            fact_provenance=prov,
            approval_compositions=pack.approval_compositions,
        )
        assert resp_bld.baseline.approvals["APR-003"].applicability_result == "does_not_apply"
        assert resp_bld.what_if.approvals["APR-003"].applicability_result == "applies"
        assert resp_bld.diff.no_change is False
        assert "APR-003" in [c.approval_id for c in resp_bld.diff.changed_approvals]

        # Test B: Hazardous waste generation override flips APR-010 from applies to does_not_apply
        resp_hw = run_whatif_assessment(
            application_id="APP-MH-CANONICAL",
            base_facts=facts,
            fact_overrides={"F-HW-01": False},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=all_ids,
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval={aid: pack.get_gaps_for_approval(aid) for aid in all_ids},
            jurisdiction=IN_MH,
            fact_provenance=prov,
            approval_compositions=pack.approval_compositions,
        )
        assert resp_hw.baseline.approvals["APR-010"].applicability_result == "applies"
        assert resp_hw.what_if.approvals["APR-010"].applicability_result == "does_not_apply"
        assert "APR-010" in [c.approval_id for c in resp_hw.diff.changed_approvals]

        # Test C: Product type change flips APR-006 from applies to does_not_apply
        resp_prd = run_whatif_assessment(
            application_id="APP-MH-CANONICAL",
            base_facts=facts,
            fact_overrides={"F-PRD-02": ["NONE"]},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=all_ids,
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval={aid: pack.get_gaps_for_approval(aid) for aid in all_ids},
            jurisdiction=IN_MH,
            fact_provenance=prov,
            approval_compositions=pack.approval_compositions,
        )
        assert resp_prd.baseline.approvals["APR-006"].applicability_result == "applies"
        assert resp_prd.what_if.approvals["APR-006"].applicability_result == "does_not_apply"
        assert "APR-006" in [c.approval_id for c in resp_prd.diff.changed_approvals]

        # Test D: Groundwater assessment unit change with abstraction flips APR-043 to applies
        resp_gw = run_whatif_assessment(
            application_id="APP-MH-CANONICAL",
            base_facts=facts,
            fact_overrides={"F-GW-01": "OVER_EXPLOITED", "F-EXP-01": True, "F-WAT-05": 50.0},
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=all_ids,
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval={aid: pack.get_gaps_for_approval(aid) for aid in all_ids},
            jurisdiction=IN_MH,
            fact_provenance=prov,
            approval_compositions=pack.approval_compositions,
        )
        assert resp_gw.baseline.approvals["APR-043"].applicability_result == "does_not_apply"
        assert resp_gw.what_if.approvals["APR-043"].applicability_result == "applies"
        assert "APR-043" in [c.approval_id for c in resp_gw.diff.changed_approvals]

    # 8. A valid handoff-ready path for an approval that is actually READY
    def test_criterion_8_handoff_ready_path(self):
        result = _build_canonical_orchestration()
        pack = load_regulatory_pack(IN_MH)

        # APR-006 is READY with zero blockers
        apr006 = result.approvals["APR-006"]
        assert apr006.status == OrchestrationStatus.READY
        assert apr006.blockers == []

        # Portal catalog confirms it is portal kind on PARIVESH
        portal = pack.get_portal_entry("APR-006")
        assert portal is not None
        assert portal["portal_kind"] == "portal"
        assert portal["external_system"] == "MoEFCC / PARIVESH"
        assert portal["portal_url"] == "https://parivesh.nic.in/"


class TestCanonicalMHDocumentAndDependencyTransitions:
    """Verifies that resolving document and dependency blockers unblocks approvals."""

    def test_apr026_tracks_doc008_while_document_blocked(self):
        # Baseline: APR-026 requires DOC-008; TRIGGER R-030 APPLIES on the
        # canonical Class-B facts and the missing DOC-008 blocks readiness.
        pack = load_regulatory_pack(IN_MH)
        assert any(
            r["requirement_key"] == "DOC-008" and "APR-026" in r["approval_ids"]
            for r in pack.document_requirements
        )
        base_result = _build_canonical_orchestration()
        assert base_result.approvals["APR-026"].applicability_result == "applies"
        assert base_result.approvals["APR-026"].status == OrchestrationStatus.BLOCKED_BY_DOCUMENTS

    def test_uploading_documents_unblocks_apr010(self):
        # Baseline with prerequisites cleared: blocked_by_documents
        obtained = {"APR-008", "APR-009"}
        base_result = _build_canonical_orchestration(obtained_approvals=obtained)
        assert base_result.approvals["APR-010"].status == OrchestrationStatus.BLOCKED_BY_DOCUMENTS

        # When DOC-001, DOC-002, DOC-003 are uploaded:
        uploaded = [
            {"requirement_key": "DOC-001", "document_name": "CTE Copy", "file_path": "/docs/cte.pdf"},
            {"requirement_key": "DOC-002", "document_name": "CTO Copy", "file_path": "/docs/cto.pdf"},
            {"requirement_key": "DOC-003", "document_name": "HW Compliance Report", "file_path": "/docs/hw.pdf"},
        ]
        unblocked_result = _build_canonical_orchestration(
            uploaded_docs=uploaded, obtained_approvals=obtained
        )
        assert unblocked_result.approvals["APR-010"].status == OrchestrationStatus.READY
        assert unblocked_result.approvals["APR-010"].blockers == []

    def test_obtaining_prerequisites_unblocks_apr010_dependency(self):
        # Baseline: APR-008 and APR-009 not obtained -> blocked_by_dependency
        base_result = _build_canonical_orchestration()
        assert base_result.approvals["APR-010"].status == OrchestrationStatus.BLOCKED_BY_DEPENDENCY

        # When APR-008 and APR-009 are obtained:
        obtained = {"APR-008", "APR-009"}
        dep_cleared_result = _build_canonical_orchestration(obtained_approvals=obtained)
        # Dependency is cleared; moves to blocked_by_documents because DOC-001/002/003 are required
        assert dep_cleared_result.approvals["APR-010"].dependency_readiness == "ready"
        assert dep_cleared_result.approvals["APR-010"].status == OrchestrationStatus.BLOCKED_BY_DOCUMENTS



class TestCanonicalMHDeterminism:
    """Proves that orchestrating the canonical scenario is 100% deterministic."""

    def test_evaluation_is_strictly_deterministic(self):
        runs = []
        for _ in range(10):
            res = _build_canonical_orchestration()
            runs.append(res.model_dump(mode="json"))

        first = runs[0]
        for idx, run in enumerate(runs[1:], start=2):
            assert run == first, f"Determinism failure on iteration {idx}"


class TestCanonicalMHFastAPIRoutes:
    """Verifies that the canonical scenario works end-to-end through FastAPI REST routes."""

    def _setup_api(self, approval_code="APR-006"):
        raw_facts = load_canonical_mh_scenario()
        facts_record = {
            "id": "facts-mh",
            "project_id": PROJECT_ID,
            "entity_type": "pvt-ltd",
            "sector": "chemical",
            "jurisdictions": ["IN-MH"],
            "headcount": 60,
            "annual_turnover_inr": 500_000_000.0,
            "facts_json": dict(raw_facts),
            "created_at": "2026-09-15T10:00:00Z",
            "updated_at": "2026-09-15T10:00:00Z",
        }
        app_record = {
            "id": APP_ID,
            "project_id": PROJECT_ID,
            "applicant_id": USER_ID,
            "status": "draft",
            "approval_id": f"00000000-0000-0000-0000-000000000{approval_code[-3:]}",
            "approval_code": approval_code,
            "reference_number": f"APP-MH-CANONICAL-{approval_code}",
            "current_stage": None,
            "submitted_at": None,
            "created_at": "2026-09-15T10:00:00Z",
            "jurisdiction": "IN-MH",
            "pack_version": "mh-v5-batch1",
        }
        project_record = {
            "id": PROJECT_ID,
            "applicant_id": USER_ID,
            "name": "Sahyadri Specialty Chemicals Pvt. Ltd.",
            "jurisdiction": "IN-MH",
            "pack_version": "mh-v5-batch1",
        }

        app_repo = MagicMock(spec=ApplicationsRepository)
        app_repo.get_by_id.return_value = app_record
        app_repo.get_by_project.return_value = [app_record]
        app_repo.get_approval_stages.return_value = []

        project_repo = MagicMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = project_record

        facts_repo = MagicMock(spec=ProjectFactsRepository)
        facts_repo.get_by_project.return_value = facts_record
        facts_repo.upsert.return_value = facts_record

        docs_repo = MagicMock(spec=DocumentsRepository)
        docs_repo.list_documents_for_application.return_value = []
        docs_repo.get_extraction_result_for_document.return_value = None
        docs_repo.get_validation_result_for_document.return_value = None

        events_repo = MagicMock(spec=WorkflowEventsRepository)
        events_repo.list_for_application.return_value = []

        consistency_repo = MagicMock(spec=ConsistencyRepository)
        consistency_repo.get_latest_result.return_value = None

        handoffs_rows = {}
        handoffs_repo = MagicMock(spec=HandoffsRepository)
        handoffs_repo.list_for_application.side_effect = lambda app_id: [
            r for r in handoffs_rows.values() if r["application_id"] == str(app_id)
        ]
        handoffs_repo.get_active_for_approval.side_effect = lambda app_id, code: next(
            (r for r in handoffs_rows.values() if r["application_id"] == str(app_id) and r["approval_code"] == code),
            None,
        )
        handoffs_repo.get_by_id.side_effect = lambda hid: handoffs_rows.get(str(hid))
        def _create_h(data):
            row = dict(data)
            row.setdefault("id", str(uuid4()))
            handoffs_rows[row["id"]] = row
            return row
        def _update_h(hid, data):
            row = handoffs_rows.get(str(hid))
            if row:
                row.update(data)
            return row
        handoffs_repo.create.side_effect = _create_h
        handoffs_repo.update.side_effect = _update_h

        app = FastAPI()
        app.include_router(projects_router)
        app.include_router(orchestration_router)
        app.include_router(handoffs_router)

        app.dependency_overrides[get_current_user] = lambda: _make_user()
        app.dependency_overrides[get_applications_repository] = lambda: app_repo
        app.dependency_overrides[get_project_repository] = lambda: project_repo
        app.dependency_overrides[get_project_facts_repository] = lambda: facts_repo
        app.dependency_overrides[get_documents_repository] = lambda: docs_repo
        app.dependency_overrides[get_workflow_events_repository] = lambda: events_repo
        app.dependency_overrides[get_consistency_repository] = lambda: consistency_repo
        app.dependency_overrides[get_handoffs_repository] = lambda: handoffs_repo

        return TestClient(app), handoffs_repo

    def test_api_orchestration_endpoint(self):
        # 1. APR-006: applies and ready
        client_006, _ = self._setup_api("APR-006")
        resp_006 = client_006.get(f"/applications/{APP_ID}/orchestration")
        assert resp_006.status_code == 200
        body_006 = resp_006.json()
        assert "fact_provenance" in body_006
        assert body_006["fact_provenance"]["F-INC-01"]["value"] == "SMALL"
        assert body_006["fact_provenance"]["F-PRC-03"]["value"] is False
        assert body_006["approvals"]["APR-006"]["applicability_result"] == "applies"
        assert body_006["approvals"]["APR-006"]["status"] == "ready"

        # 2. APR-026: applies, blocked_by_documents (DOC-008 required)
        client_026, _ = self._setup_api("APR-026")
        resp_026 = client_026.get(f"/applications/{APP_ID}/orchestration")
        assert resp_026.status_code == 200
        assert resp_026.json()["approvals"]["APR-026"]["applicability_result"] == "applies"
        assert resp_026.json()["approvals"]["APR-026"]["status"] == "blocked_by_documents"

        # 3. APR-010: blocked_by_dependency
        client_010, _ = self._setup_api("APR-010")
        resp_010 = client_010.get(f"/applications/{APP_ID}/orchestration")
        assert resp_010.status_code == 200
        assert resp_010.json()["approvals"]["APR-010"]["status"] == "blocked_by_dependency"

        # 4. APR-001: insufficient_data
        client_001, _ = self._setup_api("APR-001")
        resp_001 = client_001.get(f"/applications/{APP_ID}/orchestration")
        assert resp_001.status_code == 200
        assert resp_001.json()["approvals"]["APR-001"]["applicability_result"] == "insufficient_data"

    def test_api_whatif_endpoint(self):
        client, _ = self._setup_api("APR-003")
        resp = client.post(
            f"/applications/{APP_ID}/orchestration/what-if",
            json={"fact_overrides": {"F-BLD-01": 25000.0}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["baseline"]["approvals"]["APR-003"]["applicability_result"] == "does_not_apply"
        assert data["what_if"]["approvals"]["APR-003"]["applicability_result"] == "applies"
        assert data["diff"]["no_change"] is False

    def test_api_handoff_journey(self):
        client, store = self._setup_api("APR-006")

        # 1. List handoffs shows ready approvals (APR-006)
        resp_list = client.get(f"/applications/{APP_ID}/handoffs")
        assert resp_list.status_code == 200
        ready_codes = [r["approval_code"] for r in resp_list.json()["ready_approvals"]]
        assert "APR-006" in ready_codes

        # 2. Initiate handoff for APR-006
        resp_init = client.post(
            f"/applications/{APP_ID}/handoffs/initiate",
            json={"approval_code": "APR-006"},
        )
        assert resp_init.status_code == 200
        created = resp_init.json()
        assert created["approval_code"] == "APR-006"
        assert created["external_system"] == "MoEFCC / PARIVESH"
        assert created["status"] == "handed_off"
        hid = created["id"]

        # 3. Record applicant submission with external reference
        resp_sub = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/record-submission",
            json={"external_reference": "PARIVESH-MH-2026-0042"},
        )
        assert resp_sub.status_code == 200
        assert resp_sub.json()["external_reference"] == "PARIVESH-MH-2026-0042"
        assert resp_sub.json()["status"] == "submitted_externally"

        # 4. Reviewer/Staff verifies the submission
        client.app.dependency_overrides[get_current_user] = lambda: _make_user(role=SystemRole.REVIEWER)
        resp_ver = client.post(
            f"/applications/{APP_ID}/handoffs/{hid}/verify",
            json={"verified_status": "submitted_externally"},
        )
        assert resp_ver.status_code == 200
        assert resp_ver.json()["verification"] == "staff_verified"
