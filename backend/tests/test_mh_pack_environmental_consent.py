"""Tests for Maharashtra Environmental / Consent Cluster (R-003, R-004, R-007, R-008, R-013, R-014).

This suite audits and verifies the environmental and consent cluster rules:
- R-007: Prior EC - Item 8(a) Building & construction (ALREADY IMPLEMENTED in Batch 1)
  Predicate: F-BLD-01 >= 20000 AND F-BLD-01 < 150000. Verified active in pack.
- R-003: Prior EC Item 5(f) Category A vs B appraisal determination - DEFERRED
  Reason: Category determination (CAT_BASE := A | B), not an approval applicability
  predicate; both Cat A and B require Prior EC (APR-001); encoding as an approval rule
  would falsely negate EC for Category B units; requires cross-rule composition with R-002.
- R-004: Prior EC Item 5(f) General Condition category escalation - DEFERRED
  Reason: Category escalation rule modifying appraisal authority, not an approval
  applicability predicate; requires cross-rule composition with R-003 and existential
  sub-fact evaluation over F-LOC-07.
- R-008: Prior EC Item 8(a) General Condition negative declaration - DEFERRED
  Reason: Meta-rule declaring General Condition category escalation inoperative for
  Item 8(a); not an independent approval applicability predicate; encoding under APR-003
  would contradict R-007.
- R-013: Consent to Establish Red/Orange/Green trigger - DEFERRED
  Reason: Requires rule composition with R-014 sector lookup and unmodeled fact
  MPCB_CATEGORY; standalone encoding cannot evaluate against F-MPCB-01 codes without
  lookup engine capability; multi-code cardinality guard R-015 emits UNKNOWN.
- R-014: CPCB sector code to pollution category lookup - DEFERRED
  Reason: Sector classification lookup function (operator LOOKUP), not an approval
  applicability predicate; full sector table not digitized; multi-activity cardinality
  guard R-015 emits UNKNOWN.

Jurisdiction isolation and fail-closed safety are verified throughout.
"""
from __future__ import annotations

import pytest

from app.rules.applicability import evaluate_rule
from app.rules.facts import (
    FactValueType,
    get_fact_spec,
)
from app.rules.models import ApprovalResult
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

AUDITED_CLUSTER_RULE_IDS: frozenset[str] = frozenset({
    "R-003",
    "R-004",
    "R-007",
    "R-008",
    "R-013",
    "R-014",
})

DEFERRED_CLUSTER_RULE_IDS: frozenset[str] = frozenset({
    "R-003",
    "R-004",
    "R-008",
    "R-013",
    "R-014",
})


def _by_id(rule_id: str):
    for r in load_mh_approval_rules():
        if r.id == rule_id:
            return r
    raise KeyError(rule_id)


