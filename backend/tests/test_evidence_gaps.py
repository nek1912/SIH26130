"""G0-R5 regulatory evidence boundary tests (TDD RED).

Machine-readable evidence-status representation for unresolved regulatory
facts. Statuses: VERIFIED / PARTIAL / NOT_ESTABLISHED / CONFLICTING.

Source of truth:
- docs/approval-identity-verification.md (read-only, asserts nothing)
- Gap-Closure Pass G0-R5 Final evidence baseline (cut-off 25.09.2026)

Fail-closed invariants:
- No applicability rules from PARTIAL or NOT_ESTABLISHED evidence.
- No invented thresholds, authorities, SLAs, exemptions, legal conclusions.
- Existing verified rules keep working unchanged.
- Orchestration surfaces evidence gaps as INSUFFICIENT_DATA where relevant.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.regulatory.evidence import (
    EvidenceNotVerifiedError,
    EvidenceRecord,
    EvidenceStatus,
    gap_to_applicability_result,
    is_encodable,
    is_evidence_gap,
    require_verified,
)


def _load_gaps() -> list[EvidenceRecord]:
    from app.seed.evidence_gaps import load_evidence_gaps

    return load_evidence_gaps()


class TestEvidenceStatusEnum:
    def test_all_four_statuses_exist(self):
        assert EvidenceStatus.VERIFIED.value == "VERIFIED"
        assert EvidenceStatus.PARTIAL.value == "PARTIAL"
        assert EvidenceStatus.NOT_ESTABLISHED.value == "NOT_ESTABLISHED"
        assert EvidenceStatus.CONFLICTING.value == "CONFLICTING"

    def test_status_values_are_distinct(self):
        values = [s.value for s in EvidenceStatus]
        assert len(set(values)) == 4


class TestEvidenceRecordShape:
    def test_required_fields_present(self):
        rec = EvidenceRecord(
            evidence_id="G0R5-TEST",
            subject="test subject",
            status=EvidenceStatus.NOT_ESTABLISHED,
            verified_scope="what is verified",
            unresolved_question="what remains",
            source_reference="G0-R5 test",
        )
        assert rec.evidence_id == "G0R5-TEST"
        assert rec.effective_date is None
        assert rec.notes == ""
        assert rec.flags == []

    def test_machine_readable_dump_roundtrip(self):
        rec = EvidenceRecord(
            evidence_id="G0R5-TEST",
            subject="s",
            status=EvidenceStatus.PARTIAL,
            verified_scope="v",
            unresolved_question="u",
            source_reference="src",
            effective_date=date(2023, 3, 29),
            notes="n",
            flags=["f1"],
        )
        dumped = rec.model_dump()
        for key in (
            "evidence_id",
            "subject",
            "status",
            "verified_scope",
            "unresolved_question",
            "source_reference",
            "effective_date",
            "notes",
            "flags",
        ):
            assert key in dumped
        revived = EvidenceRecord.model_validate(dumped)
        assert revived == rec


class TestG0R5Register:
    def test_twelve_items(self):
        gaps = _load_gaps()
        assert len(gaps) == 12

    def test_evidence_ids_unique(self):
        gaps = _load_gaps()
        ids = [g.evidence_id for g in gaps]
        assert len(set(ids)) == 12

    def test_expected_ids_present(self):
        gaps = _load_gaps()
        ids = {g.evidence_id for g in gaps}
        assert ids == {
            "G0R5-OSH-01",
            "G0R5-FIRE-R25",
            "G0R5-FIRE-RENEWAL",
            "G0R5-EODB-2026",
            "G0R5-ELEC-VOLTAGE",
            "G0R5-CGDCR-CONSOL",
            "G0R5-GIDC-GDCR",
            "G0R5-GW-JURISDICTION",
            "G0R5-GW-NO-EXTRACTION",
            "G0R5-LIFT-RULES",
            "G0R5-MSIHC-AUTHORITY",
            "G0R5-VGIP-2026",
        }

    def test_no_verified_items_in_unresolved_register(self):
        # This register records UNRESOLVED facts only; nothing here may
        # claim VERIFIED (future verified facts live elsewhere).
        gaps = _load_gaps()
        for g in gaps:
            assert g.status != EvidenceStatus.VERIFIED, g.evidence_id

    def test_fire_renewal_is_conflicting(self):
        gaps = {g.evidence_id: g for g in _load_gaps()}
        rec = gaps["G0R5-FIRE-RENEWAL"]
        assert rec.status == EvidenceStatus.CONFLICTING
        # Must record both sides without resolving the conflict.
        assert "2" in rec.verified_scope
        assert "3" in rec.verified_scope

    def test_partial_items(self):
        gaps = {g.evidence_id: g for g in _load_gaps()}
        for eid in (
            "G0R5-OSH-01",
            "G0R5-FIRE-R25",
            "G0R5-GW-JURISDICTION",
            "G0R5-LIFT-RULES",
        ):
            assert gaps[eid].status == EvidenceStatus.PARTIAL, eid

    def test_not_established_items(self):
        gaps = {g.evidence_id: g for g in _load_gaps()}
        for eid in (
            "G0R5-EODB-2026",
            "G0R5-ELEC-VOLTAGE",
            "G0R5-CGDCR-CONSOL",
            "G0R5-GIDC-GDCR",
            "G0R5-GW-NO-EXTRACTION",
            "G0R5-MSIHC-AUTHORITY",
            "G0R5-VGIP-2026",
        ):
            assert gaps[eid].status == EvidenceStatus.NOT_ESTABLISHED, eid

    def test_no_extraction_rule_must_remain_not_established(self):
        gaps = {g.evidence_id: g for g in _load_gaps()}
        rec = gaps["G0R5-GW-NO-EXTRACTION"]
        assert rec.status == EvidenceStatus.NOT_ESTABLISHED
        assert "must remain" in rec.notes.lower() or any(
            "no_noc" in f or "must_remain" in f or "fail_closed" in f
            for f in rec.flags
        )

    def test_only_jurisdiction_has_effective_date(self):
        gaps = {g.evidence_id: g for g in _load_gaps()}
        assert gaps["G0R5-GW-JURISDICTION"].effective_date == date(2023, 3, 29)
        for eid, rec in gaps.items():
            if eid != "G0R5-GW-JURISDICTION":
                assert rec.effective_date is None, eid

    def test_every_item_has_traceability(self):
        gaps = _load_gaps()
        for g in gaps:
            assert g.subject.strip(), g.evidence_id
            assert g.verified_scope.strip(), g.evidence_id
            assert g.unresolved_question.strip(), g.evidence_id
            assert g.source_reference.strip(), g.evidence_id


class TestFailClosedGuards:
    def test_is_encodable_only_for_verified(self):
        verified = EvidenceRecord(
            evidence_id="X",
            subject="s",
            status=EvidenceStatus.VERIFIED,
            verified_scope="v",
            unresolved_question="",
            source_reference="src",
        )
        assert is_encodable(verified) is True
        for status in (
            EvidenceStatus.PARTIAL,
            EvidenceStatus.NOT_ESTABLISHED,
            EvidenceStatus.CONFLICTING,
        ):
            rec = EvidenceRecord(
                evidence_id="X",
                subject="s",
                status=status,
                verified_scope="v",
                unresolved_question="u",
                source_reference="src",
            )
            assert is_encodable(rec) is False

    def test_require_verified_raises_for_gaps(self):
        gaps = _load_gaps()
        for g in gaps:
            with pytest.raises(EvidenceNotVerifiedError):
                require_verified(g)

    def test_require_verified_passes_for_verified(self):
        rec = EvidenceRecord(
            evidence_id="X",
            subject="s",
            status=EvidenceStatus.VERIFIED,
            verified_scope="v",
            unresolved_question="",
            source_reference="src",
        )
        assert require_verified(rec) is rec

    def test_is_evidence_gap_true_for_all_register_items(self):
        for g in _load_gaps():
            assert is_evidence_gap(g) is True

    def test_gap_maps_to_insufficient_data(self):
        for g in _load_gaps():
            assert gap_to_applicability_result(g) == "insufficient_data"

    def test_verified_has_no_gap_result(self):
        rec = EvidenceRecord(
            evidence_id="X",
            subject="s",
            status=EvidenceStatus.VERIFIED,
            verified_scope="v",
            unresolved_question="",
            source_reference="src",
        )
        assert gap_to_applicability_result(rec) is None


class TestNoRulesFromGaps:
    def test_existing_approval_rules_unchanged(self):
        # G0-R5 must not change the verified rule count/shape.
        from app.seed.approvals import load_approval_rules

        rules = load_approval_rules()
        assert len(rules) == 19
        ids = {r.id for r in rules}
        assert "R-GIDC-001" in ids
        assert "R-CGWA-001" in ids

    def test_no_rule_claims_gap_evidence_as_verified(self):
        # No ApprovalRule may cite a G0-R5 gap evidence_id as its basis.
        from app.seed.approvals import load_approval_rules

        gap_ids = {g.evidence_id for g in _load_gaps()}
        for rule in load_approval_rules():
            for ref in rule.source_refs:
                assert ref.source_id not in gap_ids, rule.id


class TestOrchestrationSurfacesGaps:
    def test_gap_blocker_is_insufficient_data(self):
        from app.orchestration.service import evidence_gaps_to_blockers

        gaps = _load_gaps()
        blockers = evidence_gaps_to_blockers(gaps[:1], approval_id="A06")
        assert len(blockers) == 1
        assert blockers[0].blocker_type.value == "insufficient_data"
        assert blockers[0].affected_approval_id == "A06"

    def test_orchestration_goes_insufficient_with_relevant_gap(self):
        from app.orchestration.service import orchestrate_application
        from app.seed.approvals import (
            load_approval_authorities,
            load_approval_rules,
        )
        from app.seed.dependencies import load_approval_dependencies

        gaps = _load_gaps()
        fire_gap = [g for g in gaps if g.evidence_id == "G0R5-FIRE-R25"]
        result = orchestrate_application(
            application_id="APP-GAP",
            approval_id="A04",
            project_facts={
                "industry_type": "synthetic organic / specialty chemical manufacturing",
            },
            approval_rules=load_approval_rules(),
            approval_authorities=load_approval_authorities(),
            dependencies=load_approval_dependencies(),
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps=fire_gap,
        )
        assert result.status.value == "insufficient_data"
        assert any(
            b.blocker_type.value == "insufficient_data" for b in result.blockers
        )

    def test_orchestration_unchanged_without_gaps(self):
        # Existing verified behaviour preserved when no gaps supplied.
        from app.orchestration.service import orchestrate_application
        from app.seed.approvals import (
            load_approval_authorities,
            load_approval_rules,
        )
        from app.seed.dependencies import load_approval_dependencies

        result = orchestrate_application(
            application_id="APP-TEST",
            approval_id="A04",
            project_facts={
                "industry_type": "synthetic organic / specialty chemical manufacturing",
            },
            approval_rules=load_approval_rules(),
            approval_authorities=load_approval_authorities(),
            dependencies=load_approval_dependencies(),
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
        )
        assert result.status.value == "ready"

    def test_not_applicable_stays_not_applicable_with_gap(self):
        from app.orchestration.service import orchestrate_application
        from app.seed.approvals import (
            load_approval_authorities,
            load_approval_rules,
        )
        from app.seed.dependencies import load_approval_dependencies

        gaps = _load_gaps()
        result = orchestrate_application(
            application_id="APP-GAP-NA",
            approval_id="A01",
            project_facts={
                "industry_type": "textile manufacturing",
                "plot_area_sqm": 12000,
            },
            approval_rules=load_approval_rules(),
            approval_authorities=load_approval_authorities(),
            dependencies=load_approval_dependencies(),
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps=gaps[:1],
        )
        assert result.status.value == "not_applicable"
