"""MH batch-1 pack: contract, rule-level, R-074, contamination (Phase 3).

Batch 1 = 19 directly encodable IMPLEMENTATION_SAFE rules. Every
expected result below comes from the v5 rule semantics (thresholds,
set memberships, exception clauses), not from the implementation.
"""
from __future__ import annotations

from datetime import date

from app.orchestration.service import orchestrate_application_full
from app.rules.applicability import evaluate_rule
from app.rules.facts import mh_fact_keys
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ConditionNode,
    LiteralNode,
    NotNode,
    OrNode,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_DO_NOT_IMPLEMENT_RULE_IDS,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    MH_UNKNOWN_RULE_IDS,
    load_mh_approval_authorities,
    load_mh_approval_rules,
)
from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack


def _by_id(rule_id):
    return next(r for r in load_mh_approval_rules() if r.id == rule_id)


def _leaf_fields(node: ConditionNode) -> set[str]:
    if isinstance(node, ApplicabilityCondition):
        return {node.field}
    if isinstance(node, (AndNode, OrNode)):
        out: set[str] = set()
        for child in node.conditions:
            out |= _leaf_fields(child)
        return out
    if isinstance(node, NotNode):
        return _leaf_fields(node.condition)
    if isinstance(node, LiteralNode):
        return set()
    raise AssertionError(f"unknown node {node!r}")


class TestPackContract:
    def test_26_rules_loaded(self):
        assert len(load_mh_approval_rules()) == 26
        assert {r.id for r in load_mh_approval_rules()} == set(
            MH_INCLUDED_RULE_IDS
        )

    def test_included_subset_of_safe(self):
        assert set(MH_INCLUDED_RULE_IDS) <= MH_IMPLEMENTATION_SAFE_RULE_IDS

    def test_exclusion_sets_disjoint_from_pack(self):
        packed = {r.id for r in load_mh_approval_rules()}
        assert packed & MH_REQUIRES_CONFIRMATION_RULE_IDS == set()
        assert packed & MH_DO_NOT_IMPLEMENT_RULE_IDS == set()
        assert packed & MH_UNKNOWN_RULE_IDS == set()
        assert packed & set(MH_DEFERRED_RULES) == set()

    def test_classification_sets_cover_all_105(self):
        assert (
            len(MH_IMPLEMENTATION_SAFE_RULE_IDS)
            + len(MH_REQUIRES_CONFIRMATION_RULE_IDS)
            + len(MH_DO_NOT_IMPLEMENT_RULE_IDS)
            == 105
        )

    def test_every_rule_has_source_metadata(self):
        for rule in load_mh_approval_rules():
            assert rule.source_refs, rule.id
            for ref in rule.source_refs:
                assert ref.source_id.startswith("SRC-"), rule.id
                assert len(ref.citation_span) >= 1, rule.id

    def test_every_rule_versioned_v5(self):
        for rule in load_mh_approval_rules():
            assert rule.version == "v5", rule.id

    def test_referenced_facts_exist_in_registry(self):
        known = set(mh_fact_keys())
        for rule in load_mh_approval_rules():
            fields: set[str] = set()
            for tree in rule.applicability_conditions:
                fields |= _leaf_fields(tree)
            assert fields <= known, (rule.id, fields - known)

    def test_effective_windows_valid(self):
        for rule in load_mh_approval_rules():
            if rule.effective_from is not None and (
                rule.effective_to is not None
            ):
                assert rule.effective_from <= rule.effective_to, rule.id

    def test_approval_ids_internally_consistent(self):
        authorities = load_mh_approval_authorities()
        rule_approvals = {r.approval_id for r in load_mh_approval_rules()}
        assert rule_approvals <= set(authorities), (
            rule_approvals - set(authorities)
        )

    def test_no_duplicate_rule_ids(self):
        ids = [r.id for r in load_mh_approval_rules()]
        assert len(set(ids)) == len(ids)


