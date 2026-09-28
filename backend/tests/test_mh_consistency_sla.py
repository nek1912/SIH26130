"""MH consistency (explicitly empty) + SLA display metadata (Phase 6).

Consistency: the v5 pack contains no cross-document consistency
records for the batch-1 documents (register-wide search: zero hits),
so nothing is transcribed — inventing checks would be fabrication.

SLA: 10 display-only rows referenced by batch-1 rule timelines.
Target and outer limit are never merged; UNKNOWN/"-"/NOT_STATED are
preserved; no deadline is computed from these records.
"""
from __future__ import annotations

import dataclasses

from app.orchestration.service import orchestrate_application_full
from app.seed.mh.consistency import (
    MH_DEFERRED_CONSISTENCY_NOTE,
    load_mh_consistency_rules,
)
from app.seed.mh.slas import (
    MH_DEFERRED_SLAS,
    MH_LOADED_SLA_IDS,
    load_mh_sla_records,
)
from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack
from app.workflow.sla import SlaMetadata


class TestMHConsistencyEmpty:
    def test_no_consistency_records_transcribed(self):
        assert load_mh_consistency_rules() == []

    def test_deferral_reason_documented(self):
        assert "Zero hits" in MH_DEFERRED_CONSISTENCY_NOTE or (
            "zero hits" in MH_DEFERRED_CONSISTENCY_NOTE.lower()
        )

    def test_mh_pack_consistency_empty(self):
        assert load_regulatory_pack(IN_MH).consistency_rules == []

    def test_gj_consistency_unchanged(self):
        from app.seed.consistency import load_consistency_rules

        assert len(load_consistency_rules()) == 18
        assert {r.id for r in load_consistency_rules()} == {
            f"C{i:02d}" for i in range(1, 19)
        }

    def test_no_gj_consistency_ids_in_mh(self):
        gj_ids = {"C01", "D01"}
        assert gj_ids.isdisjoint(
            {r.id for r in load_regulatory_pack(IN_MH).consistency_rules}
        )


class TestMHSLACorpus:
    def test_10_rows_loaded(self):
        records = load_mh_sla_records()
        assert len(records) == 10
        assert {r.sla_id for r in records} == set(MH_LOADED_SLA_IDS)
        assert MH_LOADED_SLA_IDS == {
            "SLA-004", "SLA-008", "SLA-011", "SLA-012", "SLA-013",
            "SLA-031", "SLA-032", "SLA-040", "SLA-045", "SLA-047",
        }

    def test_deferred_slas_documented(self):
        assert set(MH_DEFERRED_SLAS) == {"SLA-009", "SLA-029", "SLA-039"}

    def test_values_verbatim(self):
        by_id = {r.sla_id: r for r in load_mh_sla_records()}
        assert by_id["SLA-004"].target_value == "120"
        assert by_id["SLA-004"].target_unit == "DAYS"
        assert by_id["SLA-004"].clock_start == (
            "Receipt of complete application"
        )
        assert by_id["SLA-045"].target_unit == "MONTHS"
        assert by_id["SLA-008"].clock_start == "RTS"
        # UNKNOWN / "-" preserved, never substituted.
        assert by_id["SLA-031"].target_value == "NOT_STATED"
        assert by_id["SLA-031"].target_unit == "-"
        assert by_id["SLA-031"].clock_start == "-"
        assert by_id["SLA-031"].final_status == "UNKNOWN"
        assert by_id["SLA-032"].target_value == "UNKNOWN"
        assert by_id["SLA-032"].final_status == "UNKNOWN"
        # ROC travels with the record (display blocks nothing).
        assert by_id["SLA-013"].final_status == (
            "REQUIRES_OFFICIAL_CONFIRMATION"
        )
        assert "CON-008" == by_id["SLA-013"].conflict_id

    def test_working_day_semantics_not_converted(self):
        by_id = {r.sla_id: r for r in load_mh_sla_records()}
        assert by_id["SLA-004"].target_unit == "DAYS"
        assert by_id["SLA-004"].timeline_type == "LEGAL"
        assert by_id["SLA-008"].timeline_type == "RTS/SERVICE"
        assert by_id["SLA-040"].timeline_type == "LEGAL"
        assert by_id["SLA-047"].timeline_type == "PORTAL"

    def test_sla_sources_resolve(self):
        source_ids = {
            s.id for s in load_regulatory_pack(IN_MH).sources
        }
        for record in load_mh_sla_records():
            assert set(record.source_ids) <= source_ids, record.sla_id

    def test_sla_approvals_are_batch_approvals(self):
        pack = load_regulatory_pack(IN_MH)
        batch = {r.approval_id for r in pack.approval_rules}
        for record in pack.sla_records:
            assert record.approval_id in batch, record.sla_id


