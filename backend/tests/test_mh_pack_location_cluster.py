"""Tests for Maharashtra Location Cluster (R-077, R-096, R-083, R-084) and related rules.

Covers:
- R-077: CGWA NOC - groundwater abstraction (over-exploited assessment unit)
- R-083: CRZ category of site (CRZ Notification 2019)
- R-084: Forest land involved (Van Adhiniyam 1980 / Rules 2023)
- R-096: Hazardous waste authorisation Schedule II characteristic test
- R-085: Deferred verification (missing EC_REQUIRED precondition fact)
- R-060 & R-061: Deferred verification
- R-091: Partial derivation semantics verification (M3, M7, M9)
- Location facts UNKNOWN fail-closed behavior
- Jurisdiction isolation (IN-MH only, IN-GJ unaffected)
"""
from __future__ import annotations

from datetime import date

import pytest

from app.rules.applicability import evaluate_rule
from app.rules.derivations import derive_mah_status
from app.rules.models import ApprovalResult
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.pack import IN_GJ, IN_MH, load_regulatory_pack


def _rules_by_id():
    return {r.id: r for r in load_mh_approval_rules()}


def _eval(rule_id: str, facts: dict, evaluation_date: date | None = None):
    rules = _rules_by_id()
    assert rule_id in rules, f"Rule {rule_id} not loaded in MH approval rules"
    return evaluate_rule(rules[rule_id], facts, evaluation_date=evaluation_date)


