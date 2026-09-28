"""Service-level tests for stateless What-If recalculation.

Flow under test:
  base facts -> orchestrate (baseline) -> apply overrides (copy) ->
  orchestrate (what-if) -> compare. Both runs share the same deterministic
  pipeline; docs/consistency/SLA/obtained/gaps are held constant.
"""
from __future__ import annotations

import pytest

from app.orchestration.service import orchestrate_application_full
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.dependencies import load_approval_dependencies
from app.seed.documents import load_document_requirements
from app.seed.evidence_gaps import get_gaps_for_approval

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

_ALL_CODES = [f"A{i:02d}" for i in range(1, 19)]


def _assess(facts, gaps_by_approval=None):
    return orchestrate_application_full(
        application_id="APP-WHATIF",
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
        evidence_gaps_by_approval=gaps_by_approval,
    )


class TestApplyFactOverrides:
    def test_merge_returns_new_dict(self):
        from app.orchestration.whatif import apply_fact_overrides

        base = dict(_FULL_FACTS)
        merged = apply_fact_overrides(base, {"production_capacity": 30000})
        assert merged["production_capacity"] == 30000
        assert base["production_capacity"] == 20000
        assert merged is not base

    def test_none_removes_fact(self):
        from app.orchestration.whatif import apply_fact_overrides

        merged = apply_fact_overrides(dict(_FULL_FACTS), {"power_demand": None})
        assert "power_demand" not in merged

    def test_multiple_overrides_atomic(self):
        from app.orchestration.whatif import apply_fact_overrides

        merged = apply_fact_overrides(
            dict(_FULL_FACTS),
            {"production_capacity": 30000, "building_height": 14},
        )
        assert merged["production_capacity"] == 30000
        assert merged["building_height"] == 14

    def test_unknown_field_rejected(self):
        from app.orchestration.whatif import WhatIfValidationError, apply_fact_overrides

        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(dict(_FULL_FACTS), {"admin": True})

    def test_invalid_type_rejected_without_coercion(self):
        from app.orchestration.whatif import WhatIfValidationError, apply_fact_overrides

        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(dict(_FULL_FACTS), {"power_demand": "1000"})
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(dict(_FULL_FACTS), {"groundwater_use": 1})

    def test_bool_not_accepted_as_numeric(self):
        from app.orchestration.whatif import WhatIfValidationError, apply_fact_overrides

        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(dict(_FULL_FACTS), {"power_demand": True})


class TestCompareOrchestrations:
    def test_no_change_scenario(self):
        from app.orchestration.whatif import compare_orchestrations

        baseline = _assess(dict(_FULL_FACTS))
        what_if = _assess(dict(_FULL_FACTS))
        diff = compare_orchestrations(baseline, what_if)
        assert diff.no_change is True
        assert diff.changed_approvals == []
        assert set(diff.unchanged_approvals) == set(_ALL_CODES)
        assert diff.added_blockers == []
        assert diff.removed_blockers == []
        assert diff.overall_baseline == diff.overall_whatif

    def test_single_applicability_change(self):
        from app.orchestration.whatif import apply_fact_overrides, compare_orchestrations

        baseline = _assess(dict(_FULL_FACTS))
        merged = apply_fact_overrides(dict(_FULL_FACTS), {"production_capacity": 10000})
        what_if = _assess(merged)
        # Rule-level: A05 production_capacity gte 20000 flips applies -> does_not_apply.
        assert baseline.approvals["A05"].applicability_result == "applies"
        assert what_if.approvals["A05"].applicability_result == "does_not_apply"
        diff = compare_orchestrations(baseline, what_if)
        assert diff.no_change is False
        changed_ids = {c.approval_id for c in diff.changed_approvals}
        assert "A05" in changed_ids
        a05 = next(c for c in diff.changed_approvals if c.approval_id == "A05")
        assert a05.baseline_applicability == "applies"
        assert a05.whatif_applicability == "does_not_apply"
        # Explanations come from the engine output, verbatim.
        assert a05.whatif_explanation == what_if.approvals["A05"].explanation

    def test_base_facts_never_mutated(self):
        from app.orchestration.whatif import apply_fact_overrides

        base = dict(_FULL_FACTS)
        snapshot = dict(base)
        apply_fact_overrides(base, {"production_capacity": 10000, "power_demand": None})
        assert base == snapshot

    def test_unused_field_override_is_no_change(self):
        from app.orchestration.whatif import apply_fact_overrides, compare_orchestrations

        baseline = _assess(dict(_FULL_FACTS))
        merged = apply_fact_overrides(dict(_FULL_FACTS), {"village": "Dahej"})
        what_if = _assess(merged)
        diff = compare_orchestrations(baseline, what_if)
        assert diff.no_change is True

    def test_blocker_diff_stable(self):
        from app.orchestration.whatif import compare_orchestrations

        baseline = _assess(dict(_FULL_FACTS))
        what_if = _assess(dict(_FULL_FACTS))
        diff = compare_orchestrations(baseline, what_if)
        assert diff.added_blockers == []
        assert diff.removed_blockers == []

    def test_next_action_diff(self):
        from app.orchestration.whatif import apply_fact_overrides, compare_orchestrations

        baseline = _assess(dict(_FULL_FACTS))
        merged = apply_fact_overrides(dict(_FULL_FACTS), {"production_capacity": 10000})
        what_if = _assess(merged)
        diff = compare_orchestrations(baseline, what_if)
        assert diff.next_action_baseline is not None or diff.next_action_whatif is not None
        # At minimum the overall/next-action fields are carried through verbatim.
        assert diff.overall_baseline == baseline.overall_status.value
        assert diff.overall_whatif == what_if.overall_status.value

    def test_docs_consistency_sla_held_constant(self):
        from app.orchestration.whatif import apply_fact_overrides, compare_orchestrations

        baseline = _assess(dict(_FULL_FACTS))
        merged = apply_fact_overrides(dict(_FULL_FACTS), {"production_capacity": 10000})
        what_if = _assess(merged)
        # Document readiness inputs are identical, so per-approval document
        # summaries for approvals whose applicability did not change are equal.
        for aid in ("A04", "A11"):
            assert baseline.approvals[aid].documents == what_if.approvals[aid].documents
        diff = compare_orchestrations(baseline, what_if)
        assert diff.no_change is False  # facts still changed applicability elsewhere


