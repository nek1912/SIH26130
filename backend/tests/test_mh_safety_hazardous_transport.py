"""Tests for Maharashtra Safety, Hazardous Chemicals & Transport Cluster.

This suite performs the authoritative audit and verification for:
- R-030: Petroleum storage licence / Class B exemption (APR-026 / AUT-008, AUT-009)
  Status: ACTIVE in pack (batch 1); audit confirms PET_EXEMPT_B is a statutory
  exemption predicate under Petroleum Act 1934 s.7(1)(a) rather than a general
  approval requirement; active status preserved with limited-scope boundaries pinned.
- R-032: Petroleum licence form and authority routing (APR-026) - DEFERRED
  Reason: Computes PET_FORM string ('XII (DA)' | 'XIII (DA)' | 'XVI (PESO)' | 'XV (PESO)')
  rather than a boolean approval applicability predicate; multiple classes combination
  rules unmodeled; cannot be expressed by ConditionNode boolean primitives.
  (Candidate prompt misidentified R-032 as Gas cylinder storage licence).
- R-033: Gas cylinder storage licence exemption under GCR 2016 r.44 (APR-027) - DEFERRED
  Reason: GCR_EXEMPT requires list iteration and per-group quantifiers over F-GAS-01;
  LPG clause under r.44(c) is legally ambiguous (UNK-016, PT-05); gas classification
  unmodeled (UNK-039); unread GCR amendments remain (UR-10).
  (Candidate prompt misidentified R-033 as SMPV licence).
- R-034: SMPV(U) Rules 2016 r.2 pressure vessel definition & r.45 licence (APR-028) - DEFERRED
  Reason: Requires existential quantifier (EXISTS) over F-PV-01 list and process
  vessel exclusion filtering (r.3 16-hr feed rule); official status is
  REQUIRES_OFFICIAL_CONFIRMATION due to unread amendments (UR-10).
- R-035: MIDC plot allotment branch guard (APR-029)
  Status: ACTIVE in pack (batch 1); audit confirms R-035 is MIDC branch guard
  (MIDC_BRANCH := F-LOC-01 == True). Candidate prompt misidentified R-035 as
  Factory safety / hazardous process; true Factory safety rules (R-022, R-023)
  were audited and safely deferred in the Labour cluster, while R-070 is active.
- R-062: CTO validity rule under GSR 62/63 (APR-008) - DEFERRED
  Reason: Lifecycle validity clause (CTO_VALIDITY := 'VALID_TILL_CANCELLED'), not an
  approval applicability predicate; CTO grant date fact absent from registry;
  Maharashtra implementation unconfirmed (UNK-032). Candidate prompt misidentified
  R-062 as Biomedical Waste; BMWM Rules 2016 are inapplicable to synthetic organic
  chemical manufacturing (zero BMW rules/approvals in domain).
- R-092: Petroleum DA NOC under r.144 (APR-026) - DEFERRED
  Reason: Requires rule composition with R-032 (form and authority routing) which is
  deferred; cannot be evaluated standalone without licensing authority determination.

Active MH rules remain 26. Active GJ rules remain 19.
Default jurisdiction remains IN-GJ.
"""
from __future__ import annotations

import pytest

from app.rules.applicability import evaluate_rule
from app.rules.facts import (
    FactValueType,
    get_fact_spec,
    mh_fact_keys,
)
from app.rules.models import ApprovalResult
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    _encode,
    load_mh_approval_authorities,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

AUDITED_SAFETY_DEFERRED_RULE_IDS: frozenset[str] = frozenset({
    "R-032",
    "R-033",
    "R-034",
    "R-062",
    "R-092",
})

AUDITED_SAFETY_ACTIVE_RULE_IDS: frozenset[str] = frozenset({
    "R-030",
    "R-035",
})


def _by_id(rule_id: str):
    for r in load_mh_approval_rules():
        if r.id == rule_id:
            return r
    raise KeyError(rule_id)


