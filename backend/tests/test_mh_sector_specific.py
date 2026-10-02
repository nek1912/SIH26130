"""Tests for Maharashtra Sector-Specific Approvals / Clearance Pack Cluster.

This suite performs the authoritative audit and verification for:
- R-051: AAI Height Clearance NOC (APR-049 / AUT-020) - DEFERRED
  Reason: Requires 3D GIS spatial coordinates, obstacle limitation surface (OLS)
  geometry, and CCZM permissible elevation grid lookup against aerodrome coordinates
  unsupported by condition primitives; unmodeled aerodrome dataset; status
  REQUIRES_OFFICIAL_CONFIRMATION (SRC-063/SRC-104).
- R-068: Drug / bulk drug / API manufacturing licence (APR-056 / Maharashtra FDA) - DEFERRED
  Reason: Regulated under Drugs & Cosmetics Act 1940 s.18(c) and Drugs Rules 1945
  Part VII; form numbers not re-extracted; UNK-036 open; UR-11 open for MH FDA authority
  routing; applies only if unit manufactures statutorily defined drug under s.3(b) (F-DRG-01);
  status REQUIRES_OFFICIAL_CONFIRMATION (SRC-101/SRC-070).
- R-069: Explosives manufacturing licence (APR-059 / AUT-008 PESO) - DEFERRED
  Reason: Regulated under Explosives Act 1884 and Explosives Rules 2008; requires expert
  substance classification as explosive (peso_gating note); possession thresholds not
  extracted (UNKNOWN for possession-only); separation-distance geometry (Schedule VII)
  unsupported by condition primitives; status REQUIRES_OFFICIAL_CONFIRMATION (SRC-107/SRC-119).
- R-095: Ozone Depleting Substances regulation (CND-022 / MoEFCC Ozone Cell) - DEFERRED
  Reason: Regulated under ODS Rules 2000 r.8; represents a compliance condition /
  registration obligation (RULE_LOGIC) rather than an approval applicability predicate;
  producer (r.3) and seller (r.6) branches unmodeled in fact registry; post-2000
  amendments unverified; status VERIFIED_CONDITIONAL (SRC-127).
- R-105: Planning Zone Industrial Permissibility (PS-02 / Planning Authority) - DEFERRED
  Reason: Regulated under MRTP Act 1966 s.44 and UDCPR Reg. 1.4(iii); represents a planning
  workflow gate (RULE_LOGIC), not an approval applicability predicate; never returns
  APPLIES/DOES_NOT_APPLY (emits CONDITIONAL AUTHORITY_SITE_DEPENDENT when 4 facts supplied,
  else INSUFFICIENT_DATA per ET-v5-21/22); site DP/RP zoning data unmodeled in repository;
  status VERIFIED_CONDITIONAL (SRC-123/SRC-124).

Active MH rules remain 26. Active GJ rules remain 19.
Deferred MH rules increase from 45 to 50.
Default jurisdiction remains IN-GJ.
"""
from __future__ import annotations

import pytest

from app.rules.facts import (
    FactValidationError,
    FactValueType,
    get_fact_spec,
    mh_fact_keys,
    validate_fact_value,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_DO_NOT_IMPLEMENT_RULE_IDS,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

AUDITED_SECTOR_SPECIFIC_RULE_IDS: frozenset[str] = frozenset({
    "R-051",
    "R-068",
    "R-069",
    "R-095",
    "R-105",
})


class TestSectorSpecificInventoryAndIsolation:
    """Verify rule inventory, exact approval mapping, and active/deferred isolation."""

    def test_all_audited_rules_excluded_from_active_pack(self):
        """All 5 rules must be absent from active MH approval rules."""
        rules = load_mh_approval_rules()
        active_ids = {r.id for r in rules}
        for rid in AUDITED_SECTOR_SPECIFIC_RULE_IDS:
            assert rid not in active_ids, f"{rid} must not be in active MH rules"
            assert rid not in MH_INCLUDED_RULE_IDS

    def test_active_rule_count_remains_26(self):
        """Active pack rule count must remain strictly 26."""
        rules = load_mh_approval_rules()
        assert len(rules) == 26
        assert len(MH_INCLUDED_RULE_IDS) == 26

    def test_deferred_rules_registered_with_explicit_reasons(self):
        """All 5 rules must be registered in MH_DEFERRED_RULES with substantial reasons."""
        for rid in AUDITED_SECTOR_SPECIFIC_RULE_IDS:
            assert rid in MH_DEFERRED_RULES, f"{rid} must be registered in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rid].strip()) > 30

    def test_deferred_rules_total_count_is_50(self):
        """Deferred rules count must be at least 50 (50 baseline from sector-specific cluster)."""
        assert len(MH_DEFERRED_RULES) >= 50

    def test_active_and_deferred_sets_are_strictly_disjoint(self):
        """Active and deferred rule ID sets must not intersect."""
        assert set(MH_INCLUDED_RULE_IDS).isdisjoint(set(MH_DEFERRED_RULES))

    def test_encode_raises_fail_closed_for_all_deferred_rules(self):
        """_encode must raise ValueError for all 5 audited deferred rules."""
        for rid in AUDITED_SECTOR_SPECIFIC_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rid} is deferred:"):
                _encode(rid, "APR-TEST", [], [])


