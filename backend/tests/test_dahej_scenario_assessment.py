"""Canonical Dahej chemical-project scenario end-to-end assessment.

Uses ONLY the frozen workbook scenario facts (app.seed.scenario) unchanged.
Runs the real flow — applicability -> evidence boundary -> dependencies ->
documents -> orchestration — over all 18 approvals and pins the resulting
assessment. Any change to scenario facts, rules, dependencies, document
requirements, or evidence hints breaks these tests by design.
"""
from __future__ import annotations

from app.orchestration.service import orchestrate_application_full
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.dependencies import load_approval_dependencies
from app.seed.documents import load_document_requirements
from app.seed.evidence_gaps import get_gaps_for_approval
from app.seed.scenario import load_scenario

_ALL_CODES = [f"A{i:02d}" for i in range(1, 19)]

_EXPECTED_APPLICABILITY = {
    "A01": "applies",
    "A02": "applies",
    "A03": "applies",
    "A04": "applies",
    "A05": "applies",
    "A06": "applies",
    "A07": "applies",
    "A08": "applies",
    "A09": "applies",
    "A10": "applies",
    "A11": "applies",
    "A12": "applies",
    "A13": "applies",
    "A14": "applies",
    "A15": "applies",
    "A16": "applies",
    "A17": "applies",
    "A18": "does_not_apply",
}

# Derived from the deterministic engines + verified hint mapping only.
_EXPECTED_STATUS = {
    "A01": "insufficient_data",  # CGDCR-CONSOL + GIDC-GDCR gaps
    "A02": "insufficient_data",  # GIDC-GDCR gap (would be blocked by A04)
    "A03": "insufficient_data",  # GIDC-GDCR gap (would be blocked by deps)
    "A04": "blocked_by_documents",  # D05/D07/D08 required, none uploaded
    "A05": "ready",
    "A06": "insufficient_data",  # FIRE-R25 + FIRE-RENEWAL gaps
    "A07": "insufficient_data",  # OSH-01 gap
    "A08": "ready",
    "A09": "insufficient_data",  # ELEC-VOLTAGE gap
    "A10": "insufficient_data",  # ELEC-VOLTAGE gap
    "A11": "ready",
    "A12": "insufficient_data",  # MSIHC-AUTHORITY gap
    "A13": "blocked_by_documents",  # D11 required, none uploaded
    "A14": "insufficient_data",  # CGDCR-CONSOL gap
    "A15": "insufficient_data",  # LIFT-RULES gap
    "A16": "ready",
    "A17": "ready",
    "A18": "not_applicable",  # groundwater_use is False; gaps preserved, not decisive
}


def _assess_all():
    facts = load_scenario()
    return orchestrate_application_full(
        application_id="APP-DAHEJ",
        project_facts=facts,
        approval_rules=load_approval_rules(),
        approval_authorities=load_approval_authorities(),
        dependencies=load_approval_dependencies(),
        all_approval_ids=list(_ALL_CODES),
        document_requirements=load_document_requirements(),
        uploaded_documents=[],
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=set(),
        evidence_gaps_by_approval={
            aid: get_gaps_for_approval(aid) for aid in _ALL_CODES
        },
    )


class TestDahejScenarioFactsFrozen:
    def test_canonical_facts_unchanged(self):
        facts = load_scenario()
        assert facts["state"] == "Gujarat"
        assert facts["estate"] == "Dahej-II"
        assert facts["district"] == "Bharuch"
        assert facts["taluka"] == "Vagra"
        assert facts["village"] == "Dahej"
        assert facts["plot_area_sqm"] == 12000
        assert facts["builtup_area_sqm"] == 5000
        assert (
            facts["industry_type"]
            == "synthetic organic / specialty chemical manufacturing"
        )
        assert facts["new_project"] is True
        assert facts["production_capacity"] == 20000
        assert facts["max_storage_by_chemical"] == {
            "Methanol": "25 MT",
            "Toluene": "20 MT",
            "EDC": "15 MT",
            "THF": "10 MT",
            "Nitrobenzene": "10 MT",
        }
        assert facts["hazardous_waste_generated"] is True
        assert facts["water_source"] == "GIDC industrial water"
        assert facts["fresh_water_requirement"] == 100
        assert facts["process_water"] == 70
        assert facts["domestic_water"] == 30
        assert facts["effluent_generation"] == 70
        assert facts["ETP_capacity"] == 80
        assert facts["power_demand"] == 1000
        assert facts["DG_capacity"] == 750
        assert facts["workers_total"] == 60
        assert facts["hazardous_process"] is True
        assert facts["building_height"] == 18
        assert facts["lift_present"] is True
        assert facts["boiler_present"] is True
        assert facts["groundwater_use"] is False
        assert facts["tree_felling"] is False
        assert facts["forest_or_protected_area_overlap"] == "UNRESOLVED_AT_PLOT_LEVEL"
        assert facts["critical_pollution_area_status"] == "UNRESOLVED_AT_PLOT_LEVEL"
        assert facts["coastal_regulation_zone_status"] == "UNRESOLVED_AT_PLOT_LEVEL"
        assert facts["notified_industrial_area"] == "UNRESOLVED_AT_PLOT_LEVEL"
        assert facts["legal_entity"] == "Pvt Ltd"


