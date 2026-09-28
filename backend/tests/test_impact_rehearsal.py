"""Service-level tests for stateless regulatory change rehearsal.

Rehearsal = old inputs -> orchestrate -> new inputs -> orchestrate ->
compare with the existing compare_orchestrations(). Nothing is persisted;
seed rules stay authoritative and untouched.
"""
from __future__ import annotations

import pytest

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


def _inputs(facts=None, scope=None, obtained=None):
    from app.regulatory.impact import RehearsalInputs
    from app.seed.approvals import load_approval_authorities, load_approval_rules
    from app.seed.dependencies import load_approval_dependencies
    from app.seed.documents import load_document_requirements
    from app.seed.evidence_gaps import get_gaps_for_approval

    codes = list(scope) if scope else list(_ALL_CODES)
    return RehearsalInputs(
        base_facts=dict(facts) if facts is not None else dict(_FULL_FACTS),
        approval_rules=load_approval_rules(),
        approval_authorities=load_approval_authorities(),
        dependencies=load_approval_dependencies(),
        all_approval_ids=codes,
        document_requirements=load_document_requirements(),
        uploaded_documents=[],
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=set(obtained) if obtained else set(),
        evidence_gaps_by_approval={aid: get_gaps_for_approval(aid) for aid in codes},
    )


def _rule_dict(rule_id):
    from app.seed.approvals import load_approval_rules

    for rule in load_approval_rules():
        if rule.id == rule_id:
            return rule.model_dump()
    raise AssertionError(f"unknown seed rule {rule_id}")


