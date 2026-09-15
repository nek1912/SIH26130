"""Tests for workbook seed data loading and validation."""
from __future__ import annotations

from app.rules.applicability import _collect_required_inputs
from app.rules.models import (
    ApplicabilityCondition,
    ApplicabilityOp,
)
from app.rules.validation import validate_applicability_conditions
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.scenario import load_scenario


def _cond(field: str, op: str, value) -> ApplicabilityCondition:
    return ApplicabilityCondition(field=field, op=ApplicabilityOp(op), value=value)


class TestScenarioLoading:
    def test_load_scenario_returns_dict(self):
        scenario = load_scenario()
        assert isinstance(scenario, dict)
        assert len(scenario) > 0

    def test_scenario_has_required_fields(self):
        scenario = load_scenario()
        required = [
            "state",
            "estate",
            "district",
            "plot_area_sqm",
            "industry_type",
            "hazardous_process",
            "building_height",
            "power_demand",
            "workers_total",
            "groundwater_use",
        ]
        for field in required:
            assert field in scenario, f"Missing required field: {field}"

    def test_scenario_values_match_workbook(self):
        scenario = load_scenario()
        assert scenario["state"] == "Gujarat"
        assert scenario["estate"] == "Dahej-II"
        assert scenario["plot_area_sqm"] == 12000
        assert scenario["building_height"] == 18
        assert scenario["power_demand"] == 1000
        assert scenario["hazardous_process"] is True
        assert scenario["groundwater_use"] is False

    def test_unresolved_fields_preserved(self):
        scenario = load_scenario()
        assert (
            scenario["forest_or_protected_area_overlap"]
            == "UNRESOLVED_AT_PLOT_LEVEL"
        )
        assert (
            scenario["coastal_regulation_zone_status"]
            == "UNRESOLVED_AT_PLOT_LEVEL"
        )

    def test_scenario_facts_valid_in_engine(self):
        test_conditions = [
            _cond("plot_area_sqm", "gte", 10000),
            _cond("building_height", "gt", 15),
            _cond("hazardous_process", "eq", True),
            _cond("power_demand", "gte", 100),
            _cond("groundwater_use", "eq", False),
            _cond("workers_total", "gte", 50),
        ]
        result = validate_applicability_conditions(test_conditions)
        assert result.ok is True, f"Validation issues: {result.issues}"


class TestApprovalRules:
    def test_load_returns_19_rules(self):
        rules = load_approval_rules()
        assert len(rules) == 19

    def test_all_rules_have_ids(self):
        rules = load_approval_rules()
        for rule in rules:
            assert rule.id, f"Rule missing id: {rule}"
            assert rule.approval_id, f"Rule missing approval_id: {rule}"

    def test_all_rules_have_source_refs(self):
        rules = load_approval_rules()
        for rule in rules:
            assert len(rule.source_refs) > 0, f"Rule {rule.id} has no source_refs"

    def test_all_rules_have_conditions(self):
        rules = load_approval_rules()
        for rule in rules:
            assert len(rule.applicability_conditions) > 0, (
                f"Rule {rule.id} has no conditions"
            )

    def test_authorities_mapping_complete(self):
        rules = load_approval_rules()
        authorities = load_approval_authorities()
        for rule in rules:
            assert rule.approval_id in authorities, (
                f"Rule {rule.id} approval_id {rule.approval_id} not in authorities"
            )

    def test_unique_rule_ids(self):
        rules = load_approval_rules()
        ids = [r.id for r in rules]
        assert len(ids) == len(set(ids)), f"Duplicate rule IDs: {ids}"

    def test_approval_ids_cover_all_18(self):
        rules = load_approval_rules()
        ids = {r.approval_id for r in rules}
        expected_ids = {f"A{str(i).zfill(2)}" for i in range(1, 19)}
        assert ids == expected_ids

    def test_required_inputs_cover_domain_fields(self):
        rules = load_approval_rules()
        all_inputs: set[str] = set()
        for rule in rules:
            all_inputs |= set(_collect_required_inputs(rule))
        assert "plot_area_sqm" in all_inputs
        assert "building_height" in all_inputs
        assert "power_demand" in all_inputs
        assert "hazardous_process" in all_inputs
        assert "groundwater_use" in all_inputs