class TestDualDisplay:
    def test_statute_and_portal_rows_coexist_unmerged(self):
        by_id = {r.sla_id: r for r in load_mh_sla_records()}
        statute, portal = by_id["SLA-040"], by_id["SLA-047"]
        assert statute.sla_source_type == "STATUTE"
        assert portal.sla_source_type.startswith("PORTAL")
        assert statute.target_value != portal.target_value
        assert statute.conflict_id == portal.conflict_id == "CON-020"

    def test_target_outer_fields_independent(self):
        # Mechanism test on the model (synthetic outer values, clearly
        # not pack data): the two fields coexist and serialize apart.
        record = SlaMetadata(
            sla_id="SYN", approval_id="APR-010", service="synthetic",
            target_value="15", target_unit="WORKING_DAYS",
            outer_value="30", outer_unit="DAYS",
        )
        assert record.target_value != record.outer_value
        assert record.target_unit != record.outer_unit
        dumped = dataclasses.asdict(record)
        assert dumped["target_value"] == "15"
        assert dumped["outer_value"] == "30"
        # All real batch-1 rows carry target only (no outer invented).
        for real in load_mh_sla_records():
            assert real.outer_value is None, real.sla_id
            assert real.outer_unit is None, real.sla_id

    def test_pack_serialization_keeps_both_dimensions(self):
        pack = load_regulatory_pack(IN_MH)
        dumped = [dataclasses.asdict(r) for r in pack.sla_records]
        assert len(dumped) == 10
        by_id = {d["sla_id"]: d for d in dumped}
        assert by_id["SLA-040"]["timeline_type"] == "LEGAL"
        assert by_id["SLA-047"]["timeline_type"] == "PORTAL"


class TestPackIntegration:
    def test_mh_pack_serves_sla_records(self):
        pack = load_regulatory_pack(IN_MH)
        assert [r.sla_id for r in pack.sla_records] == [
            r.sla_id for r in load_mh_sla_records()
        ]

    def test_gj_pack_has_empty_sla_dimension(self):
        assert load_regulatory_pack(IN_GJ).sla_records == []


class TestDecisionRegression:
    def _run(self, facts):
        pack = load_regulatory_pack(IN_MH)
        aids = sorted({r.approval_id for r in pack.approval_rules})
        return orchestrate_application_full(
            application_id="MH-P6",
            project_facts=dict(facts),
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=aids,
            document_requirements=pack.document_requirements,
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval={
                aid: pack.get_gaps_for_approval(aid) for aid in aids
            },
        )

    def test_apr006_ready(self):
        orch = self._run(
            {"F-PRD-02": ["PESTICIDE_TECHNICAL"]}
        ).approvals["APR-006"]
        assert orch.applicability_result == "applies"
        assert orch.status.value == "ready"

    def test_apr010_dependency_blocked(self):
        orch = self._run({"F-HW-01": True}).approvals["APR-010"]
        assert orch.status.value == "blocked_by_dependency"

    def test_apr026_document_blocked(self):
        orch = self._run(
            {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 900}
        ).approvals["APR-026"]
        assert orch.status.value == "blocked_by_documents"

    def test_apr001_evidence_fail_closed(self):
        orch = self._run(
            {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False}
        ).approvals["APR-001"]
        assert orch.applicability_result == "applies"
        assert orch.status.value == "insufficient_data"

    def test_apr003_does_not_apply(self):
        orch = self._run({"F-BLD-01": 1000}).approvals["APR-003"]
        assert orch.status.value == "not_applicable"
        assert orch.blockers == []

    def test_empty_facts_insufficient(self):
        orch = self._run({}).approvals["APR-010"]
        assert orch.applicability_result == "insufficient_data"
        assert orch.applicability_result != "does_not_apply"