class TestDependencyPropagation:
    def test_a04_change_propagates_to_a03(self):
        from app.orchestration.whatif import apply_fact_overrides, compare_orchestrations

        baseline = _assess(dict(_FULL_FACTS))
        assert baseline.approvals["A03"].dependency_readiness == "blocked"
        merged = apply_fact_overrides(dict(_FULL_FACTS), {"industry_type": "textiles"})
        what_if = _assess(merged)
        # A03's own rule does not use industry_type, so its applicability is
        # unchanged, but its prerequisites (A04/A02 now does_not_apply and
        # therefore satisfied) flip its dependency readiness.
        assert what_if.approvals["A03"].applicability_result == (
            baseline.approvals["A03"].applicability_result
        )
        assert what_if.approvals["A03"].dependency_readiness != (
            baseline.approvals["A03"].dependency_readiness
        )
        diff = compare_orchestrations(baseline, what_if)
        changed_ids = {c.approval_id for c in diff.changed_approvals}
        assert "A03" in changed_ids
        a03 = next(c for c in diff.changed_approvals if c.approval_id == "A03")
        assert a03.baseline_dependency != a03.whatif_dependency


class TestEvidenceSafety:
    def _gaps(self):
        return {aid: get_gaps_for_approval(aid) for aid in _ALL_CODES}

    def test_groundwater_false_stays_not_applicable(self):
        baseline = _assess(dict(_FULL_FACTS), gaps_by_approval=self._gaps())
        a18 = baseline.approvals["A18"]
        assert a18.applicability_result == "does_not_apply"
        assert a18.status.value == "not_applicable"

    def test_groundwater_true_fails_closed_on_gaps(self):
        from app.orchestration.whatif import apply_fact_overrides

        merged = apply_fact_overrides(dict(_FULL_FACTS), {"groundwater_use": True})
        what_if = _assess(merged, gaps_by_approval=self._gaps())
        a18 = what_if.approvals["A18"]
        # The CGWA rule itself applies once groundwater is used...
        assert a18.applicability_result == "applies"
        # ...but unresolved groundwater evidence forces INSUFFICIENT_DATA.
        assert a18.status.value == "insufficient_data"
        assert any(b.evidence_id for b in a18.blockers)
        combined = " ".join(
            [a18.explanation] + [b.description for b in a18.blockers]
        ).lower()
        # No affirmative "not required" conclusion may be fabricated; the gap
        # texts themselves discuss the missing exemption in prohibitive terms.
        assert "legally not required" not in combined
        assert "is not required" not in combined
        # Fail-closed action is attached, not a legal determination.
        assert any("do not encode" in b.action_required.lower() for b in a18.blockers)
