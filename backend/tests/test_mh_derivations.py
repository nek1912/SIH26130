"""IN-MH derived facts (F-PRC-03, F-INC-01; F-INC-03/F-INC-04 blocked).

Evidence (all in-repo v5 CSVs, nothing invented):
- F-INC-01 := R-057 MSME_CLASS bands (rules.csv/rule_register_v5.csv,
  SRC-061 GR MSME definition para): MICRO inv<=2.5 AND turnover<=10;
  SMALL inv<=25 AND turnover<=100; MEDIUM inv<=125 AND turnover<=500;
  else LARGE. Either input UNKNOWN -> UNKNOWN (ET-040/041/042/112).
- F-PRC-03 := R-091 MAH_DERIVED join semantics (rules.csv, SRC-016 /
  SRC-134, M1..M9): TRUE if any resolved chemical >= col 3; FALSE only
  if all inventory chemicals resolved and none >= col 3; else UNKNOWN
  (ET-127/ET-081/ET-v4-04/ET-v5-06). Runtime join is over the supplied
  F-HAZ-01 inventory and F-HAZ-02 schedule mapping only; the
  msihc_t1_thresholds table is evidence, never a runtime lookup (M2
  identity source unselected, CON-021 thresholds unconfirmed).
- F-INC-03 BLOCKED: INC-001 documents only "unit's sector falls in
  thrust sector #6" (SRC-061) with no input-fact mapping and no member
  list. F-INC-04 BLOCKED: R-058 is DO_NOT_IMPLEMENT_YET ("Annexure not
  digitised in this pack"); no taluka->basket table exists in-repo.
"""
from __future__ import annotations

import pytest

from app.rules.derivations import (
    derive_mah_status,
    derive_mh_facts,
    derive_msme_class,
)
from app.rules.facts import FactValidationError


class TestMsmeClassValid:
    def test_micro_boundary(self):
        assert derive_msme_class(2.5, 10) == "MICRO"

    def test_small_boundary(self):
        assert derive_msme_class(25, 100) == "SMALL"

    def test_medium_values(self):
        assert derive_msme_class(100, 400) == "MEDIUM"

    def test_large_values(self):
        assert derive_msme_class(200, 600) == "LARGE"

    def test_zero_is_micro(self):
        assert derive_msme_class(0, 0) == "MICRO"


class TestMsmeClassAndNotOr:
    def test_investment_micro_turnover_small_is_small(self):
        # AND within each band: inv fits MICRO but turnover does not.
        assert derive_msme_class(2.5, 100) == "SMALL"

    def test_small_investment_large_turnover_is_medium(self):
        assert derive_msme_class(1, 500) == "MEDIUM"

    def test_just_over_micro_investment(self):
        # ET-042: inv=2.6, turnover=9 -> SMALL.
        assert derive_msme_class(2.6, 9) == "SMALL"


class TestMsmeClassBoundaries:
    def test_turnover_just_over_micro(self):
        assert derive_msme_class(2.5, 10.01) == "SMALL"

    def test_medium_upper_boundary(self):
        assert derive_msme_class(125, 500) == "MEDIUM"

    def test_just_over_medium_investment(self):
        assert derive_msme_class(125.01, 500) == "LARGE"

    def test_just_over_medium_turnover(self):
        assert derive_msme_class(125, 500.01) == "LARGE"


class TestMsmeClassMissingUnknownInvalid:
    def test_none_investment_is_unknown(self):
        assert derive_msme_class(None, 10) is None

    def test_none_turnover_is_unknown(self):
        assert derive_msme_class(2.5, None) is None

    def test_unknown_token_investment_is_unknown(self):
        assert derive_msme_class("UNKNOWN", 10) is None

    def test_unknown_token_turnover_is_unknown(self):
        # ET-040: inv=2.5, turnover=UNKNOWN -> UNKNOWN.
        assert derive_msme_class(2.5, "UNKNOWN") is None

    def test_bool_rejected(self):
        assert derive_msme_class(True, 10) is None
        assert derive_msme_class(2.5, False) is None

    def test_string_rejected(self):
        assert derive_msme_class("2.5", 10) is None

    def test_negative_rejected(self):
        assert derive_msme_class(-1, 10) is None
        assert derive_msme_class(2.5, -10) is None


class TestMahStatusValid:
    def test_above_col3_is_mah(self):
        # ET-v4-04: ammonia 60 t vs col 3 (50 t) -> MAH.
        inventory = [{"chemical": "Ammonia", "max_qty_t": 60}]
        mapping = [{"chemical": "Ammonia", "schedule": "Sch3P1", "col3_t": 50}]
        assert derive_mah_status(inventory, mapping) is True

    def test_below_col3_all_resolved_is_not_mah(self):
        inventory = [{"chemical": "Ammonia", "max_qty_t": 40}]
        mapping = [{"chemical": "Ammonia", "schedule": "Sch3P1", "col3_t": 50}]
        assert derive_mah_status(inventory, mapping) is False

    def test_exact_col3_is_mah(self):
        inventory = [{"chemical": "X", "max_qty_t": 50}]
        mapping = [{"chemical": "X", "schedule": "Sch2", "col3_t": 50}]
        assert derive_mah_status(inventory, mapping) is True

    def test_empty_inventory_is_not_mah(self):
        assert derive_mah_status([], [{"chemical": "X", "col3_t": 50}]) is False