class TestSafetyClusterInventoryAndIsolation:
    """Verify rule inventory, exact approval mapping, and active/deferred isolation."""

    def test_active_safety_rules_in_pack(self):
        rules = load_mh_approval_rules()
        active_ids = {r.id for r in rules}
        for rid in AUDITED_SAFETY_ACTIVE_RULE_IDS:
            assert rid in active_ids, f"{rid} must be in active MH rules"
            assert rid in MH_INCLUDED_RULE_IDS

    def test_deferred_safety_rules_excluded_from_active_pack(self):
        rules = load_mh_approval_rules()
        active_ids = {r.id for r in rules}
        for rid in AUDITED_SAFETY_DEFERRED_RULE_IDS:
            assert rid not in active_ids, f"{rid} must not be in active MH rules"
            assert rid not in MH_INCLUDED_RULE_IDS

    def test_active_rule_count_remains_26(self):
        """Active pack rule count must remain exactly 26."""
        assert len(load_mh_approval_rules()) == 26

    def test_deferred_safety_rules_registered(self):
        for rid in AUDITED_SAFETY_DEFERRED_RULE_IDS:
            assert rid in MH_DEFERRED_RULES, f"{rid} must be registered in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rid].strip()) > 30

    def test_encode_raises_for_deferred_safety_rules(self):
        for rid in AUDITED_SAFETY_DEFERRED_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rid} is deferred:"):
                _encode(rid, "APR-TEST", [], [])


class TestExactApprovalAndAuthorityMappings:
    """Verify exact approval IDs and authorities, dispelling prompt label mismatches."""

    def test_r030_exact_mapping(self):
        """R-030 targets APR-026 (not prompt's APR-024). Authority is AUT-008 / AUT-009."""
        rule = _by_id("R-030")
        assert rule.approval_id == "APR-026"
        authorities = load_mh_approval_authorities()
        assert authorities["APR-026"] == "AUT-008 / AUT-009"

    def test_r035_exact_mapping(self):
        """R-035 targets APR-029 (MIDC plot allotment, AUT-010), not factory safety."""
        rule = _by_id("R-035")
        assert rule.approval_id == "APR-029"
        authorities = load_mh_approval_authorities()
        assert authorities["APR-029"] == "AUT-010"

    def test_r032_and_r033_identity_disambiguation(self):
        """Disambiguate prompt labels: R-032 is Petroleum Form routing, R-033 is GCR Form F."""
        assert "R-032" in MH_DEFERRED_RULES
        assert "Petroleum licence form" in MH_DEFERRED_RULES["R-032"]
        assert "R-033" in MH_DEFERRED_RULES
        assert "Gas cylinder storage licence" in MH_DEFERRED_RULES["R-033"]

    def test_r034_and_smpv_identity_disambiguation(self):
        """SMPV licence is R-034 (APR-028), not R-033 (which is GCR APR-027)."""
        assert "R-034" in MH_DEFERRED_RULES
        assert "SMPV(U)" in MH_DEFERRED_RULES["R-034"]
        assert "R-034" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_r062_and_biomedical_waste_disambiguation(self):
        """R-062 is CTO validity under GSR 62/63 (APR-008), not Biomedical Waste (APR-011)."""
        assert "R-062" in MH_DEFERRED_RULES
        assert "CTO validity" in MH_DEFERRED_RULES["R-062"]
        assert "Biomedical Waste is inapplicable" in MH_DEFERRED_RULES["R-062"]


class TestFactRegistryCoverageForSafety:
    """Verify that all safety, gas, petroleum, and pressure vessel facts exist with correct types.
    """

    def test_petroleum_facts_exist(self):
        assert "F-PET-01" in mh_fact_keys()
        assert "F-PET-02" in mh_fact_keys()
        assert "F-PET-03" in mh_fact_keys()
        assert "F-PET-04" in mh_fact_keys()

        spec_01 = get_fact_spec("IN-MH", "F-PET-01")
        assert spec_01.value_type == FactValueType.ENUM
        assert set(spec_01.allowed_values) == {"A", "B", "C", "NOT_PETROLEUM", "UNKNOWN"}

        spec_02 = get_fact_spec("IN-MH", "F-PET-02")
        assert spec_02.value_type == FactValueType.NUMBER
        assert spec_02.unit == "L"

        spec_03 = get_fact_spec("IN-MH", "F-PET-03")
        assert spec_03.value_type == FactValueType.ENUM
        assert set(spec_03.allowed_values) == {"BULK", "NON_BULK"}

        spec_04 = get_fact_spec("IN-MH", "F-PET-04")
        assert spec_04.value_type == FactValueType.NUMBER
        assert spec_04.unit == "L"

    def test_gas_facts_exist(self):
        assert "F-GAS-01" in mh_fact_keys()
        assert "F-GAS-02" in mh_fact_keys()
        assert "F-GAS-03" in mh_fact_keys()

        spec_01 = get_fact_spec("IN-MH", "F-GAS-01")
        assert spec_01.value_type == FactValueType.LIST

        spec_02 = get_fact_spec("IN-MH", "F-GAS-02")
        assert spec_02.value_type == FactValueType.NUMBER
        assert spec_02.unit == "kg"

        spec_03 = get_fact_spec("IN-MH", "F-GAS-03")
        assert spec_03.value_type == FactValueType.ENUM
        assert "FLAMMABLE_NONTOXIC" in spec_03.allowed_values
        assert "TOXIC" in spec_03.allowed_values
        assert "LPG" in spec_03.allowed_values

    def test_pressure_vessel_facts_exist(self):
        assert "F-PV-01" in mh_fact_keys()
        assert "F-PV-02" in mh_fact_keys()

        spec_01 = get_fact_spec("IN-MH", "F-PV-01")
        assert spec_01.value_type == FactValueType.LIST

        spec_02 = get_fact_spec("IN-MH", "F-PV-02")
        assert spec_02.value_type == FactValueType.BOOLEAN

    def test_transport_and_hazardous_waste_facts_exist(self):
        assert "F-TRN-01" in mh_fact_keys()
        assert "F-HW-01" in mh_fact_keys()
        assert "F-HW-04" in mh_fact_keys()

        spec_trn = get_fact_spec("IN-MH", "F-TRN-01")
        assert spec_trn.value_type == FactValueType.BOOLEAN

    def test_biomedical_waste_facts_absent_from_registry(self):
        """Synthetic organic chemical manufacturing pack carries no biomedical waste facts."""
        keys = mh_fact_keys()
        assert not any("BMW" in k or "BIOMEDICAL" in k for k in keys)


