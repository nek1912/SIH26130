"""Tests for Maharashtra Planning & Fire Cluster (R-041, R-078, R-079, R-080, R-082).

This suite audits and verifies the planning and fire cluster rules:
- R-041: Building/development permission (non-MIDC) - DEFERRED
  Reason: fact 'construction' absent from registry; dynamic authority routing R-080
  and regulation regime selection R-082 require cross-rule composition; dual target
  APR-038 (pre-construction) / APR-041 (post-construction occupancy).
- R-078: Provisional fire NOC authority routing (non-MIDC) - DEFERRED
  Reason: authority routing expression computing FIRE_AUTHORITY string, not a boolean
  approval applicability predicate (mirrors R-047 precedent).
- R-079: Schedule-I fire approval building class predicate - DEFERRED
  Reason: Schedule-I predicate requires composition with non-MIDC guard (F-LOC-01 == False)
  and fire authority R-078 under R-042; standalone encoding under APR-039 would over-apply
  to MIDC estates (mirrors R-031/R-103 precedent). R-042 is held in REQUIRES_OFFICIAL_CONFIRMATION.
- R-080: Planning authority routing (non-MIDC) - DEFERRED
  Reason: authority routing expression computing BP_AUTHORITY string, not a boolean
  approval applicability predicate (mirrors R-047 precedent).
- R-082: UDCPR applicability regime selector - DEFERRED
  Reason: regulation regime selector (UDCPR vs own DCR), not an approval applicability
  predicate; encoding under APR-038 would falsely negate building permission in excluded
  jurisdictions (e.g. MCGM, NAINA) where building permission is mandatory under local DCRs.

Jurisdiction isolation and fail-closed safety are verified throughout.
"""
from __future__ import annotations

import pytest

from app.rules.facts import (
    MH_FACTS,
    FactValueType,
    get_fact_spec,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import IN_GJ, load_regulatory_pack

PLANNING_FIRE_CLUSTER_RULE_IDS: frozenset[str] = frozenset({
    "R-041",
    "R-078",
    "R-079",
    "R-080",
    "R-082",
})


class TestPlanningFireClusterPackExclusion:
    """Verify that all 5 cluster rules are safe candidates but excluded from pack."""

    def test_candidates_in_safe_set(self):
        """All 5 rules were transcribed as IMPLEMENTATION_SAFE in rule_register_v5.csv."""
        for rule_id in PLANNING_FIRE_CLUSTER_RULE_IDS:
            assert rule_id in MH_IMPLEMENTATION_SAFE_RULE_IDS, f"{rule_id} must be in safe set"

    def test_candidates_excluded_from_pack(self):
        """None of the 5 rules must be loaded in the active MH approval rules."""
        active_rules = {r.id for r in load_mh_approval_rules()}
        for rule_id in PLANNING_FIRE_CLUSTER_RULE_IDS:
            assert rule_id not in active_rules, f"{rule_id} must NOT be in active pack"
            assert rule_id not in MH_INCLUDED_RULE_IDS, f"{rule_id} must NOT be in included IDs"

    def test_total_mh_rule_count_unchanged(self):
        """MH pack rule count remains exactly 26 (batch 1 + batch 2 + location cluster)."""
        rules = load_mh_approval_rules()
        assert len(rules) == 26

    def test_all_five_in_deferred_dict(self):
        """All 5 rules must be registered in MH_DEFERRED_RULES with explicit reasons."""
        for rule_id in PLANNING_FIRE_CLUSTER_RULE_IDS:
            assert rule_id in MH_DEFERRED_RULES, f"{rule_id} must be in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rule_id].strip()) > 20, (
                f"{rule_id} deferral reason must be substantive"
            )

    def test_encode_raises_for_deferred(self):
        """_encode() must reject any of the 5 rules fail-closed."""
        for rule_id in PLANNING_FIRE_CLUSTER_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rule_id} is deferred:"):
                _encode(rule_id, "APR-TEST", [], [])


class TestPlanningFireDeferralRationales:
    """Verify specific regulatory/engine rationales for deferral."""

    def test_r041_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-041"]
        assert "construction" in reason
        assert "R-080" in reason or "authority" in reason
        assert "R-082" in reason or "DCR" in reason
        assert "APR-038" in reason

    def test_r078_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-078"]
        assert "FIRE_AUTHORITY" in reason
        assert "authority routing" in reason
        assert "R-047" in reason

    def test_r079_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-079"]
        assert "Schedule-I" in reason
        assert "F-LOC-01==False" in reason or "non-MIDC" in reason
        assert "APR-039" in reason
        assert "MIDC" in reason

    def test_r080_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-080"]
        assert "BP_AUTHORITY" in reason
        assert "authority routing" in reason
        assert "R-047" in reason

    def test_r082_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-082"]
        assert "UDCPR" in reason
        assert "regulation regime selector" in reason or "regime selector" in reason
        assert "excluded jurisdictions" in reason or "APR-038" in reason