class TestSourceMetadataChange:
    def test_unchanged_source_is_no_impact(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="SOURCE_METADATA_CHANGE",
            source_id="S01",
            old_value={"checked_date": "2026-09-15"},
            new_value={"checked_date": "2026-09-15"},
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "NO_IMPACT"

    def test_source_with_no_rule_references_is_no_impact(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        # S33 is cited only by incentive schemes, never by approval rules.
        change = ChangeDescriptor(
            change_kind="SOURCE_METADATA_CHANGE",
            source_id="S33",
            old_value={"checked_date": "2026-09-15"},
            new_value={"checked_date": "2026-09-26"},
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "NO_IMPACT"
        assert impact.affected_approvals == []

    def test_source_referenced_by_one_rule_is_relevant(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        # S19 is cited only by the A18 CGWA rule.
        change = ChangeDescriptor(
            change_kind="SOURCE_METADATA_CHANGE",
            source_id="S19",
            old_value={"checked_date": "2026-09-15"},
            new_value={"checked_date": "2026-09-26"},
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "SOURCE_RELEVANT"
        assert impact.affected_approvals == ["A18"]
        combined = " ".join([impact.reason] + impact.evidence_caveats).lower()
        assert "required" not in combined.replace("not required", "")

    def test_source_referenced_by_multiple_rules(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        # S01 is cited by A04 (R-IFP-001) and A08 (R-BOCW-001).
        change = ChangeDescriptor(
            change_kind="SOURCE_METADATA_CHANGE",
            source_id="S01",
            old_value={"title": "Gujarat IFP Pre-Establishment"},
            new_value={"title": "Gujarat IFP Pre-Establishment (revised)"},
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "SOURCE_RELEVANT"
        assert set(impact.affected_approvals) == {"A04", "A08"}

    def test_metadata_change_never_fabricates_legal_result(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="SOURCE_METADATA_CHANGE",
            source_id="S07",
            old_value={"authority": "Government of Gujarat"},
            new_value={"authority": "Government of Gujarat (renamed dept)"},
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "SOURCE_RELEVANT"
        assert impact.diffs == []
        assert "required" not in impact.reason.lower()

    def test_unknown_source_rejected(self):
        from app.regulatory.impact import ImpactValidationError, rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="SOURCE_METADATA_CHANGE",
            source_id="S99",
            old_value={},
            new_value={"checked_date": "2026-09-26"},
        )
        with pytest.raises(ImpactValidationError):
            rehearse_impact(change, _inputs())


class TestRuleChange:
    def test_rule_change_producing_result_changed(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-EIA-001")
        new = dict(old)
        # Raise the EIA threshold above the Dahej production capacity.
        new["applicability_conditions"] = [
            {
                "kind": "and",
                "conditions": [
                    {
                        "kind": "condition",
                        "field": "industry_type",
                        "op": "eq",
                        "value": "synthetic organic / specialty chemical manufacturing",
                    },
                    {
                        "kind": "condition",
                        "field": "production_capacity",
                        "op": "gte",
                        "value": 30000,
                    },
                ],
            }
        ]
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE",
            rule_id="R-EIA-001",
            old_value=old,
            new_value=new,
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "RESULT_CHANGED"
        assert "A05" in [d.approval_id for d in impact.diffs]
        a05 = next(d for d in impact.diffs if d.approval_id == "A05")
        assert a05.baseline_applicability == "applies"
        assert a05.whatif_applicability == "does_not_apply"

    def test_rule_change_producing_source_relevant(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-HW-001")
        new = dict(old)
        # Citation-only edit: output must be identical.
        new["source_refs"] = [
            {
                "source_id": "S16",
                "citation_span": "CPCB HOWM 2024 Amendment - Rule 6 (revised)",
            }
        ]
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE", rule_id="R-HW-001", old_value=old, new_value=new
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "SOURCE_RELEVANT"
        assert impact.affected_approvals == ["A11"]

    def test_unrelated_project_scope_is_no_impact(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-EIA-001")
        new = dict(old)
        new["applicability_conditions"] = [
            {
                "kind": "and",
                "conditions": [
                    {
                        "kind": "condition",
                        "field": "industry_type",
                        "op": "eq",
                        "value": "synthetic organic / specialty chemical manufacturing",
                    },
                    {
                        "kind": "condition",
                        "field": "production_capacity",
                        "op": "gte",
                        "value": 30000,
                    },
                ],
            }
        ]
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE",
            rule_id="R-EIA-001",
            old_value=old,
            new_value=new,
        )
        # Application scoped to A04 only: A05 is out of scope.
        impact = rehearse_impact(change, _inputs(scope=["A04"]))
        assert impact.classification == "NO_IMPACT"

    def test_same_authority_without_rule_link_is_no_impact(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        # S04 (GIDC) is cited by the A02 rule only; scope to A18.
        change = ChangeDescriptor(
            change_kind="SOURCE_METADATA_CHANGE",
            source_id="S04",
            old_value={"checked_date": "2026-09-15"},
            new_value={"checked_date": "2026-09-26"},
        )
        impact = rehearse_impact(change, _inputs(scope=["A18"]))
        assert impact.classification == "NO_IMPACT"

    def test_malformed_rule_rejected(self):
        from app.regulatory.impact import ImpactValidationError, rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-EIA-001")
        new = {"kind": "not-a-rule"}
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE", rule_id="R-EIA-001", old_value=old, new_value=new
        )
        with pytest.raises(ImpactValidationError):
            rehearse_impact(change, _inputs())

    def test_unknown_rule_rejected(self):
        from app.regulatory.impact import ImpactValidationError, rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-EIA-001")
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE", rule_id="R-NOPE-000", old_value=old, new_value=dict(old)
        )
        with pytest.raises(ImpactValidationError):
            rehearse_impact(change, _inputs())

    def test_rule_approval_mismatch_rejected(self):
        from app.regulatory.impact import ImpactValidationError, rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-EIA-001")
        new = dict(old)
        new["approval_id"] = "A04"
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE", rule_id="R-EIA-001", old_value=old, new_value=new
        )
        with pytest.raises(ImpactValidationError):
            rehearse_impact(change, _inputs())

    def test_deterministic_repeatability(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-EIA-001")
        new = dict(old)
        new["applicability_conditions"] = [
            {
                "kind": "and",
                "conditions": [
                    {
                        "kind": "condition",
                        "field": "industry_type",
                        "op": "eq",
                        "value": "synthetic organic / specialty chemical manufacturing",
                    },
                    {
                        "kind": "condition",
                        "field": "production_capacity",
                        "op": "gte",
                        "value": 30000,
                    },
                ],
            }
        ]
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE",
            rule_id="R-EIA-001",
            old_value=old,
            new_value=new,
        )
        first = rehearse_impact(change, _inputs()).model_dump()
        second = rehearse_impact(change, _inputs()).model_dump()
        assert first == second


class TestDependencyChange:
    def test_dependency_removal_propagates(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="DEPENDENCY_CHANGE",
            old_value={"approval_id": "A02", "prerequisite_approval_id": "A04"},
            new_value=None,
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "RESULT_CHANGED"
        changed_ids = {d.approval_id for d in impact.diffs}
        assert "A02" in changed_ids
        a02 = next(d for d in impact.diffs if d.approval_id == "A02")
        assert a02.baseline_dependency == "blocked"
        assert a02.whatif_dependency == "ready"

    def test_rule_change_cascades_a04_a02_a03(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        old = _rule_dict("R-IFP-001")
        new = dict(old)
        new["applicability_conditions"] = [
            {"kind": "condition", "field": "industry_type", "op": "eq", "value": "textiles"}
        ]
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE", rule_id="R-IFP-001", old_value=old, new_value=new
        )
        # A02 obtained isolates the A04 -> A03 path: A03's own rule is
        # untouched, only its dependency readiness can move.
        impact = rehearse_impact(change, _inputs(obtained={"A02"}))
        assert impact.classification == "RESULT_CHANGED"
        changed_ids = {d.approval_id for d in impact.diffs}
        assert {"A04", "A03"} <= changed_ids
        a03 = next(d for d in impact.diffs if d.approval_id == "A03")
        # A03's own rule is untouched; only dependency readiness moves.
        assert a03.baseline_applicability == a03.whatif_applicability
        assert a03.baseline_dependency != a03.whatif_dependency


class TestEvidenceChange:
    def test_partial_to_verified_can_resolve(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="EVIDENCE_STATUS_CHANGE",
            evidence_id="G0R5-MSIHC-AUTHORITY",
            old_status="NOT_ESTABLISHED",
            new_status="VERIFIED",
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification == "RESULT_CHANGED"
        assert "A12" in [d.approval_id for d in impact.diffs]

    def test_partial_to_not_established_stays_fail_closed(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="EVIDENCE_STATUS_CHANGE",
            evidence_id="G0R5-FIRE-R25",
            old_status="PARTIAL",
            new_status="NOT_ESTABLISHED",
        )
        impact = rehearse_impact(change, _inputs())
        a06_new = impact.new_results["A06"]
        assert a06_new["status"] == "insufficient_data"
        assert "required" not in impact.reason.lower()

    def test_conflicting_evidence_stays_fail_closed(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="EVIDENCE_STATUS_CHANGE",
            evidence_id="G0R5-FIRE-RENEWAL",
            old_status="CONFLICTING",
            new_status="CONFLICTING",
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.new_results["A06"]["status"] == "insufficient_data"

    def test_stale_old_status_rejected(self):
        from app.regulatory.impact import ImpactValidationError, rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="EVIDENCE_STATUS_CHANGE",
            evidence_id="G0R5-FIRE-R25",
            old_status="VERIFIED",  # actual seed status is PARTIAL
            new_status="NOT_ESTABLISHED",
        )
        with pytest.raises(ImpactValidationError):
            rehearse_impact(change, _inputs())

    def test_unknown_evidence_rejected(self):
        from app.regulatory.impact import ImpactValidationError, rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="EVIDENCE_STATUS_CHANGE",
            evidence_id="G0R5-NOPE",
            old_status="PARTIAL",
            new_status="VERIFIED",
        )
        with pytest.raises(ImpactValidationError):
            rehearse_impact(change, _inputs())

    def test_groundwater_safety_preserved(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor

        change = ChangeDescriptor(
            change_kind="EVIDENCE_STATUS_CHANGE",
            evidence_id="G0R5-GW-NO-EXTRACTION",
            old_status="NOT_ESTABLISHED",
            new_status="NOT_ESTABLISHED",
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.new_results["A18"]["status"] == "not_applicable"
        combined = " ".join(
            [impact.reason]
            + [
                b["description"]
                for d in impact.diffs
                for b in d.added_blockers + d.removed_blockers
            ]
        ).lower()
        assert "legally not required" not in combined
        assert "is not required" not in combined


class TestDocumentChange:
    def test_document_requirement_change(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor
        from app.seed.documents import load_document_requirements

        current = next(
            r for r in load_document_requirements() if r["requirement_key"] == "D15"
        )
        old = dict(current)
        new = dict(current)
        new["requirement_level"] = "required"
        change = ChangeDescriptor(
            change_kind="DOCUMENT_REQUIREMENT_CHANGE",
            requirement_key="D15",
            old_value=old,
            new_value=new,
        )
        impact = rehearse_impact(change, _inputs())
        assert impact.classification in ("RESULT_CHANGED", "SOURCE_RELEVANT")
        assert "A05" in impact.affected_approvals
        # Applicability reasoning is untouched by document edits.
        assert impact.baseline_results["A05"]["applicability"] == (
            impact.new_results["A05"]["applicability"]
        )


class TestSeedAuthorityRegression:
    def test_rehearsal_never_reads_db_rules_table(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor
        from app.repositories.approvals import ApprovalsRepository

        def _forbidden(self, *args, **kwargs):
            raise AssertionError("rehearsal must use seed rules, not the DB table")

        original = ApprovalsRepository.get_rules_for_approval
        ApprovalsRepository.get_rules_for_approval = _forbidden
        try:
            change = ChangeDescriptor(
                change_kind="SOURCE_METADATA_CHANGE",
                source_id="S07",
                old_value={"checked_date": "2026-09-15"},
                new_value={"checked_date": "2026-09-26"},
            )
            impact = rehearse_impact(change, _inputs())
            assert impact.classification == "SOURCE_RELEVANT"
        finally:
            ApprovalsRepository.get_rules_for_approval = original

    def test_seed_rules_untouched_by_rehearsal(self):
        from app.regulatory.impact import rehearse_impact
        from app.regulatory.impact_models import ChangeDescriptor
        from app.seed.approvals import load_approval_rules

        before = [r.model_dump() for r in load_approval_rules()]
        old = _rule_dict("R-EIA-001")
        new = dict(old)
        new["version"] = "2"
        change = ChangeDescriptor(
            change_kind="RULE_CHANGE", rule_id="R-EIA-001", old_value=old, new_value=new
        )
        rehearse_impact(change, _inputs())
        after = [r.model_dump() for r in load_approval_rules()]
        assert before == after