class TestR030PetroleumBoundariesAndFailClosed:
    """Verify R-030 condition boundaries, edge cases, and fail-closed behavior."""

    def test_class_b_below_and_at_thresholds(self):
        """Class B total <= 2500 L and receptacle <= 1000 L -> applies."""
        rule = _by_id("R-030")
        # Exactly at thresholds: 2500 L, 1000 L receptacle
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2500, "F-PET-04": 1000}
        ).result == ApprovalResult.APPLIES
        # Strictly below thresholds: 2000 L, 500 L receptacle
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 500}
        ).result == ApprovalResult.APPLIES

    def test_class_b_above_thresholds(self):
        """Class B total > 2500 L or receptacle > 1000 L -> does_not_apply."""
        rule = _by_id("R-030")
        # Quantity exceeds 2500 L (ET-027)
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2501, "F-PET-04": 1000}
        ).result == ApprovalResult.DOES_NOT_APPLY
        # Receptacle exceeds 1000 L (ET-028)
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": 1001}
        ).result == ApprovalResult.DOES_NOT_APPLY

    def test_non_class_b_evaluates_does_not_apply(self):
        rule = _by_id("R-030")
        assert evaluate_rule(
            rule, {"F-PET-01": "A", "F-PET-02": 10, "F-PET-04": 10}
        ).result == ApprovalResult.DOES_NOT_APPLY
        assert evaluate_rule(
            rule, {"F-PET-01": "C", "F-PET-02": 10000, "F-PET-04": 500}
        ).result == ApprovalResult.DOES_NOT_APPLY
        assert evaluate_rule(
            rule, {"F-PET-01": "NOT_PETROLEUM", "F-PET-02": 0, "F-PET-04": 0}
        ).result == ApprovalResult.DOES_NOT_APPLY

    def test_missing_and_unknown_fail_closed(self):
        """Missing or UNKNOWN facts must fail closed to INSUFFICIENT_DATA."""
        rule = _by_id("R-030")
        assert evaluate_rule(rule, {}).result == ApprovalResult.INSUFFICIENT_DATA
        assert evaluate_rule(rule, {"F-PET-01": "B"}).result == ApprovalResult.INSUFFICIENT_DATA
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2000}
        ).result == ApprovalResult.INSUFFICIENT_DATA
        assert evaluate_rule(
            rule, {"F-PET-01": "B", "F-PET-02": 2000, "F-PET-04": "UNKNOWN"}
        ).result == ApprovalResult.INSUFFICIENT_DATA


class TestR035MIDCBranchGuard:
    """Verify R-035 location branch guard behavior."""

    def test_r035_true_applies(self):
        rule = _by_id("R-035")
        assert evaluate_rule(rule, {"F-LOC-01": True}).result == ApprovalResult.APPLIES

    def test_r035_false_does_not_apply(self):
        rule = _by_id("R-035")
        assert evaluate_rule(rule, {"F-LOC-01": False}).result == ApprovalResult.DOES_NOT_APPLY

    def test_r035_missing_fails_closed(self):
        rule = _by_id("R-035")
        assert evaluate_rule(rule, {}).result == ApprovalResult.INSUFFICIENT_DATA
        assert evaluate_rule(rule, {"F-LOC-01": None}).result == ApprovalResult.INSUFFICIENT_DATA
        res = evaluate_rule(rule, {"F-LOC-01": "UNKNOWN"})
        assert res.result == ApprovalResult.INSUFFICIENT_DATA