class TestR007AlreadyImplemented:
    """Verify R-007 (EIA Item 8(a)) remains correctly active and functioning in MH pack."""

    def test_r007_in_active_pack(self):
        rules = load_mh_approval_rules()
        active_ids = {r.id for r in rules}
        assert "R-007" in active_ids
        assert "R-007" in MH_INCLUDED_RULE_IDS
        assert "R-007" not in MH_DEFERRED_RULES

    def test_r007_approval_id_and_sources(self):
        rule = _by_id("R-007")
        assert rule.approval_id == "APR-003"
        source_ids = [ref.source_id for ref in rule.source_refs]
        assert "SRC-001" in source_ids
        assert "SRC-179" in source_ids

    def test_r007_boundary_exact_lower_bound(self):
        """20,000 m2 is exactly on the lower boundary (inclusive) -> APPLIES (ET-002)."""
        res = evaluate_rule(_by_id("R-007"), {"F-BLD-01": 20000})
        assert res.result == ApprovalResult.APPLIES

    def test_r007_boundary_just_below_lower(self):
        """19,999 m2 is below the lower boundary -> DOES_NOT_APPLY (ET-001)."""
        res = evaluate_rule(_by_id("R-007"), {"F-BLD-01": 19999})
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_r007_boundary_just_above_lower(self):
        """20,001 m2 is above lower boundary -> APPLIES (ET-003)."""
        res = evaluate_rule(_by_id("R-007"), {"F-BLD-01": 20001})
        assert res.result == ApprovalResult.APPLIES

    def test_r007_boundary_just_below_upper(self):
        """149,999 m2 is below upper boundary -> APPLIES (ET-056)."""
        res = evaluate_rule(_by_id("R-007"), {"F-BLD-01": 149999})
        assert res.result == ApprovalResult.APPLIES

    def test_r007_boundary_exact_upper(self):
        """150,000 m2 is on upper bound (exclusive for 8(a)) -> DOES_NOT_APPLY (ET-005)."""
        res = evaluate_rule(_by_id("R-007"), {"F-BLD-01": 150000})
        assert res.result == ApprovalResult.DOES_NOT_APPLY

    def test_r007_unknown_fail_closed(self):
        """Missing or UNKNOWN built-up area fails closed to INSUFFICIENT_DATA (ET-004)."""
        res_missing = evaluate_rule(_by_id("R-007"), {})
        assert res_missing.result == ApprovalResult.INSUFFICIENT_DATA

        res_unknown = evaluate_rule(_by_id("R-007"), {"F-BLD-01": "UNKNOWN"})
        assert res_unknown.result == ApprovalResult.INSUFFICIENT_DATA


class TestDeferredEnvironmentalRulesExclusion:
    """Verify that R-003, R-004, R-008, R-013, R-014 are excluded from active pack."""

    def test_all_audited_in_safe_set(self):
        """All 6 rules were transcribed as IMPLEMENTATION_SAFE candidates in v5 register."""
        for rule_id in AUDITED_CLUSTER_RULE_IDS:
            assert rule_id in MH_IMPLEMENTATION_SAFE_RULE_IDS, f"{rule_id} must be in safe set"

    def test_deferred_rules_excluded_from_active_pack(self):
        active_ids = {r.id for r in load_mh_approval_rules()}
        for rule_id in DEFERRED_CLUSTER_RULE_IDS:
            assert rule_id not in active_ids, f"{rule_id} must NOT be in active pack"
            assert rule_id not in MH_INCLUDED_RULE_IDS, f"{rule_id} must NOT be in included IDs"

    def test_total_mh_rule_count_remains_26(self):
        """Active pack rule count must remain exactly 26."""
        assert len(load_mh_approval_rules()) == 26

    def test_deferred_rules_registered_in_deferred_dict(self):
        for rule_id in DEFERRED_CLUSTER_RULE_IDS:
            assert rule_id in MH_DEFERRED_RULES, f"{rule_id} must be in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rule_id].strip()) > 20

    def test_encode_raises_for_deferred_rules(self):
        for rule_id in DEFERRED_CLUSTER_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rule_id} is deferred:"):
                _encode(rule_id, "APR-TEST", [], [])


class TestDeferredEnvironmentalRationales:
    """Verify specific regulatory/engine rationales for deferrals."""

    def test_r003_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-003"]
        assert (
            "Category determination" in reason
            or "CAT_BASE" in reason
            or "category" in reason.lower()
        )
        assert "R-002" in reason or "composition" in reason
        assert "APR-001" in reason

    def test_r004_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-004"]
        assert "escalation" in reason or "General Condition" in reason
        assert "R-003" in reason or "F-LOC-07" in reason

    def test_r008_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-008"]
        assert "General Condition" in reason or "Item 8(a)" in reason
        assert "R-007" in reason or "contradict" in reason

    def test_r013_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-013"]
        assert "R-014" in reason or "composition" in reason
        assert "MPCB_CATEGORY" in reason or "lookup" in reason

    def test_r014_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-014"]
        assert "lookup" in reason or "classification" in reason or "LOOKUP" in reason
        assert "R-015" in reason or "table" in reason