class TestExactApprovalAndAuthorityMappings:
    """Verify exact approval/condition IDs and competent authorities from v5 registers."""

    def test_r051_aai_mapping_and_authority(self):
        """R-051 targets APR-049 under AUT-020 (Airports Authority of India)."""
        assert "R-051" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        reason = MH_DEFERRED_RULES["R-051"]
        assert "AAI height clearance NOC" in reason
        assert "GSR 751(E)" in reason
        assert "CCZM" in reason
        assert "SRC-063" in reason
        assert "SRC-104" in reason

    def test_r068_drug_api_mapping_and_authority(self):
        """R-068 targets APR-056 under Maharashtra FDA (State Licensing Authority)."""
        assert "R-068" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        reason = MH_DEFERRED_RULES["R-068"]
        assert "Drugs Rules 1945 Part VII" in reason
        assert "F-DRG-01" in reason
        assert "UNK-036" in reason
        assert "UR-11" in reason
        assert "MH FDA" in reason
        assert "SRC-101" in reason

    def test_r069_explosives_mapping_and_authority(self):
        """R-069 targets APR-059 under AUT-008 (PESO - Circle/Chief Controller)."""
        assert "R-069" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        reason = MH_DEFERRED_RULES["R-069"]
        assert "Explosives Rules 2008" in reason
        assert "peso_gating" in reason
        assert "possession" in reason
        assert "separation-distance" in reason
        assert "SRC-107" in reason
        assert "SRC-119" in reason

    def test_r095_ods_mapping_and_nature(self):
        """R-095 targets CND-022, representing an ODS compliance/registration duty."""
        assert "R-095" in MH_IMPLEMENTATION_SAFE_RULE_IDS
        reason = MH_DEFERRED_RULES["R-095"]
        assert "CND-022" in reason
        assert "ODS Rules 2000 r.8" in reason
        assert "compliance condition / registration obligation" in reason
        assert "SRC-127" in reason

    def test_r105_planning_zone_mapping_and_nature(self):
        """R-105 targets PS-02, representing a planning workflow permissibility gate."""
        assert "R-105" in MH_IMPLEMENTATION_SAFE_RULE_IDS
        reason = MH_DEFERRED_RULES["R-105"]
        assert "PS-02" in reason
        assert "MRTP Act s.44" in reason
        assert "UDCPR" in reason
        assert "never returns APPLIES/DOES_NOT_APPLY" in reason
        assert "ET-v5-21/22" in reason
        assert "SRC-123" in reason
        assert "SRC-124" in reason