class TestDeferralRationalesAndEngineLimitations:
    """Verify the detailed deferral rationales for all unencoded candidate rules."""

    def test_r032_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-032"]
        assert "PET_FORM" in reason
        assert "ConditionNode" in reason or "routing" in reason

    def test_r033_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-033"]
        assert "GCR_EXEMPT" in reason or "F-GAS-01" in reason
        assert "UNK-016" in reason or "UR-10" in reason

    def test_r034_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-034"]
        assert "SMPV" in reason
        assert "EXISTS" in reason or "F-PV-01" in reason
        assert "UR-10" in reason or "REQUIRES_OFFICIAL_CONFIRMATION" in reason

    def test_r062_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-062"]
        assert "CTO_VALIDITY" in reason
        assert "UNK-032" in reason or "Biomedical Waste" in reason

    def test_r092_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-092"]
        assert "r.144" in reason or "R-032" in reason


class TestFactorySafetyAndLabourClusterIntegrity:
    """Verify Factory Safety rules audited in Labour cluster remain safely deferred."""

    def test_r022_factory_plan_and_licence_deferred(self):
        assert "R-022" in MH_DEFERRED_RULES
        assert "APR-015" in MH_DEFERRED_RULES["R-022"]
        assert "APR-016" in MH_DEFERRED_RULES["R-022"]

    def test_r023_dish_licence_category_deferred(self):
        assert "R-023" in MH_DEFERRED_RULES
        assert "DISH_LICENCE_CATEGORY" in MH_DEFERRED_RULES["R-023"]

    def test_r070_safety_officer_active_in_pack(self):
        rule = _by_id("R-070")
        assert rule.approval_id == "CMP-018"
        # 250 workers with hazardous process -> applies
        assert evaluate_rule(
            rule, {"F-LAB-01": 250, "F-LAB-07": True}
        ).result == ApprovalResult.APPLIES
        # 249 workers with hazardous process -> does_not_apply
        assert evaluate_rule(
            rule, {"F-LAB-01": 249, "F-LAB-07": True}
        ).result == ApprovalResult.DOES_NOT_APPLY


class TestMultipleRegimeOverlapSafety:
    """Verify that multiple safety/chemical regimes operate without illegal conflation."""

    def test_transport_cmvr_independent_of_petroleum(self):
        """R-093 (CMVR consignor duties, CMP-024) is independent of petroleum storage."""
        rule = _by_id("R-093")
        assert rule.approval_id == "CMP-024"
        assert evaluate_rule(rule, {"F-TRN-01": True}).result == ApprovalResult.APPLIES
        assert evaluate_rule(rule, {"F-TRN-01": False}).result == ApprovalResult.DOES_NOT_APPLY

    def test_hazardous_waste_independent_of_biomedical(self):
        """Hazardous waste authorisation (R-018, R-096) operates under APR-010 without BMW."""
        r018 = _by_id("R-018")
        assert r018.approval_id == "APR-010"
        assert evaluate_rule(r018, {"F-HW-01": True}).result == ApprovalResult.APPLIES

        r096 = _by_id("R-096")
        assert r096.approval_id == "APR-010"
        assert evaluate_rule(r096, {"F-HW-04": "CLASS_A"}).result == ApprovalResult.APPLIES

    def test_boiler_independent_of_pressure_vessels(self):
        """Boilers Act 2025 (R-028, R-073, R-086, R-087) governs fired steam boilers, not SMPV."""
        r028 = _by_id("R-028")
        assert r028.approval_id == "APR-023"
        boiler_facts = {
            "F-BLR-04": True, "F-BLR-01": 30, "F-BLR-05": 5,
            "F-BLR-02": 2, "F-BLR-03": 150,
        }
        assert evaluate_rule(r028, boiler_facts).result == ApprovalResult.APPLIES


class TestJurisdictionIsolation:
    """Verify complete isolation between IN-MH and IN-GJ."""

    def test_default_jurisdiction_is_in_gj(self):
        assert DEFAULT_JURISDICTION == IN_GJ

    def test_gj_pack_unmodified(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        gj_rule_ids = {r.id for r in gj_pack.approval_rules}
        assert not gj_rule_ids.intersection(MH_INCLUDED_RULE_IDS)

    def test_mh_pack_has_exactly_26_active_rules(self):
        mh_pack = load_regulatory_pack("IN-MH")
        assert len(mh_pack.approval_rules) == 26
        active_ids = {r.id for r in mh_pack.approval_rules}
        assert active_ids == set(MH_INCLUDED_RULE_IDS)