class TestFactRegistryEnvironmentalCoverage:
    """Verify state of environmental facts in facts.py."""

    def test_fbld01_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-BLD-01")
        assert spec.label == "total_built_up_area_m2"
        assert spec.value_type == FactValueType.NUMBER

    def test_floc02_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-LOC-02")
        assert spec.label == "site_in_notified_industrial_area_or_estate (EIA sense)"
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True

    def test_floc07_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-LOC-07")
        assert "gc_within_5km" in spec.label
        assert spec.value_type == FactValueType.OBJECT
        assert spec.unknown_allowed is True

    def test_fmpcb01_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-MPCB-01")
        assert spec.label == "cpcb_sector_codes"
        assert spec.value_type == FactValueType.LIST

    def test_mpcb_category_fact_absent_from_registry(self):
        """Confirm intermediate fact 'MPCB_CATEGORY' is unmodeled in facts.py."""
        from app.rules.facts import MH_FACTS
        assert "MPCB_CATEGORY" not in MH_FACTS
        assert "F-MPCB-CATEGORY" not in MH_FACTS


class TestSemanticRiskDemonstrations:
    """Demonstrate why naive encoding of non-applicability predicates causes legal hazards."""

    def test_r003_hazard_of_false_negation_for_category_b(self):
        """R-003 condition: CAT_BASE := 'A' IF (F-LOC-02 == FALSE AND SMALL_UNIT == FALSE) ELSE 'B'.

        If R-003 were naively encoded as an ApprovalRule for APR-001
        (Prior Environmental Clearance) using the Category A predicate:
        F-LOC-02 == False AND SMALL_UNIT == False.

        Then for a synthetic organic chemical unit inside an industrial estate
        (F-LOC-02 == True), the rule would evaluate to DOES_NOT_APPLY.
        In reality, Prior EC (APR-001) is strictly MANDATORY for Category B projects;
        the only difference is that appraisal is conducted by SEIAA (AUT-002) rather
        than MoEFCC (AUT-001). Naive encoding would create a catastrophic legal false negative.
        """
        # A unit inside an industrial estate (Category B project):
        in_estate = True
        small_unit = False

        # If encoded as an approval condition:
        naive_ec_applies = (not in_estate) and (not small_unit)
        assert naive_ec_applies is False

        # But statutory truth under EIA 2006 Item 5(f):
        ec_required_under_law = True  # Both Cat A and Cat B require Prior EC
        assert ec_required_under_law != naive_ec_applies

    def test_r008_hazard_of_colliding_with_r007(self):
        """R-008 condition: EC_8A_GC := NOT_APPLICABLE.

        Item 8(a) col 5 states 'General Conditions shall not apply'.
        If encoded as an ApprovalRule for APR-003 with LiteralNode('not_applicable'),
        it would evaluate to NOT_APPLICABLE for a building project with built-up area
        of 30,000 m2, colliding with R-007 (which correctly evaluates to APPLIES).
        """
        # R-008 is a meta-rule about GC inapplicability, not approval applicability.
        assert "R-008" in MH_DEFERRED_RULES

    def test_r013_r014_hazard_of_type_mismatch_and_missing_lookup(self):
        """F-MPCB-01 carries sector codes (e.g. ['111.1']), not color strings.

        R-013 tests MPCB_CATEGORY in {RED, ORANGE, GREEN}.
        Without R-014's lookup engine capability, an approval condition leaf
        cannot evaluate F-MPCB-01 against category strings.
        """
        raw_facts = {"F-MPCB-01": ["111.1"]}
        category_values = ["RED", "ORANGE", "GREEN"]
        # Code '111.1' does not match category name 'RED':
        assert raw_facts["F-MPCB-01"][0] not in category_values


class TestJurisdictionIsolation:
    """Verify that IN-MH environmental audit does not affect IN-GJ."""

    def test_gj_pack_isolation(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        gj_rule_ids = {r.id for r in gj_pack.approval_rules}
        for rule_id in AUDITED_CLUSTER_RULE_IDS:
            assert rule_id not in gj_rule_ids, f"{rule_id} must not be in GJ pack"

    def test_gj_rule_count_unchanged(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19

    def test_global_default_remains_gujarat(self):
        assert DEFAULT_JURISDICTION == IN_GJ == "IN-GJ"