class TestDahejEndToEndAssessment:
    def test_all_18_approvals_represented(self):
        result = _assess_all()
        assert set(result.approvals.keys()) == set(_ALL_CODES)

    def test_applicability_results(self):
        result = _assess_all()
        for code, expected in _EXPECTED_APPLICABILITY.items():
            assert result.approvals[code].applicability_result == expected, code

    def test_orchestration_statuses(self):
        result = _assess_all()
        for code, expected in _EXPECTED_STATUS.items():
            assert result.approvals[code].status.value == expected, code

    def test_overall_status_is_worst_case(self):
        result = _assess_all()
        assert result.overall_status.value == "blocked_by_documents"
        total = sum(len(o.blockers) for o in result.approvals.values())
        assert result.total_blockers == total
        assert total > 0


class TestDahejEvidenceSurfacing:
    def test_gap_affected_approvals_carry_structured_evidence_blockers(self):
        result = _assess_all()
        a06_ids = {
            b.evidence_id
            for b in result.approvals["A06"].blockers
            if b.blocker_type.value == "insufficient_data"
        }
        assert a06_ids == {"G0R5-FIRE-R25", "G0R5-FIRE-RENEWAL"}
        a01_ids = {
            b.evidence_id
            for b in result.approvals["A01"].blockers
            if b.blocker_type.value == "insufficient_data"
        }
        assert a01_ids == {"G0R5-CGDCR-CONSOL", "G0R5-GIDC-GDCR"}
        for code in ("A01", "A06"):
            for blocker in result.approvals[code].blockers:
                if blocker.blocker_type.value != "insufficient_data":
                    continue
                assert blocker.evidence_status in (
                    "PARTIAL",
                    "NOT_ESTABLISHED",
                    "CONFLICTING",
                )
                assert blocker.unresolved_question.strip() != ""
                assert blocker.source_ref.strip() != ""
                assert blocker.evidence.strip() != ""
                assert blocker.action_required.strip() != ""

    def test_no_extraction_is_not_converted_to_no_noc(self):
        """A18 stays NOT_APPLICABLE on does_not_apply; the GW gap blockers
        are attached but decisively inert — no 'no NOC required' conclusion."""
        result = _assess_all()
        a18 = result.approvals["A18"]
        assert a18.applicability_result == "does_not_apply"
        assert a18.status.value == "not_applicable"
        # No relief conclusion may be fabricated: the gap text itself only
        # scopes the duty ("abstracting ground water") and denies the mapping.
        assert "no NOC required" not in a18.explanation
        assert "NOC not required" not in a18.explanation
        for blocker in a18.blockers:
            if blocker.blocker_type.value != "insufficient_data":
                continue
            assert blocker.evidence_status in ("PARTIAL", "NOT_ESTABLISHED")

    def test_unmapped_ready_approvals_have_no_evidence_blockers(self):
        result = _assess_all()
        for code in ("A05", "A08", "A11", "A16", "A17"):
            assert result.approvals[code].status.value == "ready", code
            assert all(
                b.blocker_type.value != "insufficient_data"
                for b in result.approvals[code].blockers
            ), code

    def test_every_assessment_is_traceable(self):
        result = _assess_all()
        assert result.explanation.strip() != ""
        for code, orch in result.approvals.items():
            assert orch.explanation.strip() != "", code
            for blocker in orch.blockers:
                assert blocker.description.strip() != "", code
                assert blocker.source_ref.strip() != "", code