class TestRuleSemantics:
    def test_r002_small_unit(self):
        small = {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False}
        assert evaluate_rule(_by_id("R-002"), small).result == "applies"
        # 25 exactly is NOT small (strict lt).
        exact = {"F-PRC-01": 25, "F-PRC-02": 10, "F-PRC-03": False}
        assert evaluate_rule(_by_id("R-002"), exact).result == "does_not_apply"
        assert evaluate_rule(_by_id("R-002"), {}).result == "insufficient_data"
        # Effective 2014-06-25.
        assert evaluate_rule(
            _by_id("R-002"), small, evaluation_date=date(2014, 6, 24)
        ).result == "does_not_apply"
        assert evaluate_rule(
            _by_id("R-002"), small, evaluation_date=date(2014, 6, 25)
        ).result == "applies"

    def test_r007_builtup_range(self):
        rule = _by_id("R-007")
        assert evaluate_rule(rule, {"F-BLD-01": 20000}).result == "applies"
        assert evaluate_rule(rule, {"F-BLD-01": 149999}).result == "applies"
        assert evaluate_rule(rule, {"F-BLD-01": 19999}).result == (
            "does_not_apply"
        )
        assert evaluate_rule(rule, {"F-BLD-01": 150000}).result == (
            "does_not_apply"
        )
        assert evaluate_rule(rule, {}).result == "insufficient_data"

    def test_r009_either_limb_wins(self):
        rule = _by_id("R-009")
        # Area limb true while built-up unknown: OR still applies.
        assert evaluate_rule(rule, {"F-BLD-03": 50}).result == "applies"
        assert evaluate_rule(rule, {"F-BLD-01": 150000}).result == "applies"
        neither = {"F-BLD-03": 10, "F-BLD-01": 100}
        assert evaluate_rule(rule, neither).result == "does_not_apply"
        assert evaluate_rule(rule, {}).result == "insufficient_data"

    def test_r011_r012_product_sets(self):
        assert evaluate_rule(
            _by_id("R-011"), {"F-PRD-02": ["PESTICIDE_TECHNICAL"]}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-011"), {"F-PRD-02": ["BULK_DRUG"]}
        ).result == "does_not_apply"
        assert evaluate_rule(_by_id("R-011"), {}).result == (
            "insufficient_data"
        )
        assert evaluate_rule(
            _by_id("R-012"), {"F-PRD-02": ["PAINT_INTEGRATED"]}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-012"), {"F-PRD-02": ["NONE"]}
        ).result == "does_not_apply"

    def test_r018_hw_trigger(self):
        assert evaluate_rule(
            _by_id("R-018"), {"F-HW-01": True}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-018"), {"F-HW-01": False}
        ).result == "does_not_apply"
        assert evaluate_rule(_by_id("R-018"), {}).result == (
            "insufficient_data"
        )

    def test_r026_exception_fails_closed(self):
        rule = _by_id("R-026")
        ok = {"F-LAB-03": 50, "F-LAB-09": False}
        assert evaluate_rule(rule, ok).result == "applies"
        assert evaluate_rule(
            rule, {"F-LAB-03": 49, "F-LAB-09": False}
        ).result == "does_not_apply"
        # Exception limb true -> no registration duty.
        assert evaluate_rule(
            rule, {"F-LAB-03": 50, "F-LAB-09": True}
        ).result == "does_not_apply"
        # Exception fact missing -> cannot confirm -> fail closed.
        assert evaluate_rule(rule, {"F-LAB-03": 50}).result == (
            "insufficient_data"
        )

    def test_r028_boiler_definition(self):
        rule = _by_id("R-028")
        boiler = {
            "F-BLR-04": True, "F-BLR-01": 30, "F-BLR-05": 5,
            "F-BLR-02": 2, "F-BLR-03": 150,
        }
        assert evaluate_rule(rule, boiler).result == "applies"
        # Small-boiler exclusion: design AND working gauge < 1.
        small = dict(boiler, **{"F-BLR-05": 0.5, "F-BLR-02": 0.5})
        assert evaluate_rule(rule, small).result == "does_not_apply"
        # Low-temperature exclusion.
        cold = dict(boiler, **{"F-BLR-03": 50})
        assert evaluate_rule(rule, cold).result == "does_not_apply"
        # Unknown operand that could flip -> UNKNOWN, never FALSE.
        assert evaluate_rule(rule, {}).result == "insufficient_data"
        partial = dict(boiler)
        del partial["F-BLR-03"]
        assert evaluate_rule(rule, partial).result == "insufficient_data"

    def test_r030_class_b_boundaries(self):
        rule = _by_id("R-030")
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2500, "F-PET-04": 1000}
        ).result == "applies"
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2501, "F-PET-04": 1000}
        ).result == "does_not_apply"
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 1001}
        ).result == "does_not_apply"
        assert evaluate_rule(
            rule, {"F-PET-01": "A", "F-PET-02": 10, "F-PET-04": 10}
        ).result == "does_not_apply"
        # YEAR_ONLY effective date is omitted, never invented.
        assert rule.effective_from is None

    def test_r035_branch_guard(self):
        assert evaluate_rule(
            _by_id("R-035"), {"F-LOC-01": True}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-035"), {"F-LOC-01": False}
        ).result == "does_not_apply"
        assert evaluate_rule(_by_id("R-035"), {}).result == (
            "insufficient_data"
        )

    def test_r043_mse_exemption(self):
        rule = _by_id("R-043")
        assert evaluate_rule(
            rule, {"F-INC-01": "MICRO", "F-WAT-05": 5}
        ).result == "applies"
        # 10 exactly is not exempt (strict lt).
        assert evaluate_rule(
            rule, {"F-INC-01": "SMALL", "F-WAT-05": 10}
        ).result == "does_not_apply"
        # Medium enterprises are not covered.
        assert evaluate_rule(
            rule, {"F-INC-01": "MEDIUM", "F-WAT-05": 5}
        ).result == "does_not_apply"
        # Derived class missing -> fail closed.
        assert evaluate_rule(rule, {"F-WAT-05": 5}).result == (
            "insufficient_data"
        )

    def test_r044_domestic_exemption(self):
        rule = _by_id("R-044")
        assert evaluate_rule(
            rule, {"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 5}
        ).result == "applies"
        assert evaluate_rule(
            rule, {"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 6}
        ).result == "does_not_apply"
        assert evaluate_rule(
            rule, {"F-WAT-06": "INDUSTRIAL", "F-WAT-05": 1}
        ).result == "does_not_apply"

    def test_r046_r056_r067_r093_triggers(self):
        assert evaluate_rule(
            _by_id("R-046"), {"F-WAT-08": True}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-046"), {"F-WAT-08": False}
        ).result == "does_not_apply"
        assert evaluate_rule(
            _by_id("R-056"), {"F-HW-03": True}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-067"), {"F-INS-01": True}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-067"), {"F-INS-01": False}
        ).result == "does_not_apply"
        assert evaluate_rule(
            _by_id("R-093"), {"F-TRN-01": True}
        ).result == "applies"

    def test_r070_safety_officer_bands(self):
        rule = _by_id("R-070")
        assert evaluate_rule(
            rule, {"F-LAB-07": False, "F-LAB-01": 500}
        ).result == "applies"
        assert evaluate_rule(
            rule, {"F-LAB-07": True, "F-LAB-01": 250}
        ).result == "applies"
        assert evaluate_rule(
            rule, {"F-LAB-07": False, "F-LAB-01": 499}
        ).result == "does_not_apply"
        assert evaluate_rule(
            rule, {"F-LAB-07": True, "F-LAB-01": 249}
        ).result == "does_not_apply"
        assert evaluate_rule(rule, {"F-LAB-01": 999}).result == (
            "insufficient_data"
        )

    def test_r089_ismw_threshold(self):
        assert evaluate_rule(
            _by_id("R-089"), {"F-LAB-08": 10}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-089"), {"F-LAB-08": 9}
        ).result == "does_not_apply"

    def test_r094_ewaste_threshold(self):
        assert evaluate_rule(
            _by_id("R-094"), {"F-EEE-01": 1000}
        ).result == "applies"
        assert evaluate_rule(
            _by_id("R-094"), {"F-EEE-01": 999}
        ).result == "does_not_apply"
        # Effective 2023-04-01.
        assert evaluate_rule(
            _by_id("R-094"), {"F-EEE-01": 1000},
            evaluation_date=date(2023, 3, 31),
        ).result == "does_not_apply"

    def test_explanations_carry_traceability(self):
        ev = evaluate_rule(
            _by_id("R-007"), {"F-BLD-01": 30000}, authority="AUT-002"
        )
        assert ev.rule_id == "R-007"
        assert ev.approval_id == "APR-003"
        assert ev.authority == "AUT-002"
        assert ev.required_inputs == ["F-BLD-01"]
        assert ev.source_references[0].source_id == "SRC-001"
        assert "F-BLD-01" in ev.reason


class TestR074FailClosed:
    def test_r074_absent_from_pack(self):
        assert "R-074" not in {r.id for r in load_mh_approval_rules()}

    def test_r074_classified_unknown_hold(self):
        assert "R-074" in MH_UNKNOWN_RULE_IDS
        assert "R-074" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_no_ec_combo_rule_in_pack(self):
        for rule in load_mh_approval_rules():
            assert "5(f)+8(a)" not in rule.id
            assert "5F_AND_8A" not in rule.id

    def test_r015_r052_also_absent(self):
        packed = {r.id for r in load_mh_approval_rules()}
        assert "R-015" not in packed
        assert "R-052" not in packed


class TestContamination:
    def test_mh_pack_contains_no_gj_rules(self):
        from app.seed.approvals import load_approval_rules as gj_rules

        gj_ids = {r.id for r in gj_rules()}
        mh_ids = {r.id for r in load_mh_approval_rules()}
        assert gj_ids & mh_ids == set()
        assert all(i.startswith("R-") for i in mh_ids)
        assert not any(i.startswith("R-GIDC") for i in mh_ids)

    def test_gj_pack_contains_no_mh_rules(self):
        pack = load_regulatory_pack(IN_GJ)
        gj_ids = {r.id for r in pack.approval_rules}
        assert gj_ids & set(MH_INCLUDED_RULE_IDS) == set()

    def test_approval_namespaces_disjoint(self):
        mh_approvals = {
            r.approval_id for r in load_mh_approval_rules()
        }
        assert not any(
            a.startswith("A0") or a.startswith("A1") for a in mh_approvals
        )
        pack = load_regulatory_pack(IN_GJ)
        gj_approvals = {r.approval_id for r in pack.approval_rules}
        assert gj_approvals & mh_approvals == set()

    def test_mh_orchestration_uses_only_mh_inputs(self):
        pack = load_regulatory_pack(IN_MH)
        aids = sorted({r.approval_id for r in pack.approval_rules})
        facts = {
            "F-PRD-02": ["PESTICIDE_TECHNICAL"],
            "F-HW-01": True,
            "F-BLD-01": 30000,
            "F-LOC-01": True,
        }
        result = orchestrate_application_full(
            application_id="MH-B1",
            project_facts=facts,
            approval_rules=pack.approval_rules,
            approval_authorities=pack.approval_authorities,
            dependencies=[],
            all_approval_ids=aids,
            document_requirements=[],
            uploaded_documents=[],
            extraction_results=[],
            validation_results=[],
            consistency_result=None,
            sla_info=None,
            obtained_approvals=set(),
            evidence_gaps_by_approval=None,
        )
        assert set(result.approvals) == set(aids)
        assert result.approvals["APR-006"].applicability_result == "applies"
        assert result.approvals["APR-006"].status.value == "ready"
        assert result.approvals["APR-003"].applicability_result == "applies"
        # R-002 inputs missing -> fail closed, never does_not_apply.
        assert result.approvals["APR-001"].applicability_result == (
            "insufficient_data"
        )