class TestFactRegistryCoverageForSectorSpecific:
    """Verify that all sector-specific, spatial, and zoning facts exist with correct types."""

    def test_all_eight_facts_exist_in_mh_registry(self):
        keys = mh_fact_keys()
        expected = [
            "F-OTH-02", "F-DRG-01", "F-PRD-04", "F-ODS-01",
            "F-LOC-05", "F-PLN-02", "F-PLN-03", "F-PLN-04",
        ]
        for k in expected:
            assert k in keys, f"Fact {k} must exist in MH registry"

    def test_f_oth_02_aerodrome_height_zone_spec(self):
        spec = get_fact_spec("IN-MH", "F-OTH-02")
        assert spec.label == "within_aerodrome_height_zone"
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True
        # Valid values
        validate_fact_value("IN-MH", "F-OTH-02", True)
        validate_fact_value("IN-MH", "F-OTH-02", False)
        validate_fact_value("IN-MH", "F-OTH-02", "UNKNOWN")
        validate_fact_value("IN-MH", "F-OTH-02", None)
        # Invalid value
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-OTH-02", "INVALID_BOOL")

    def test_f_drg_01_manufactures_drug_for_sale_spec(self):
        spec = get_fact_spec("IN-MH", "F-DRG-01")
        assert spec.label == "manufactures_drug_for_sale"
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True
        validate_fact_value("IN-MH", "F-DRG-01", True)
        validate_fact_value("IN-MH", "F-DRG-01", False)
        validate_fact_value("IN-MH", "F-DRG-01", "UNKNOWN")
        validate_fact_value("IN-MH", "F-DRG-01", None)
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-DRG-01", 123)

    def test_f_prd_04_special_substance_flags_spec(self):
        spec = get_fact_spec("IN-MH", "F-PRD-04")
        assert spec.label == "special_substance_flags"
        assert spec.value_type == FactValueType.ENUM_SET
        assert "EXPLOSIVE" in spec.allowed_values
        assert "ODS" in spec.allowed_values
        assert "NDPS" in spec.allowed_values
        assert "CWC" in spec.allowed_values
        assert "NONE" in spec.allowed_values
        validate_fact_value("IN-MH", "F-PRD-04", ["EXPLOSIVE"])
        validate_fact_value("IN-MH", "F-PRD-04", ["ODS", "NONE"])
        validate_fact_value("IN-MH", "F-PRD-04", None)
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-PRD-04", ["INVALID_SUBSTANCE"])

    def test_f_ods_01_uses_ods_in_schedule_iv_activity_spec(self):
        spec = get_fact_spec("IN-MH", "F-ODS-01")
        assert spec.label == "uses_ODS_in_Schedule_IV_activity"
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True
        validate_fact_value("IN-MH", "F-ODS-01", True)
        validate_fact_value("IN-MH", "F-ODS-01", False)
        validate_fact_value("IN-MH", "F-ODS-01", "UNKNOWN")
        validate_fact_value("IN-MH", "F-ODS-01", None)
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-ODS-01", "YES")

    def test_f_loc_05_planning_authority_spec(self):
        spec = get_fact_spec("IN-MH", "F-LOC-05")
        assert spec.label == "planning_authority"
        assert spec.value_type == FactValueType.ENUM
        assert "MIDC" in spec.allowed_values
        assert "RP_AREA_COLLECTOR" in spec.allowed_values
        assert "GAOTHAN_PANCHAYAT" in spec.allowed_values
        validate_fact_value("IN-MH", "F-LOC-05", "MIDC")
        validate_fact_value("IN-MH", "F-LOC-05", "MUNICIPAL_CORP:MCGM")
        validate_fact_value("IN-MH", "F-LOC-05", "UNKNOWN")
        validate_fact_value("IN-MH", "F-LOC-05", None)
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-LOC-05", "UNRECOGNIZED_AUTHORITY")

    def test_f_pln_02_03_04_zoning_facts_spec(self):
        for fid in ["F-PLN-02", "F-PLN-03", "F-PLN-04"]:
            spec = get_fact_spec("IN-MH", fid)
            assert spec.value_type == FactValueType.STRING
            assert spec.unknown_allowed is True
            validate_fact_value("IN-MH", fid, "Industrial I-2")
            validate_fact_value("IN-MH", fid, "UNKNOWN")
            validate_fact_value("IN-MH", fid, None)
            with pytest.raises(FactValidationError):
                validate_fact_value("IN-MH", fid, 42)


class TestR051AaiHeightClearanceAudit:
    """Verify AAI height clearance NOC statutory characteristics and deferral rationale."""

    def test_r051_spatial_and_gis_dependency(self):
        """AAI NOC requires 3D CCZM elevation grid and obstacle limitation surface data."""
        reason = MH_DEFERRED_RULES["R-051"]
        assert "3D GIS spatial" in reason
        assert "obstacle limitation surface" in reason
        assert "CCZM" in reason
        assert "unmodeled aerodrome dataset" in reason

    def test_r051_requires_confirmation_status(self):
        """R-051 is classified REQUIRES_CONFIRMATION in v5 register."""
        assert "R-051" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-051" not in MH_DO_NOT_IMPLEMENT_RULE_IDS


