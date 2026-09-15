"""Tests comparing engine results against workbook Expected_Test_Results."""
from __future__ import annotations

from app.rules.applicability import (
    evaluate_approval_applicability,
    evaluate_rule,
    summarize_by_approval,
    summarize_evaluations,
)
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.expected import load_expected_results
from app.seed.scenario import load_scenario


class TestExpectedResults:
    def test_expected_results_loadable(self):
        results = load_expected_results()
        assert len(results) == 15

    def test_all_expected_have_required_fields(self):
        results = load_expected_results()
        for r in results:
            assert "test_id" in r
            assert "expected_outcome" in r
            assert "type" in r

    def test_deterministic_t01_applies(self):
        """T01: GIDC Plan - plot_area 12000 + chemical industry -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A01" in results
        assert results["A01"].result == "applies"
        assert "R-GIDC-001" in results["A01"].rule_id

    def test_deterministic_t08_applies(self):
        """T08: HT Electricity - power_demand 1000 -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A09" in results
        assert results["A09"].result == "applies"

    def test_negative_t12_does_not_apply(self):
        """T12: CGWA - groundwater_use=false -> does_not_apply."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A18" in results
        assert results["A18"].result == "does_not_apply"

    def test_prerequisite_t03_applies(self):
        """T03: GIDC Water - chemical unit -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A02" in results
        assert results["A02"].result == "applies"

    def test_prerequisite_t10_applies(self):
        """T10: Factory Registration - 60 workers + hazardous process -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A07" in results
        assert results["A07"].result == "applies"

    def test_summary_structure(self):
        """Summary has all four outcome types."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        summary = summarize_evaluations(evaluations)
        assert "applies" in summary
        assert "does_not_apply" in summary
        assert "conditional" in summary
        assert "insufficient_data" in summary
        assert summary["applies"] > 0

    def test_all_approvals_evaluated(self):
        """Each of the 18 approvals produces at least one evaluation."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        approval_ids = {e.approval_id for e in evaluations}
        expected_ids = {f"A{str(i).zfill(2)}" for i in range(1, 19)}
        assert approval_ids == expected_ids

    def test_source_references_preserved(self):
        """Every evaluation has at least one source reference."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        for e in evaluations:
            assert len(e.source_references) > 0, (
                f"Evaluation {e.rule_id} has no source references"
            )

    def test_rule_ids_traceable(self):
        """Every evaluation has a non-empty rule_id."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        for e in evaluations:
            assert e.rule_id, f"Evaluation for {e.approval_id} has no rule_id"

    def test_system_test_t15_excluded(self):
        """T15 (SYSTEM_TEST) is outside engine scope - marked in expected."""
        expected = load_expected_results()
        system_tests = [r for r in expected if r["type"] == "SYSTEM_TEST"]
        assert len(system_tests) == 1
        assert system_tests[0]["test_id"] == "T15"
        assert system_tests[0]["expected_outcome"] == "system_test"

    def test_t06_fire_general_applies(self):
        """T06: R-FIRE-001 general fire safety — hazardous building exists -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        fire_rules = [e for e in evaluations if e.rule_id == "R-FIRE-001"]
        assert len(fire_rules) == 1
        assert fire_rules[0].result == "applies"
        assert fire_rules[0].approval_id == "A06"

    def test_t07_fire_height_prohibition_does_not_apply(self):
        """T07: R-FIRE-004 height prohibition — 18m > 15m limit -> does_not_apply."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        fire_height = [e for e in evaluations if e.rule_id == "R-FIRE-004"]
        assert len(fire_height) == 1
        assert fire_height[0].result == "does_not_apply"
        assert fire_height[0].approval_id == "A06"

    def test_a06_approval_aggregate_applies(self):
        """A06 as a whole applies because R-FIRE-001 is satisfied."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        aggregated = summarize_by_approval(evaluations)
        assert "A06" in aggregated
        assert aggregated["A06"].result == "applies"

    def test_t11_howm_applies(self):
        """T11: HOWM authorization - hazardous waste generated."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A11" in results
        assert results["A11"].result == "applies"

    def test_t13_lift_applies(self):
        """T13: Lift present = true -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A15" in results
        assert results["A15"].result == "applies"

    def test_t14_boiler_applies(self):
        """T14: Boiler present = true -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A16" in results
        assert results["A16"].result == "applies"

    def test_t05_eia_applies(self):
        """T05: EIA 5(f) - synthetic organic + 20000 MT/yr -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A05" in results
        assert results["A05"].result == "applies"

    def test_t04_drainage_applies(self):
        """T04: GIDC drainage - effluent > 0 + ETP >= 1 -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A03" in results
        assert results["A03"].result == "applies"

    def test_t09_ceiced_applies(self):
        """T09: CEICED inspection - power_demand >= 100 -> applies."""
        scenario = load_scenario()
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        evaluations = evaluate_approval_applicability(
            rules, scenario, authorities
        )
        results = {e.approval_id: e for e in evaluations}
        assert "A10" in results
        assert results["A10"].result == "applies"


class TestFireSafetyEdgeCases:
    """Additional tests for the split fire safety rules (A06)."""

    def test_hazardous_building_at_15m_both_rules_apply(self):
        """A hazardous building at exactly 15m: both R-FIRE-001 and R-FIRE-004 apply."""
        facts = {
            "hazardous_process": True,
            "building_height": 15,
        }
        rules = load_approval_rules()
        fire_rules = [r for r in rules if r.approval_id == "A06"]
        assert len(fire_rules) == 2

        results = []
        for rule in fire_rules:
            eval_result = evaluate_rule(rule, facts)
            results.append(eval_result)

        r001 = [e for e in results if e.rule_id == "R-FIRE-001"][0]
        r004 = [e for e in results if e.rule_id == "R-FIRE-004"][0]
        assert r001.result == "applies"
        assert r004.result == "applies"

    def test_hazardous_building_above_15m_general_applies_height_blocks(self):
        """A hazardous building at 18m: R-FIRE-001 applies, R-FIRE-004 does_not_apply."""
        facts = {
            "hazardous_process": True,
            "building_height": 18,
        }
        rules = load_approval_rules()
        fire_rules = [r for r in rules if r.approval_id == "A06"]

        results = []
        for rule in fire_rules:
            eval_result = evaluate_rule(rule, facts)
            results.append(eval_result)

        r001 = [e for e in results if e.rule_id == "R-FIRE-001"][0]
        r004 = [e for e in results if e.rule_id == "R-FIRE-004"][0]
        assert r001.result == "applies"
        assert r004.result == "does_not_apply"

    def test_non_hazardous_building_neither_rule_applies(self):
        """A non-hazardous building: neither fire rule applies."""
        facts = {
            "hazardous_process": False,
            "building_height": 10,
        }
        rules = load_approval_rules()
        fire_rules = [r for r in rules if r.approval_id == "A06"]

        results = []
        for rule in fire_rules:
            eval_result = evaluate_rule(rule, facts)
            results.append(eval_result)

        for e in results:
            assert e.result == "does_not_apply"

    def test_no_building_height_fact_rfire001_insufficient(self):
        """R-FIRE-001 without building_height: hazardous_process=True but height missing."""
        facts = {
            "hazardous_process": True,
        }
        rules = load_approval_rules()
        rfire001 = [r for r in rules if r.id == "R-FIRE-001"][0]
        eval_result = evaluate_rule(rfire001, facts)
        assert eval_result.result == "insufficient_data"

    def test_no_building_height_fact_rfire004_insufficient(self):
        """R-FIRE-004 without building_height: hazardous_process=True but height missing."""
        facts = {
            "hazardous_process": True,
        }
        rules = load_approval_rules()
        rfire004 = [r for r in rules if r.id == "R-FIRE-004"][0]
        eval_result = evaluate_rule(rfire004, facts)
        assert eval_result.result == "insufficient_data"

    def test_fire_rules_share_source(self):
        """Both fire rules reference the same source S07."""
        rules = load_approval_rules()
        fire_rules = [r for r in rules if r.approval_id == "A06"]
        for rule in fire_rules:
            source_ids = [s.source_id for s in rule.source_refs]
            assert "S07" in source_ids

    def test_fire_rules_have_distinct_ids(self):
        """R-FIRE-001 and R-FIRE-004 are distinct rules."""
        rules = load_approval_rules()
        fire_rules = [r for r in rules if r.approval_id == "A06"]
        rule_ids = [r.id for r in fire_rules]
        assert "R-FIRE-001" in rule_ids
        assert "R-FIRE-004" in rule_ids
        assert len(rule_ids) == len(set(rule_ids))