class TestFactRegistryPlanningFireCoverage:
    """Verify state of planning & fire facts in facts.py."""

    def test_floc01_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-LOC-01")
        assert spec.label == "site_in_midc_estate"
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True

    def test_floc05_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-LOC-05")
        assert spec.label == "planning_authority"
        assert spec.value_type == FactValueType.ENUM
        assert "MIDC" in spec.allowed_values
        assert "RP_AREA_COLLECTOR" in spec.allowed_values

    def test_fpa02_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-PA-02")
        assert spec.label == "planning_or_local_authority_has_CFO"
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True

    def test_fbld10_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-BLD-10")
        assert spec.label == "MFPLSM_Schedule_I_building_class"
        assert spec.value_type == FactValueType.ENUM
        assert {"G-1", "G-2", "G-3", "H", "J"} <= set(spec.allowed_values)
        assert spec.unknown_allowed is True

    def test_fbld11_fact_present(self):
        spec = get_fact_spec("IN-MH", "F-BLD-11")
        assert spec.label == "aggregate_floor_area_largest_building_m2"
        assert spec.value_type == FactValueType.NUMBER
        assert spec.unknown_allowed is True

    def test_construction_fact_absent_from_registry(self):
        """Confirm 'construction' fact is unmodeled, preventing sound R-041 evaluation."""
        assert "construction" not in MH_FACTS
        assert "F-CONSTRUCT" not in MH_FACTS


class TestSemanticRiskDemonstrations:
    """Demonstrate why standalone encoding of partial predicates creates legal hazards."""

    def test_r079_hazard_of_missing_non_midc_guard(self):
        """R-079 predicate is solely building class (F-BLD-10).

        If encoded under APR-039 ('Provisional fire NOC (non-MIDC)'), a facility
        with F-BLD-10='J' located inside MIDC (F-LOC-01=True) would match APR-039,
        even though MIDC facilities must obtain fire approval from MIDC Fire Services
        under APR-030 / R-036.
        """
        # A chemical manufacturing unit inside MIDC estate:
        project_in_midc = {
            "F-LOC-01": True,
            "F-BLD-10": "J",
        }
        # In isolation, F-BLD-10 is 'J', which satisfies R-079:
        schedule_1_match = project_in_midc["F-BLD-10"] in {"G-1", "G-2", "G-3", "H", "J"}
        assert schedule_1_match is True

        # But applying APR-039 (non-MIDC fire NOC) to an MIDC estate is legally false:
        is_non_midc = not project_in_midc["F-LOC-01"]
        assert is_non_midc is False
        # Therefore, standalone R-079 would falsely trigger non-MIDC approval for MIDC units.

    def test_r082_hazard_of_negating_building_permission(self):
        """R-082 specifies where UDCPR applies vs local DCR.

        If encoded under APR-038 ('Building permission') as F-LOC-05 NOT IN {MCGM, ...},
        a facility in MCGM limits would evaluate to DOES_NOT_APPLY for APR-038.
        In reality, building permission is strictly mandatory under MCGM's DCPR 2034.
        """
        # A project located in Mumbai (MCGM):
        mcgm_excluded_from_udcpr = True  # per UDCPR Reg. 1.1
        # If R-082 were treated as applicability condition for building permission:
        udcpr_applies = not mcgm_excluded_from_udcpr  # False
        assert udcpr_applies is False

        # Treating UDCPR non-applicability as building permission DOES_NOT_APPLY
        # would be a catastrophic false negative for statutory compliance.

    def test_authority_routing_rules_are_not_applicability_predicates(self):
        """R-078 and R-080 compute authority entities/strings, not booleans.

        R-078 computes FIRE_AUTHORITY string (e.g. 'Chief Fire Officer of ...').
        R-080 computes BP_AUTHORITY string (e.g. 'Collector', 'MIDC (SPA)').
        Neither can be encoded as an ApplicabilityCondition without engine support
        for dynamic authority assignment.
        """
        # Verify both rules are documented as authority routing
        assert "authority routing" in MH_DEFERRED_RULES["R-078"]
        assert "authority routing" in MH_DEFERRED_RULES["R-080"]


class TestJurisdictionIsolation:
    """Verify that IN-MH planning & fire audit does not affect IN-GJ."""

    def test_gj_pack_isolation(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        gj_rule_ids = {r.id for r in gj_pack.approval_rules}
        for rule_id in PLANNING_FIRE_CLUSTER_RULE_IDS:
            assert rule_id not in gj_rule_ids, f"{rule_id} must not be in GJ pack"

    def test_gj_rule_count_unchanged(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19

    def test_global_default_remains_gujarat(self):
        from app.seed.pack import DEFAULT_JURISDICTION
        assert DEFAULT_JURISDICTION == IN_GJ == "IN-GJ"