class TestR068DrugApiLicenceAudit:
    """Verify Drug / API manufacturing licence statutory characteristics and deferral rationale."""

    def test_r068_legal_basis_and_form_uncertainty(self):
        """R-068 is governed by Drugs Rules Part VII; form numbers and routing are unconfirmed."""
        reason = MH_DEFERRED_RULES["R-068"]
        assert "Drugs Rules 1945 Part VII" in reason
        assert "form numbers not re-extracted" in reason
        assert "UNK-036" in reason
        assert "UR-11" in reason

    def test_r068_domain_boundary_distinction(self):
        """Synthetic organic chemicals do not require a drug licence unless producing
        statutory drug/API.
        """
        reason = MH_DEFERRED_RULES["R-068"]
        assert "s.3(b)" in reason
        assert "F-DRG-01" in reason

    def test_r068_requires_confirmation_status(self):
        assert "R-068" in MH_REQUIRES_CONFIRMATION_RULE_IDS


class TestR069ExplosivesLicenceAudit:
    """Verify PESO Explosives manufacturing licence characteristics and deferral rationale."""

    def test_r069_peso_explosives_regime(self):
        """R-069 is governed by Explosives Rules 2008 under PESO AUT-008."""
        reason = MH_DEFERRED_RULES["R-069"]
        assert "Explosives Rules 2008" in reason
        assert "expert substance classification" in reason
        assert "possession" in reason
        assert "separation-distance" in reason

    def test_r069_distinct_from_petroleum_and_gcr(self):
        """Explosives licence is legally distinct from Petroleum (R-030/32), GCR (R-033),
        and SMPV (R-034).
        """
        assert "R-069" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-030" in MH_INCLUDED_RULE_IDS
        assert "R-032" in MH_DEFERRED_RULES
        assert "R-033" in MH_DEFERRED_RULES
        assert "R-034" in MH_DEFERRED_RULES


class TestR095OzoneDepletingSubstancesAudit:
    """Verify ODS regulation characteristics and compliance vs approval distinction."""

    def test_r095_is_compliance_condition_not_approval(self):
        """CND-022 is a compliance/registration condition (RULE_LOGIC), not an approval."""
        reason = MH_DEFERRED_RULES["R-095"]
        assert "CND-022" in reason
        assert "ODS Rules 2000 r.8" in reason
        assert "compliance condition / registration obligation" in reason

    def test_r095_unmodeled_branches_and_amendments(self):
        """Producer and seller branches are unmodeled; post-2000 amendments unverified."""
        reason = MH_DEFERRED_RULES["R-095"]
        assert "producer (r.3) and seller (r.6) branches unmodeled" in reason
        assert "post-2000 amendments unverified" in reason


class TestR105PlanningZonePermissibilityAudit:
    """Verify Planning Zone Permissibility characteristics and planning gate nature."""

    def test_r105_is_planning_gate_not_approval(self):
        """PS-02 is a planning step (RULE_LOGIC) under MRTP s.44 and UDCPR Reg. 1.4(iii)."""
        reason = MH_DEFERRED_RULES["R-105"]
        assert "PS-02" in reason
        assert "MRTP Act s.44" in reason
        assert "UDCPR" in reason
        assert "planning workflow gate" in reason

    def test_r105_never_returns_applies_or_does_not_apply(self):
        """R-105 never produces binary APPLIES/DOES_NOT_APPLY; emits CONDITIONAL or
        INSUFFICIENT_DATA.
        """
        reason = MH_DEFERRED_RULES["R-105"]
        assert "never returns APPLIES/DOES_NOT_APPLY" in reason
        assert "ET-v5-21/22" in reason

    def test_r105_interaction_with_planning_regime(self):
        """R-105 composes with deferred planning rules R-041, R-078, R-080, R-082
        and active R-035.
        """
        assert "R-035" in MH_INCLUDED_RULE_IDS  # MIDC branch guard active
        assert "R-041" in MH_DEFERRED_RULES     # Building permission deferred
        assert "R-078" in MH_DEFERRED_RULES     # Fire authority routing deferred
        assert "R-080" in MH_DEFERRED_RULES     # BP authority routing deferred
        assert "R-082" in MH_DEFERRED_RULES     # Planning regime selector deferred
        assert "R-105" in MH_DEFERRED_RULES     # Planning zone permissibility deferred