class TestMahStatusUnknown:
    def test_unmapped_chemical_is_unknown(self):
        # ET-081 / ET-127: unresolved chemical -> UNKNOWN, never FALSE.
        inventory = [
            {"chemical": "Ammonia", "max_qty_t": 40},
            {"chemical": "MysterySolvent", "max_qty_t": 1},
        ]
        mapping = [{"chemical": "Ammonia", "schedule": "Sch3P1", "col3_t": 50}]
        assert derive_mah_status(inventory, mapping) is None

    def test_true_dominates_unresolved(self):
        # R-091: TRUE if ANY resolved chemical >= col 3.
        inventory = [
            {"chemical": "Ammonia", "max_qty_t": 60},
            {"chemical": "MysterySolvent", "max_qty_t": 1},
        ]
        mapping = [{"chemical": "Ammonia", "schedule": "Sch3P1", "col3_t": 50}]
        assert derive_mah_status(inventory, mapping) is True

    def test_missing_inventory_is_unknown(self):
        assert derive_mah_status(None, [{"chemical": "X", "col3_t": 50}]) is None

    def test_missing_mapping_is_unknown(self):
        assert derive_mah_status([{"chemical": "X", "max_qty_t": 60}], None) is None

    def test_item_missing_qty_is_unknown(self):
        inventory = [{"chemical": "Ammonia"}]
        mapping = [{"chemical": "Ammonia", "schedule": "Sch3P1", "col3_t": 50}]
        assert derive_mah_status(inventory, mapping) is None

    def test_mapping_missing_col3_is_unknown(self):
        inventory = [{"chemical": "Ammonia", "max_qty_t": 60}]
        mapping = [{"chemical": "Ammonia", "schedule": "Sch3P1"}]
        assert derive_mah_status(inventory, mapping) is None

    def test_non_list_inputs_are_unknown(self):
        assert derive_mah_status("Ammonia", [{"chemical": "Ammonia"}]) is None
        assert derive_mah_status([{"chemical": "X"}], "Ammonia") is None


class TestDeriveMhFacts:
    def test_fills_missing_derived_only(self):
        facts = {
            "F-INC-02": 2.5,
            "F-INC-09": 10,
            "F-HAZ-01": [{"chemical": "Ammonia", "max_qty_t": 40}],
            "F-HAZ-02": [
                {"chemical": "Ammonia", "schedule": "Sch3P1", "col3_t": 50}
            ],
        }
        derived = derive_mh_facts(facts)
        assert derived == {"F-INC-01": "MICRO", "F-PRC-03": False}

    def test_never_overrides_supplied_value(self):
        facts = {
            "F-INC-01": "LARGE",
            "F-INC-02": 2.5,
            "F-INC-09": 10,
            "F-PRC-03": True,
            "F-HAZ-01": [{"chemical": "Ammonia", "max_qty_t": 40}],
            "F-HAZ-02": [
                {"chemical": "Ammonia", "schedule": "Sch3P1", "col3_t": 50}
            ],
        }
        assert derive_mh_facts(facts) == {}

    def test_missing_sources_yield_nothing(self):
        assert derive_mh_facts({}) == {}
        assert derive_mh_facts({"F-INC-02": 2.5}) == {}

    def test_unknown_sources_propagate(self):
        facts = {"F-INC-02": 2.5, "F-INC-09": "UNKNOWN"}
        assert derive_mh_facts(facts) == {}

    def test_blocked_facts_never_derived(self):
        # F-INC-03 (no input mapping) and F-INC-04 (no taluka table):
        # presence of candidate inputs must not produce values.
        facts = {"F-LOC-04": "Vagra", "F-PRD-02": ["BULK_DRUG"]}
        derived = derive_mh_facts(facts)
        assert "F-INC-03" not in derived
        assert "F-INC-04" not in derived

    def test_does_not_mutate_inputs(self):
        facts = {"F-INC-02": 2.5, "F-INC-09": 10}
        derive_mh_facts(facts)
        assert facts == {"F-INC-02": 2.5, "F-INC-09": 10}


class TestJurisdictionIsolation:
    def test_gj_rejected(self):
        with pytest.raises(FactValidationError) as exc:
            derive_mh_facts({"F-INC-02": 2.5}, jurisdiction="IN-GJ")
        assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH

    def test_unknown_jurisdiction_rejected(self):
        with pytest.raises(FactValidationError) as exc:
            derive_mh_facts({}, jurisdiction="IN-XX")
        assert exc.value.code == FactValidationError.UNKNOWN_JURISDICTION

    def test_explicit_in_mh_accepted(self):
        assert derive_mh_facts(
            {"F-INC-02": 2.5, "F-INC-09": 10}, jurisdiction="IN-MH"
        ) == {"F-INC-01": "MICRO"}
