"""Jurisdiction-aware regulatory loader boundary (Phase 1 scaffold).

IN-GJ must return the existing Gujarat data unchanged; IN-MH must be an
explicitly empty placeholder; unknown jurisdictions must fail loudly.
Runtime equivalence tests prove orchestration, What-If, impact
rehearsal, and handoff readiness consume identical regulatory inputs
through the pack boundary.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.orchestration.service import orchestrate_application_full
from app.orchestration.whatif import run_whatif_assessment
from app.regulatory.impact import RehearsalInputs
from app.seed.pack import (
    DEFAULT_JURISDICTION,
    IN_GJ,
    IN_MH,
    RegulatoryPack,
    UnknownJurisdictionError,
    load_regulatory_pack,
)


def _direct_gj_inputs():
    """Baseline inputs assembled from the individual GJ seed loaders."""
    from app.seed.approvals import load_approval_authorities, load_approval_rules
    from app.seed.dependencies import load_approval_dependencies
    from app.seed.documents import load_document_requirements
    from app.seed.evidence_gaps import get_gaps_for_approval
    from app.seed.scenario import load_scenario

    rules = load_approval_rules()
    return {
        "facts": load_scenario(),
        "rules": rules,
        "authorities": load_approval_authorities(),
        "dependencies": load_approval_dependencies(),
        "doc_requirements": load_document_requirements(),
        "gaps": {r.approval_id: get_gaps_for_approval(r.approval_id) for r in rules},
    }


def _orchestrate(inputs, approval_ids):
    return orchestrate_application_full(
        application_id="PACK-TEST",
        project_facts=dict(inputs["facts"]),
        approval_rules=inputs["rules"],
        approval_authorities=inputs["authorities"],
        dependencies=inputs["dependencies"],
        all_approval_ids=list(approval_ids),
        document_requirements=inputs["doc_requirements"],
        uploaded_documents=[],
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=set(),
        evidence_gaps_by_approval=inputs["gaps"],
    )


class TestLoadRegulatoryPack:
    def test_default_jurisdiction_is_gujarat(self):
        assert DEFAULT_JURISDICTION == IN_GJ == "IN-GJ"

    def test_gj_pack_matches_direct_seed_loaders(self):
        pack = load_regulatory_pack(IN_GJ)
        assert isinstance(pack, RegulatoryPack)
        assert pack.jurisdiction == IN_GJ

        from app.seed.approvals import load_approval_authorities, load_approval_rules
        from app.seed.consistency import load_consistency_rules
        from app.seed.dependencies import load_approval_dependencies
        from app.seed.documents import load_document_requirements
        from app.seed.evidence_gaps import load_evidence_gaps
        from app.seed.handoff import all_portal_entries
        from app.seed.incentives import load_incentive_schemes
        from app.seed.sources import load_regulatory_sources

        assert [r.model_dump() for r in pack.approval_rules] == [
            r.model_dump() for r in load_approval_rules()
        ]
        assert pack.approval_authorities == load_approval_authorities()
        assert [d.model_dump() for d in pack.dependencies] == [
            d.model_dump() for d in load_approval_dependencies()
        ]
        assert pack.document_requirements == load_document_requirements()
        assert [c.model_dump() for c in pack.consistency_rules] == [
            c.model_dump() for c in load_consistency_rules()
        ]
        assert [s.model_dump() for s in pack.incentive_schemes] == [
            s.model_dump() for s in load_incentive_schemes()
        ]
        assert [s.model_dump() for s in pack.sources] == [
            s.model_dump() for s in load_regulatory_sources()
        ]
        assert [g.model_dump() for g in pack.evidence_gaps] == [
            g.model_dump() for g in load_evidence_gaps()
        ]
        assert pack.portal_entries == all_portal_entries()

    def test_gj_helpers_match_seed_helpers(self):
        pack = load_regulatory_pack(IN_GJ)

        from app.seed.documents import get_requirements_for_approval
        from app.seed.evidence_gaps import get_gaps_for_approval
        from app.seed.handoff import get_portal_entry

        assert pack.get_requirements_for_approval("A01") == (
            get_requirements_for_approval("A01")
        )
        assert [g.model_dump() for g in pack.get_gaps_for_approval("A07")] == [
            g.model_dump() for g in get_gaps_for_approval("A07")
        ]
        assert pack.get_portal_entry("A01") == get_portal_entry("A01")
        assert pack.get_portal_entry("NOPE") is None
        assert pack.get_requirements_for_approval("NOPE") == []
        assert pack.get_gaps_for_approval("NOPE") == []

    def test_mh_pack_is_populated_safe_only(self):
        from app.seed.mh.approvals import MH_INCLUDED_RULE_IDS
        from app.seed.mh.dependencies import load_mh_approval_dependencies
        from app.seed.mh.documents import load_mh_document_requirements
        from app.seed.mh.evidence import load_mh_evidence_gaps
        from app.seed.mh.portals import load_mh_portal_entries
        from app.seed.mh.sources import load_mh_sources

        pack = load_regulatory_pack(IN_MH)
        assert pack.jurisdiction == IN_MH
        assert {r.id for r in pack.approval_rules} == set(
            MH_INCLUDED_RULE_IDS
        )
        assert [d.model_dump() for d in pack.dependencies] == [
            d.model_dump() for d in load_mh_approval_dependencies()
        ]
        assert pack.document_requirements == load_mh_document_requirements()
        assert [g.model_dump() for g in pack.evidence_gaps] == [
            g.model_dump() for g in load_mh_evidence_gaps()
        ]
        assert [s.model_dump() for s in pack.sources] == [
            s.model_dump() for s in load_mh_sources()
        ]
        assert pack.portal_entries == load_mh_portal_entries()
        # Dimensions scheduled for later phases stay empty (fail closed).
        assert pack.consistency_rules == []
        assert pack.incentive_schemes == []

    @pytest.mark.parametrize(
        "bad", ["IN-US", "in-gj", "IN-GJ ", "", "GJ", "MH", None, 123]
    )
    def test_unknown_jurisdiction_fails_explicitly(self, bad):
        with pytest.raises(UnknownJurisdictionError):
            load_regulatory_pack(bad)


class TestPackRuntimeEquivalence:
    def test_orchestration_identical_through_pack(self):
        pack = load_regulatory_pack(IN_GJ)
        direct = _direct_gj_inputs()
        pack_inputs = {
            "facts": direct["facts"],
            "rules": pack.approval_rules,
            "authorities": pack.approval_authorities,
            "dependencies": pack.dependencies,
            "doc_requirements": pack.document_requirements,
            "gaps": {
                r.approval_id: pack.get_gaps_for_approval(r.approval_id)
                for r in pack.approval_rules
            },
        }
        aids = sorted({r.approval_id for r in pack.approval_rules})
        assert _orchestrate(pack_inputs, aids).model_dump() == (
            _orchestrate(direct, aids).model_dump()
        )

    def test_whatif_receives_same_pack_inputs(self):
        pack = load_regulatory_pack(IN_GJ)
        direct = _direct_gj_inputs()
        aids = sorted({r.approval_id for r in pack.approval_rules})
        common = {
            "approval_rules": pack.approval_rules,
            "approval_authorities": pack.approval_authorities,
            "dependencies": pack.dependencies,
            "all_approval_ids": aids,
            "document_requirements": pack.document_requirements,
            "uploaded_documents": [],
            "extraction_results": [],
            "validation_results": [],
            "consistency_result": None,
            "sla_info": None,
            "obtained_approvals": set(),
            "evidence_gaps_by_approval": {
                r.approval_id: pack.get_gaps_for_approval(r.approval_id)
                for r in pack.approval_rules
            },
        }
        result = run_whatif_assessment(
            application_id="PACK-TEST",
            base_facts=dict(direct["facts"]),
            fact_overrides={"production_capacity": 100},
            **common,
        )
        expected_baseline = _orchestrate(direct, aids)
        assert result.baseline.model_dump() == expected_baseline.model_dump()
        assert result.diff.no_change is False

    def test_impact_rehearsal_receives_same_pack_inputs(self):
        pack = load_regulatory_pack(IN_GJ)
        direct = _direct_gj_inputs()
        aids = sorted({r.approval_id for r in pack.approval_rules})
        from_pack = RehearsalInputs(
            base_facts=dict(direct["facts"]),
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=pack.dependencies,
            all_approval_ids=aids,
            document_requirements=pack.document_requirements,
            evidence_gaps_by_approval={
                r.approval_id: pack.get_gaps_for_approval(r.approval_id)
                for r in pack.approval_rules
            },
        )
        from_direct = RehearsalInputs(
            base_facts=dict(direct["facts"]),
            approval_rules=direct["rules"],
            approval_authorities=direct["authorities"],
            dependencies=direct["dependencies"],
            all_approval_ids=aids,
            document_requirements=direct["doc_requirements"],
            evidence_gaps_by_approval=direct["gaps"],
        )
        assert from_pack == from_direct

    def test_handoff_portal_inputs_match_seed_catalog(self):
        pack = load_regulatory_pack(IN_GJ)
        from app.seed.handoff import all_portal_entries, get_portal_entry

        assert pack.portal_entries == all_portal_entries()
        for code in ("A01", "A04", "A18"):
            assert pack.get_portal_entry(code) == get_portal_entry(code)


class TestNoDirectSeedLoadingInOrchestration:
    def test_orchestration_module_has_no_seed_loader_bindings(self):
        import app.api.orchestration as orch

        for name in (
            "load_approval_rules",
            "load_approval_authorities",
            "load_approval_dependencies",
            "load_document_requirements",
            "get_gaps_for_approval",
        ):
            assert not hasattr(orch, name), f"direct seed loader {name} in orchestration"

    def test_orchestration_source_imports_only_pack_boundary(self):
        import app.api.orchestration as orch

        source = Path(orch.__file__).read_text(encoding="utf-8")
        assert "from app.seed.pack import" in source
        for mod in (
            "app.seed.approvals",
            "app.seed.dependencies",
            "app.seed.documents",
            "app.seed.evidence_gaps",
        ):
            assert mod not in source, f"direct seed import {mod} in orchestration"