class TestJurisdictionIsolationAndRegression:
    """Verify IN-MH / IN-GJ isolation and existing active rules integrity."""

    def test_default_jurisdiction_remains_in_gj(self):
        assert DEFAULT_JURISDICTION == IN_GJ
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_in_gj_pack_retains_19_active_rules(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19

    def test_in_mh_pack_retains_26_active_rules(self):
        mh_pack = load_regulatory_pack("IN-MH")
        assert len(mh_pack.approval_rules) == 26

    def test_active_mh_rules_unique_ids(self):
        mh_rules = load_mh_approval_rules()
        rule_ids = [r.id for r in mh_rules]
        assert len(rule_ids) == len(set(rule_ids)) == 26


class TestSectorSpecificEdgeConditionsAndUnknowns:
    """Verify positive, negative, and UNKNOWN evaluations for all candidate conditions."""

    def test_r051_location_condition_states(self):
        """F-OTH-02 within_aerodrome_height_zone handles True, False, UNKNOWN, None."""
        assert validate_fact_value("IN-MH", "F-OTH-02", True) is None
        assert validate_fact_value("IN-MH", "F-OTH-02", False) is None
        assert validate_fact_value("IN-MH", "F-OTH-02", "UNKNOWN") is None
        assert validate_fact_value("IN-MH", "F-OTH-02", None) is None

    def test_r068_sector_condition_states(self):
        """F-DRG-01 manufactures_drug_for_sale handles True, False, UNKNOWN, None."""
        assert validate_fact_value("IN-MH", "F-DRG-01", True) is None
        assert validate_fact_value("IN-MH", "F-DRG-01", False) is None
        assert validate_fact_value("IN-MH", "F-DRG-01", "UNKNOWN") is None
        assert validate_fact_value("IN-MH", "F-DRG-01", None) is None

    def test_r069_substance_condition_states(self):
        """F-PRD-04 special_substance_flags handles EXPLOSIVE presence, absence, UNKNOWN."""
        assert validate_fact_value("IN-MH", "F-PRD-04", ["EXPLOSIVE"]) is None
        assert validate_fact_value("IN-MH", "F-PRD-04", ["NONE"]) is None
        assert validate_fact_value("IN-MH", "F-PRD-04", ["UNKNOWN"]) is None
        assert validate_fact_value("IN-MH", "F-PRD-04", None) is None

    def test_r095_activity_condition_states(self):
        """F-ODS-01 uses_ODS_in_Schedule_IV_activity handles True, False, UNKNOWN, None."""
        assert validate_fact_value("IN-MH", "F-ODS-01", True) is None
        assert validate_fact_value("IN-MH", "F-ODS-01", False) is None
        assert validate_fact_value("IN-MH", "F-ODS-01", "UNKNOWN") is None
        assert validate_fact_value("IN-MH", "F-ODS-01", None) is None

    def test_r105_edge_tests_v5_21_and_22(self):
        """Verify ET-v5-21 (any UNKNOWN -> INSUFFICIENT_DATA) and ET-v5-22
        (all known -> CONDITIONAL).
        """
        def evaluate_r105(facts: dict) -> str:
            inputs = [
                facts.get("F-LOC-05"),
                facts.get("F-PLN-02"),
                facts.get("F-PLN-03"),
                facts.get("F-PLN-04"),
            ]
            if any(v is None or v == "UNKNOWN" for v in inputs):
                return "INSUFFICIENT_DATA"
            return "CONDITIONAL"

        # ET-v5-21: planning authority known, zone UNKNOWN -> INSUFFICIENT_DATA
        et_21_facts = {
            "F-LOC-05": "MIDC",
            "F-PLN-02": "UNKNOWN",
            "F-PLN-03": "Synthetic organic chemicals",
            "F-PLN-04": "Vacant plot",
        }
        assert evaluate_r105(et_21_facts) == "INSUFFICIENT_DATA"

        # Missing input -> INSUFFICIENT_DATA
        et_21_missing = {
            "F-LOC-05": "MIDC",
            "F-PLN-03": "Synthetic organic chemicals",
            "F-PLN-04": "Vacant plot",
        }
        assert evaluate_r105(et_21_missing) == "INSUFFICIENT_DATA"

        # ET-v5-22: all four inputs known -> CONDITIONAL (AUTHORITY_SITE_DEPENDENT)
        et_22_facts = {
            "F-LOC-05": "MIDC",
            "F-PLN-02": "Industrial Zone I-2",
            "F-PLN-03": "Synthetic organic chemicals",
            "F-PLN-04": "Vacant plot",
        }
        assert evaluate_r105(et_22_facts) == "CONDITIONAL"

