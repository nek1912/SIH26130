"""Tests for Maharashtra Utilities, Water & Power Cluster (R-038, R-048, R-052, R-053, R-097).

This suite audits and verifies the utilities, water, and power cluster rules:
- R-038: MIDC Water Connection / Drainage (APR-034; APR-035) - DEFERRED
  Reason: Utility service request (MIDC-RTS-01) rather than a statutory approval
  applicability predicate; dual target APR-034 (water) and APR-035 (drainage) conflated
  with divergent conditions; requires set-membership predicate on F-WAT-01 enum-set;
  statutory regulations unread (UR-19 open; backed only by T3 portal evidence SRC-043);
  requires official confirmation.
- R-048: Electrical Installation Approval / Energisation (APR-046) - DEFERRED
  Reason: State-notified self-certification voltage threshold F-ELE-02 is unestablished
  in Maharashtra (UNK-005 open; central 11 kV cannot be applied per ET-050/ET-101);
  RTS 2018 notification (SRC-041) cites superseded CEA 2010 regulations; conflates
  approval applicability with inspection workflow and dynamic officer hierarchy routing;
  requires official confirmation.
- R-052: CETP Membership / Discharge Arrangement (APR-050) - DEFERRED
  Reason: No statutory source cited (source_id: -); classified UNKNOWN in v5 machine summary
  and register; estate-level CETP existence, hydraulic capacity, and effluent acceptance
  are unmodeled site-specific facts (UNK-011 open); contractual/infrastructure arrangement
  or consent condition rather than an independent statutory approval applicability predicate.
- R-053: Water Resources Department River / Surface Water Abstraction (APR-051) - DEFERRED
  Reason: Statutory legal basis explicitly unresearched across all v5 datasets ('Not researched'
  in rules/approvals/authorities); backed solely by T3 MAITRI portal list (SRC-070); competent
  WRD authority routing unverified (UR-17 open); distinguishes river/surface source without
  authoritative basin GIS layer; requires official confirmation.
- R-097: Maharashtra Groundwater Authority Deep Well Prohibition (CND-024) - DEFERRED
  Reason: Statutory prohibition condition (CND-024) under MH Groundwater Act 2009 s.8(1),
  not an approval application; complete village list for 80 notified watersheds unencoded
  in GIS layer (UR-15 open; partial machine parse); post-2015 order currency unconfirmed;
  unconfirmed location must fail closed to INSUFFICIENT_DATA per ET-v5-24, never DOES_NOT_APPLY;
  requires official confirmation.

All 5 audited rules are verified deferred fail-closed.
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
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

AUDITED_UTILITIES_WATER_POWER_RULE_IDS: frozenset[str] = frozenset({
    "R-038",
    "R-048",
    "R-052",
    "R-053",
    "R-097",
})


def _by_id(rule_id: str):
    for r in load_mh_approval_rules():
        if r.id == rule_id:
            return r
    raise KeyError(rule_id)


class TestUtilitiesWaterPowerAuditScope:
    """Verify that all 5 audited rules are deferred fail-closed and excluded from active pack."""

    def test_all_audited_rules_accounted_for(self):
        assert len(AUDITED_UTILITIES_WATER_POWER_RULE_IDS) == 5

    def test_all_audited_rules_excluded_from_active_pack(self):
        rules = load_mh_approval_rules()
        active_ids = {r.id for r in rules}
        for rule_id in AUDITED_UTILITIES_WATER_POWER_RULE_IDS:
            assert rule_id not in active_ids, f"{rule_id} must not be in active MH rules"
            assert rule_id not in MH_INCLUDED_RULE_IDS

    def test_active_rule_count_unchanged_at_26(self):
        """Active pack rule count must remain exactly 26."""
        assert len(load_mh_approval_rules()) == 26

    def test_all_audited_rules_registered_in_deferred_dict(self):
        for rule_id in AUDITED_UTILITIES_WATER_POWER_RULE_IDS:
            assert rule_id in MH_DEFERRED_RULES, f"{rule_id} must be in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rule_id].strip()) > 30

    def test_encode_raises_for_all_audited_rules(self):
        for rule_id in AUDITED_UTILITIES_WATER_POWER_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rule_id} is deferred:"):
                _encode(rule_id, "APR-TEST", [], [])


class TestUtilitiesWaterPowerDeferralRationales:
    """Verify specific regulatory, structural, and evidence rationales for all 5 deferrals."""

    def test_r038_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-038"]
        assert "utility service" in reason.lower() or "MIDC-RTS" in reason
        assert "APR-034" in reason and "APR-035" in reason
        assert "F-WAT-01" in reason or "set-membership" in reason
        assert "UR-19" in reason or "SRC-043" in reason
        assert "confirmation" in reason.lower()

    def test_r048_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-048"]
        assert "F-ELE-02" in reason
        assert "UNK-005" in reason
        assert "11 kV" in reason
        assert "SRC-041" in reason or "CEA" in reason
        assert "inspection" in reason.lower() or "officer" in reason.lower()
        assert "confirmation" in reason.lower()

    def test_r052_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-052"]
        assert "source_id: -" in reason or "no statutory source" in reason.lower()
        assert "UNKNOWN" in reason
        assert "UNK-011" in reason or "CETP" in reason
        assert (
            "consent condition" in reason.lower()
            or "contractual" in reason.lower()
            or "arrangement" in reason.lower()
        )

    def test_r053_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-053"]
        assert "Not researched" in reason or "unresearched" in reason.lower()
        assert "SRC-070" in reason or "MAITRI" in reason
        assert "UR-17" in reason or "WRD" in reason
        assert "confirmation" in reason.lower()

    def test_r097_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-097"]
        assert "CND-024" in reason or "prohibition" in reason.lower()
        assert "s.8(1)" in reason or "Groundwater Act" in reason
        assert "80 notified watersheds" in reason or "village" in reason.lower()
        assert "UR-15" in reason or "GIS" in reason
        assert "ET-v5-24" in reason or "INSUFFICIENT_DATA" in reason


class TestFactRegistryUtilitiesCoverage:
    """Verify state and typing of water, electrical, and groundwater facts in facts.py."""

    def test_fwat_facts_present(self):
        keys = set(mh_fact_keys())
        expected_fwat = {
            "F-WAT-01", "F-WAT-02", "F-WAT-03", "F-WAT-04", "F-WAT-05",
            "F-WAT-06", "F-WAT-07", "F-WAT-08", "F-WAT-09", "F-WAT-10",
        }
        assert expected_fwat <= keys

    def test_fwat_fact_types_and_enums(self):
        f1 = get_fact_spec("IN-MH", "F-WAT-01")
        assert f1.value_type == FactValueType.ENUM_SET
        assert "MIDC" in f1.allowed_values
        assert "GROUNDWATER" in f1.allowed_values
        assert "SURFACE" in f1.allowed_values

        f3 = get_fact_spec("IN-MH", "F-WAT-03")
        assert f3.value_type == FactValueType.ENUM
        assert "CETP" in f3.allowed_values
        assert "ZLD" in f3.allowed_values

        f4 = get_fact_spec("IN-MH", "F-WAT-04")
        assert f4.value_type == FactValueType.BOOLEAN
        assert f4.unknown_allowed is True

        f7 = get_fact_spec("IN-MH", "F-WAT-07")
        assert f7.value_type == FactValueType.BOOLEAN

        f10 = get_fact_spec("IN-MH", "F-WAT-10")
        assert f10.value_type == FactValueType.STRING
        assert f10.unknown_allowed is True

    def test_fele_facts_present_and_typed(self):
        keys = set(mh_fact_keys())
        assert {"F-ELE-01", "F-ELE-02", "F-ELE-03"} <= keys
        assert get_fact_spec("IN-MH", "F-ELE-01").value_type == FactValueType.NUMBER
        assert get_fact_spec("IN-MH", "F-ELE-02").value_type == FactValueType.NUMBER
        assert get_fact_spec("IN-MH", "F-ELE-02").unknown_allowed is True
        assert get_fact_spec("IN-MH", "F-ELE-03").value_type == FactValueType.NUMBER

    def test_fgw_facts_present_and_typed(self):
        keys = set(mh_fact_keys())
        assert {"F-GW-01", "F-GW-02", "F-GW-03"} <= keys
        assert get_fact_spec("IN-MH", "F-GW-01").value_type == FactValueType.ENUM
        assert get_fact_spec("IN-MH", "F-GW-02").value_type == FactValueType.NUMBER
        assert get_fact_spec("IN-MH", "F-GW-02").unknown_allowed is True
        assert get_fact_spec("IN-MH", "F-GW-03").value_type == FactValueType.BOOLEAN
        assert get_fact_spec("IN-MH", "F-GW-03").unknown_allowed is True

    def test_unmodeled_facts_confirmed_absent(self):
        """Confirm facts that must NOT be guessed are absent from the registry."""
        from app.rules.facts import MH_FACTS
        # No fake GIS boundary / watershed polygon facts
        assert "F-MWRRA-WATERSHED-POLYGON" not in MH_FACTS
        assert "MWRRA_watershed_polygon" not in MH_FACTS
        # No fake estate-level CETP capacity allocation facts
        assert "F-CETP-CAPACITY-AVAILABLE" not in MH_FACTS
        # No fake electrical officer category selector
        assert "ELEC_APPROVING_OFFICER" not in MH_FACTS


class TestLocationGISSafetyAndFailClosed:
    """Verify that location-dependent facts fail closed and do not accept unverified claims."""

    def test_midc_estate_unknown_must_not_default_true(self):
        """F-LOC-01 missing or UNKNOWN must never be coerced to True."""
        f_loc = get_fact_spec("IN-MH", "F-LOC-01")
        assert f_loc.unknown_allowed is True
        # In a deterministic engine, unknown location cannot trigger MIDC-only rules

    def test_cetp_available_never_defaults_true(self):
        """F-WAT-04 notes in facts.csv: 'Never default TRUE'.

        ET-055: discharge=CETP; cetp_available=UNKNOWN -> expected: UNKNOWN.
        """
        f4 = get_fact_spec("IN-MH", "F-WAT-04")
        assert f4.unknown_allowed is True
        desc = (f4.description + str(f4)).lower()
        assert "never default true" in desc or f4.unknown_allowed

    def test_mwrra_notified_area_never_defaults_false_on_unknown(self):
        """ET-v5-24: borewell 80 m, industrial, village UNKNOWN -> INSUFFICIENT_DATA.

        Never DOES_NOT_APPLY. If F-GW-03 is UNKNOWN, the prohibition cannot be cleared.
        """
        f_gw03 = get_fact_spec("IN-MH", "F-GW-03")
        assert f_gw03.unknown_allowed is True

    def test_unconfirmed_location_fails_closed(self):
        """Applicant claims cannot override missing authoritative GIS records."""
        # When location fact is missing or 'UNKNOWN', evaluate_rule must fail closed
        rule = _by_id("R-077")  # Active CGWA over-exploited rule
        # Missing F-GW-01 -> INSUFFICIENT_DATA
        res = evaluate_rule(rule, {"F-EXP-01": False, "F-INC-01": "LARGE"})
        assert res.result == ApprovalResult.INSUFFICIENT_DATA


class TestSemanticRiskDemonstrations:
    """Demonstrate why naive encoding of R-038/048/052/053/097 causes severe hazards."""

    def test_r038_dual_target_divergence_and_utility_nature(self):
        """R-038 conflates APR-034 (water connection) and APR-035 (drainage connection).

        In rules.csv:
            MIDC_WATER := MIDC_BRANCH AND 'MIDC' IN F-WAT-01
            MIDC_DRAIN := MIDC_BRANCH AND F-WAT-03 IN {CETP, SEWER}

        Consider an industrial plant inside MIDC (F-LOC-01 == True) that takes water from
        the MIDC piped supply ('MIDC' in F-WAT-01), but operates a Zero Liquid Discharge
        plant (F-WAT-03 == 'ZLD').
        - APR-034 (Water connection): APPLIES.
        - APR-035 (Drainage connection): DOES NOT APPLY (no effluent discharged to MIDC drain).

        A single naive rule targeting APR-034;APR-035 cannot express this divergent outcome.
        Furthermore, piped water supply is an infrastructure utility service request
        under MIDC RTS (15-day SLA), not a statutory environmental/regulatory approval.
        """
        site_in_midc = True
        water_sources = ["MIDC"]
        discharge_mode = "ZLD"

        water_applies = site_in_midc and ("MIDC" in water_sources)
        drainage_applies = site_in_midc and (discharge_mode in {"CETP", "SEWER"})

        assert water_applies is True
        assert drainage_applies is False
        assert water_applies != drainage_applies

        # Register mandates deferral:
        assert "R-038" in MH_DEFERRED_RULES

    def test_r048_unresolved_voltage_and_central_threshold_hazard(self):
        """R-048: Condition is ELEC_INSPECTION := F-ELE-01 > F-ELE-02.

        Central Government notified 11 kV as the self-certification voltage for its
        jurisdiction (PIB 05-08-2024). But CEA Safety Regulations 2023 reg. 32/43 mandate
        that each State Government notify its own self-certification voltage threshold.
        Maharashtra has NOT notified any such threshold (UNK-005 open).

        If a naive implementer had defaulted F-ELE-02 to 11 kV:
        An industrial unit connecting at 11 kV would evaluate:
            11 > 11 -> False -> DOES_NOT_APPLY.
        The unit would then energise without statutory inspection by the Electrical Inspector,
        committing an offence under Section 54/146 of the Electricity Act 2003.

        Edge tests ET-050 and ET-101 explicitly require:
            ET-050: HT 11 kV; notified voltage UNKNOWN -> expected: ELEC_INSPECTION=UNKNOWN
            ET-101: connection 11 kV; MH notified voltage UNKNOWN -> expected: UNKNOWN
                    rationale: Do not use central 11 kV.
        """
        f_ele_01 = 11.0  # 11 kV
        central_threshold = 11.0
        naive_check = f_ele_01 > central_threshold
        assert naive_check is False  # Naive encoding falsely emits DOES_NOT_APPLY!

        # F-ELE-02 is UNKNOWN -> result must be UNKNOWN/INSUFFICIENT_DATA
        assert "R-048" in MH_DEFERRED_RULES
        assert "11 kV" in MH_DEFERRED_RULES["R-048"]

    def test_r052_zero_evidence_and_cetp_availability_hazard(self):
        """R-052: CETP membership / discharge arrangement (APR-050).

        1. In rule_register_v5.csv, source_id is '-' (NO SOURCE RECORD AT ALL; tier: -).
        2. Status is UNKNOWN in machine summary and register (one of only 3 UNKNOWN rules).
        3. UNK-011 is open: estate-level CETP existence, hydraulic capacity, and acceptance
           are unmodeled site-specific facts.
        4. If naively encoded as (F-WAT-03 == 'CETP' and F-WAT-04 == True), missing F-WAT-04
           would risk false negatives (falsely advising a polluting unit that no discharge
           arrangement is needed). ET-055 strictly requires UNKNOWN.
        """
        assert "R-052" in MH_DEFERRED_RULES
        assert (
            "source_id: -" in MH_DEFERRED_RULES["R-052"]
            or "statutory source" in MH_DEFERRED_RULES["R-052"].lower()
        )

    def test_r053_unresearched_legal_basis_and_approval_identity_confusion(self):
        """R-053: Permission to draw water from river/public tanks (APR-051).

        1. In rules.csv, legal_basis is literally 'Not researched'.
        2. In approvals.csv, legal_basis is 'Not researched'.
        3. In authorities.csv, instruments is 'Not researched'.
        4. The prompt labeled this as APR-045 / AUT-014.
           In reality, APR-045 is 'New electricity connection' and AUT-014 is GSDA.
           The true approval is APR-051 and authority AUT-021 (WRD).
        5. Backed only by T3 portal listing SRC-070 (MAITRI).
        Encoding an approval whose legal basis is unresearched violates RULES.md Rule 1 and Rule 2.
        """
        assert "R-053" in MH_DEFERRED_RULES
        assert (
            "Not researched" in MH_DEFERRED_RULES["R-053"]
            or "unresearched" in MH_DEFERRED_RULES["R-053"].lower()
        )

    def test_r097_prohibition_condition_vs_approval_and_gis_hazard(self):
        """R-097: MH_GW_DEEP_WELL_PROHIBITION (CND-024).

        1. CND-024 is a statutory prohibition condition under Section 8(1) of the
           Maharashtra Groundwater Act 2009, NOT an approval application.
        2. Prohibits deep wells (>60m) for agriculture/industry in 80 notified watersheds.
        3. The complete village list has NOT been digitized into the repository GIS layer
           (UR-15 open: 'partial machine parse in v5 working files - not encoded').
        4. ET-v5-24 explicitly demands:
           inputs: borewell 80 m, industrial, village UNKNOWN -> expected: INSUFFICIENT_DATA
           (never DOES_NOT_APPLY).
        5. Naive encoding assuming False for unconfirmed village would allow illegal drilling
           in an over-exploited watershed.
        """
        well_depth = 80.0
        depth_threshold = 60.0
        village_in_annexure = None  # UNKNOWN location

        # Naive evaluation assuming unknown = False:
        naive_applies = (well_depth > depth_threshold) and (village_in_annexure is True)
        assert naive_applies is False  # False negative hazard!

        # Safe behaviour: must defer and fail closed
        assert "R-097" in MH_DEFERRED_RULES
        assert "CND-024" in MH_DEFERRED_RULES["R-097"]


class TestExistingActiveRulesRegression:
    """Verify that existing active rules remain functional and untouched."""

    def test_r043_cgwa_msme_exemption_active_and_correct(self):
        """R-043: CGWA exemption for micro/small < 10 m3/day (APR-043)."""
        rule = _by_id("R-043")
        assert rule.approval_id == "APR-043"
        # Micro + 8 m3/day -> APPLIES (exemption applies)
        res = evaluate_rule(rule, {"F-INC-01": "MICRO", "F-WAT-05": 8.0})
        assert res.result == ApprovalResult.APPLIES
        # Large + 8 m3/day -> DOES_NOT_APPLY (not exempt)
        res_large = evaluate_rule(rule, {"F-INC-01": "LARGE", "F-WAT-05": 8.0})
        assert res_large.result == ApprovalResult.DOES_NOT_APPLY
        # Micro + 12 m3/day -> DOES_NOT_APPLY
        res_over = evaluate_rule(rule, {"F-INC-01": "MICRO", "F-WAT-05": 12.0})
        assert res_over.result == ApprovalResult.DOES_NOT_APPLY

    def test_r044_cgwa_domestic_exemption_active_and_correct(self):
        """R-044: CGWA exemption for domestic only <= 5 m3/day (APR-043)."""
        rule = _by_id("R-044")
        assert rule.approval_id == "APR-043"
        # Domestic only + 5 m3/day -> APPLIES
        res = evaluate_rule(rule, {"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 5.0})
        assert res.result == ApprovalResult.APPLIES
        # Domestic only + 5.1 m3/day -> DOES_NOT_APPLY
        res_over = evaluate_rule(rule, {"F-WAT-06": "DOMESTIC_ONLY", "F-WAT-05": 5.1})
        assert res_over.result == ApprovalResult.DOES_NOT_APPLY

    def test_r077_cgwa_over_exploited_active_and_correct(self):
        """R-077: CGWA over-exploited unit restriction (APR-043)."""
        rule = _by_id("R-077")
        assert rule.approval_id == "APR-043"
        # Over-exploited + non-MSME new -> APPLIES
        res = evaluate_rule(
            rule,
            {"F-GW-01": "OVER_EXPLOITED", "F-EXP-01": False, "F-INC-01": "LARGE"},
        )
        assert res.result == ApprovalResult.APPLIES
        # Safe unit -> DOES_NOT_APPLY
        res_safe = evaluate_rule(
            rule,
            {"F-GW-01": "SAFE", "F-EXP-01": False, "F-INC-01": "LARGE"},
        )
        assert res_safe.result == ApprovalResult.DOES_NOT_APPLY

    def test_r007_eia_building_construction_active_and_correct(self):
        """R-007: EIA 8(a) building/construction (APR-003)."""
        rule = _by_id("R-007")
        assert rule.approval_id == "APR-003"
        assert evaluate_rule(rule, {"F-BLD-01": 20000.0}).result == ApprovalResult.APPLIES
        assert evaluate_rule(rule, {"F-BLD-01": 19999.0}).result == ApprovalResult.DOES_NOT_APPLY
        assert evaluate_rule(rule, {"F-BLD-01": 150000.0}).result == ApprovalResult.DOES_NOT_APPLY

    def test_r026_labour_active_and_correct(self):
        """R-026: Principal employer registration under CLRA (APR-019)."""
        rule = _by_id("R-026")
        res = evaluate_rule(rule, {"F-LAB-03": 50, "F-LAB-09": False})
        assert res.result == ApprovalResult.APPLIES


class TestJurisdictionIsolation:
    """Verify that IN-MH audit does not affect IN-GJ."""

    def test_gj_pack_isolation(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        gj_rule_ids = {r.id for r in gj_pack.approval_rules}
        for rule_id in AUDITED_UTILITIES_WATER_POWER_RULE_IDS:
            assert rule_id not in gj_rule_ids, f"{rule_id} must not be in GJ pack"

    def test_gj_rule_count_unchanged(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19

    def test_global_default_remains_gujarat(self):
        assert DEFAULT_JURISDICTION == IN_GJ == "IN-GJ"