class TestLocationClusterPackInclusion:
    """Verify pack inclusion and isolation for the location cluster."""

    def test_implemented_rules_included(self):
        rules = _rules_by_id()
        assert "R-077" in rules
        assert "R-083" in rules
        assert "R-084" in rules
        assert "R-096" in rules
        assert {"R-077", "R-083", "R-084", "R-096"} <= set(MH_INCLUDED_RULE_IDS)

    def test_total_mh_rule_count(self):
        # 22 (batch 1 + batch 2) + 4 (location cluster) = 26
        assert len(load_mh_approval_rules()) == 26

    def test_source_refs_present(self):
        rules = _rules_by_id()
        assert rules["R-077"].source_refs[0].source_id == "SRC-052"
        assert rules["R-083"].source_refs[0].source_id == "SRC-112"
        assert rules["R-084"].source_refs[0].source_id == "SRC-113"
        assert rules["R-096"].source_refs[0].source_id == "SRC-120"

    def test_all_rule_authorities_defined(self):
        pack = load_regulatory_pack(IN_MH)
        authorities = pack.approval_authorities
        assert "APR-043" in authorities
        assert "APR-010" in authorities
        assert "LOC-CRZ" in authorities
        assert "LOC-FOREST" in authorities
        for r in load_mh_approval_rules():
            assert r.approval_id in authorities, f"Missing authority for {r.approval_id}"

    def test_sources_loaded_in_mh_pack(self):
        pack = load_regulatory_pack(IN_MH)
        source_ids = {s.id for s in pack.sources}
        assert "SRC-052" in source_ids
        assert "SRC-112" in source_ids
        assert "SRC-113" in source_ids
        assert "SRC-120" in source_ids

    def test_gj_pack_isolation(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        gj_rule_ids = {r.id for r in gj_pack.approval_rules}
        assert {"R-077", "R-083", "R-084", "R-096"} & gj_rule_ids == set()

    def test_deferred_rules_not_in_pack(self):
        rules = _rules_by_id()
        assert "R-060" not in rules
        assert "R-061" not in rules
        assert "R-085" not in rules
        assert "R-091" not in rules
        assert "R-060" in MH_DEFERRED_RULES
        assert "R-061" in MH_DEFERRED_RULES
        assert "R-085" in MH_DEFERRED_RULES
        assert "R-091" in MH_DEFERRED_RULES


class TestR077GroundwaterOverExploited:
    """R-077: CGWA NOC for groundwater abstraction in over-exploited assessment units.

    Condition: F-GW-01 == 'OVER_EXPLOITED' AND (
        (F-EXP-01 == False AND F-INC-01 NOT IN {MICRO, SMALL, MEDIUM})
        OR F-EXP-01 == True
    )
    """

    def test_applies_new_large_industry_in_oe(self):
        res = _eval("R-077", {
            "F-GW-01": "OVER_EXPLOITED",
            "F-EXP-01": False,
            "F-INC-01": "LARGE",
        })
        assert res.result == ApprovalResult.APPLIES

    def test_applies_expansion_in_oe_regardless_of_msme(self):
        for msme in ("MICRO", "SMALL", "MEDIUM", "LARGE"):
            res = _eval("R-077", {
                "F-GW-01": "OVER_EXPLOITED",
                "F-EXP-01": True,
                "F-INC-01": msme,
            })
            assert res.result == ApprovalResult.APPLIES

    def test_does_not_apply_new_micro_in_oe(self):
        res = _eval("R-077", {
            "F-GW-01": "OVER_EXPLOITED",
            "F-EXP-01": False,
            "F-INC-01": "MICRO",
        })
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_does_not_apply_new_small_in_oe(self):
        res = _eval("R-077", {
            "F-GW-01": "OVER_EXPLOITED",
            "F-EXP-01": False,
            "F-INC-01": "SMALL",
        })
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_does_not_apply_new_medium_in_oe(self):
        res = _eval("R-077", {
            "F-GW-01": "OVER_EXPLOITED",
            "F-EXP-01": False,
            "F-INC-01": "MEDIUM",
        })
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_does_not_apply_in_safe_unit(self):
        res = _eval("R-077", {
            "F-GW-01": "SAFE",
            "F-EXP-01": False,
            "F-INC-01": "LARGE",
        })
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_does_not_apply_in_semi_critical_unit(self):
        res = _eval("R-077", {
            "F-GW-01": "SEMI_CRITICAL",
            "F-EXP-01": True,
            "F-INC-01": "LARGE",
        })
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_does_not_apply_in_critical_unit(self):
        res = _eval("R-077", {
            "F-GW-01": "CRITICAL",
            "F-EXP-01": False,
            "F-INC-01": "LARGE",
        })
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_unknown_location_fails_closed_to_insufficient_data(self):
        res = _eval("R-077", {
            "F-GW-01": "UNKNOWN",
            "F-EXP-01": False,
            "F-INC-01": "LARGE",
        })
        assert res.result in (ApprovalResult.INSUFFICIENT_DATA, ApprovalResult.CONDITIONAL)
        assert res.result != ApprovalResult.DOES_NOT_APPLY

    def test_missing_gw_fact_fails_closed(self):
        res = _eval("R-077", {
            "F-EXP-01": False,
            "F-INC-01": "LARGE",
        })
        assert res.result in (ApprovalResult.INSUFFICIENT_DATA, ApprovalResult.CONDITIONAL)
        assert res.result != ApprovalResult.DOES_NOT_APPLY

    def test_missing_msme_class_when_new_in_oe_fails_closed(self):
        res = _eval("R-077", {
            "F-GW-01": "OVER_EXPLOITED",
            "F-EXP-01": False,
        })
        assert res.result in (ApprovalResult.INSUFFICIENT_DATA, ApprovalResult.CONDITIONAL)
        assert res.result != ApprovalResult.DOES_NOT_APPLY

    def test_effective_window(self):
        facts = {
            "F-GW-01": "OVER_EXPLOITED",
            "F-EXP-01": False,
            "F-INC-01": "LARGE",
        }
        # Effective from 2020-09-24
        before = _eval("R-077", facts, evaluation_date=date(2020, 9, 23))
        assert before.result == ApprovalResult.DOES_NOT_APPLY
        assert "not in force" in before.reason

        on_date = _eval("R-077", facts, evaluation_date=date(2020, 9, 24))
        assert on_date.result == ApprovalResult.APPLIES


class TestR083CoastalRegulationZone:
    """R-083: CRZ Notification 2019 applicability.

    Condition: F-GEO-01 IN {CRZ-I, CRZ-II, CRZ-III, CRZ-IV}
    """

    @pytest.mark.parametrize("cat", ["CRZ-I", "CRZ-II", "CRZ-III", "CRZ-IV"])
    def test_applies_in_crz_categories(self, cat: str):
        res = _eval("R-083", {"F-GEO-01": cat})
        assert res.result == ApprovalResult.APPLIES

    def test_does_not_apply_outside_crz(self):
        res = _eval("R-083", {"F-GEO-01": "NOT_IN_CRZ"})
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_unknown_crz_fails_closed(self):
        res = _eval("R-083", {"F-GEO-01": "UNKNOWN"})
        assert res.result in (ApprovalResult.INSUFFICIENT_DATA, ApprovalResult.CONDITIONAL)
        assert res.result != ApprovalResult.DOES_NOT_APPLY

    def test_missing_crz_fails_closed(self):
        res = _eval("R-083", {})
        assert res.result == ApprovalResult.INSUFFICIENT_DATA

    def test_effective_window(self):
        facts = {"F-GEO-01": "CRZ-I"}
        # Effective from 2019-01-18
        before = _eval("R-083", facts, evaluation_date=date(2019, 1, 17))
        assert before.result == ApprovalResult.DOES_NOT_APPLY
        assert "not in force" in before.reason

        on_date = _eval("R-083", facts, evaluation_date=date(2019, 1, 18))
        assert on_date.result == ApprovalResult.APPLIES


class TestR084ForestLand:
    """R-084: Van (Sanrakshan Evam Samvardhan) Adhiniyam 1980 / Rules 2023.

    Condition: F-LOC-15 == True
    """

    def test_applies_when_forest_land_involved(self):
        res = _eval("R-084", {"F-LOC-15": True})
        assert res.result == ApprovalResult.APPLIES

    def test_does_not_apply_when_no_forest_land(self):
        res = _eval("R-084", {"F-LOC-15": False})
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_unknown_forest_land_fails_closed(self):
        res = _eval("R-084", {"F-LOC-15": "UNKNOWN"})
        assert res.result in (ApprovalResult.INSUFFICIENT_DATA, ApprovalResult.CONDITIONAL)
        assert res.result != ApprovalResult.DOES_NOT_APPLY

    def test_missing_forest_land_fails_closed(self):
        res = _eval("R-084", {})
        assert res.result == ApprovalResult.INSUFFICIENT_DATA

    def test_effective_window(self):
        facts = {"F-LOC-15": True}
        # Effective from 2023-12-01
        before = _eval("R-084", facts, evaluation_date=date(2023, 11, 30))
        assert before.result == ApprovalResult.DOES_NOT_APPLY
        assert "not in force" in before.reason

        on_date = _eval("R-084", facts, evaluation_date=date(2023, 12, 1))
        assert on_date.result == ApprovalResult.APPLIES


class TestR096HazardousWasteScheduleII:
    """R-096: Hazardous waste authorisation Schedule II characteristic test.

    Condition: F-HW-04 contains matching characteristics (Class A, B, C1, C2, C3).
    """

    @pytest.mark.parametrize("characteristic", [
        "CLASS_A", "CLASS_B", "CLASS_C1", "CLASS_C2", "CLASS_C3",
        "CLASS_A_TCLP", "CLASS_C1_FLAMMABLE", "CLASS_C2_CORROSIVE",
        "CLASS_C3_REACTIVE", "HAZARDOUS", "MEETS_SCHEDULE_II",
    ])
    def test_applies_with_matching_characteristic(self, characteristic: str):
        res = _eval("R-096", {"F-HW-04": [characteristic]})
        assert res.result == ApprovalResult.APPLIES

    def test_does_not_apply_with_empty_lab_results(self):
        res = _eval("R-096", {"F-HW-04": []})
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_does_not_apply_with_non_hazardous_results(self):
        res = _eval("R-096", {"F-HW-04": ["NON_HAZARDOUS", "WITHIN_LIMITS"]})
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_unknown_lab_data_fails_closed_to_insufficient_data(self):
        res = _eval("R-096", {"F-HW-04": "UNKNOWN"})
        assert res.result in (ApprovalResult.INSUFFICIENT_DATA, ApprovalResult.CONDITIONAL)
        assert res.result != ApprovalResult.DOES_NOT_APPLY

    def test_missing_lab_data_fails_closed_to_insufficient_data(self):
        res = _eval("R-096", {})
        assert res.result == ApprovalResult.INSUFFICIENT_DATA

    def test_effective_window(self):
        facts = {"F-HW-04": ["CLASS_A"]}
        # Effective from 2016-04-04
        before = _eval("R-096", facts, evaluation_date=date(2016, 4, 3))
        assert before.result == ApprovalResult.DOES_NOT_APPLY
        assert "not in force" in before.reason

        on_date = _eval("R-096", facts, evaluation_date=date(2016, 4, 4))
        assert on_date.result == ApprovalResult.APPLIES


class TestDeferredRulesGating:
    """Verify deferred rules remain deferred with clear documented reasons."""

    def test_r085_deferred_due_to_missing_ec_required_fact(self):
        assert "R-085" in MH_DEFERRED_RULES
        assert "EC_REQUIRED" in MH_DEFERRED_RULES["R-085"]

    def test_r060_deferred_due_to_existential_quantifier(self):
        assert "R-060" in MH_DEFERRED_RULES

    def test_r061_deferred_due_to_aggregation(self):
        assert "R-061" in MH_DEFERRED_RULES

    def test_r091_deferred_due_to_unselected_identity_and_thresholds(self):
        assert "R-091" in MH_DEFERRED_RULES


class TestR091PartialDerivationSemantics:
    """Verify R-091 M3-M7-M9 derivation in derive_mah_status()."""

    def test_verified_chemical_exceeds_threshold_is_true(self):
        inventory = [{"chemical": "Ammonia", "max_qty_t": 60.0}]
        mapping = [{"chemical": "Ammonia", "col3_t": 50.0}]
        assert derive_mah_status(inventory, mapping) is True

    def test_verified_chemical_below_threshold_is_false(self):
        inventory = [{"chemical": "Ammonia", "max_qty_t": 30.0}]
        mapping = [{"chemical": "Ammonia", "col3_t": 50.0}]
        assert derive_mah_status(inventory, mapping) is False

    def test_exact_threshold_boundary_is_true(self):
        inventory = [{"chemical": "Ammonia", "max_qty_t": 50.0}]
        mapping = [{"chemical": "Ammonia", "col3_t": 50.0}]
        assert derive_mah_status(inventory, mapping) is True

    def test_unresolved_chemical_returns_unknown(self):
        inventory = [
            {"chemical": "Ammonia", "max_qty_t": 30.0},
            {"chemical": "UnknownSolvent", "max_qty_t": 10.0},
        ]
        mapping = [{"chemical": "Ammonia", "col3_t": 50.0}]
        # Second chemical has no mapping -> UNKNOWN (never False!)
        assert derive_mah_status(inventory, mapping) is None

    def test_true_dominance_over_unresolved_chemical(self):
        inventory = [
            {"chemical": "Ammonia", "max_qty_t": 60.0},  # Exceeds col3
            {"chemical": "UnknownSolvent", "max_qty_t": 10.0},  # Unresolved
        ]
        mapping = [{"chemical": "Ammonia", "col3_t": 50.0}]
        # Ammonia exceeds col3 -> TRUE dominates even with unresolved chemical
        assert derive_mah_status(inventory, mapping) is True

    def test_empty_inventory_is_false(self):
        assert derive_mah_status([], [{"chemical": "Ammonia", "col3_t": 50.0}]) is False

    def test_none_inventory_or_mapping_returns_none(self):
        assert derive_mah_status(None, []) is None
        assert derive_mah_status([], None) is None
