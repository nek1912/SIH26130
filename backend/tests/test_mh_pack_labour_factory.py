"""Tests for Maharashtra Labour & Factory Cluster (R-019, R-020, R-027, R-022, R-023, R-090).

This suite audits and verifies the labour and factory establishment cluster rules:
- R-019: MSIHC site notification (Rule 7) - DEFERRED
  Reason: Requires existential quantifier (EXISTS c:) over F-HAZ-01, multi-schedule
  evaluation (Sch 3 col 3 vs Sch 2 col 3), aggregation across storage units, and
  dynamic authority routing per Sch 5 (AUT-005, AUT-003, AUT-008, District Collector)
  unsupported by ConditionNode primitives.
- R-020: MSIHC safety report (Rules 10-12) - DEFERRED
  Reason: Requires existential quantifier (EXISTS c:) over F-HAZ-01, column 4 threshold
  lookup, and aggregation unsupported by condition primitives; unconfirmed col 4 values
  (UR-01 ethylene oxide '501'); targets APR-012 with different lifecycle/frequency.
- R-027: Contractor licence (OSH Code s.45(1)(ii) / s.47) - DEFERRED
  Reason: Contractor worker-count fact absent from registry (mapping to F-LAB-03 would
  be regulatory guessing); applicant is the principal employer / manufacturing occupier,
  not the manpower contractor.
- R-022: Factory threshold / Plan approval & licence (OSH Code s.2(1)(w) / s.79) - DEFERRED
  Reason: Statutory definition of factory under OSH Code s.2(1)(w), not an approval
  applicability predicate; dual target APR-015 (plan approval) and APR-016 (licence);
  sub-threshold (<20/<40) cannot safely evaluate to FALSE due to saved s.85
  hazardous-process notifications (ET-017); requires official confirmation (UNK-029).
- R-023: Factory registration & licence category (DISH online service) - DEFERRED
  Reason: Licence category / fee schedule selector (DISH_LICENCE_CATEGORY := 'MAH/HAZARDOUS'
  | 'OTHER'), not an approval applicability predicate; outputs string classification;
  'hazardous process' criterion unencoded; requires official confirmation.
- R-090: BOCW establishment registration (OSH Code s.2(1)(h) / s.2(1)(v)) - DEFERRED
  Reason: BOCW registration under OSH Code s.2(1)(h) contains statutory exclusion for
  construction related to a factory; whether new factory construction falls within
  exclusion is unresolved in MH (ET-126 requires UNKNOWN); exception fact unmodeled;
  requires official confirmation.

All 6 audited rules are verified deferred fail-closed.
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

AUDITED_LABOUR_FACTORY_RULE_IDS: frozenset[str] = frozenset({
    "R-019",
    "R-020",
    "R-027",
    "R-022",
    "R-023",
    "R-090",
})


def _by_id(rule_id: str):
    for r in load_mh_approval_rules():
        if r.id == rule_id:
            return r
    raise KeyError(rule_id)


class TestLabourFactoryClusterAuditScope:
    """Verify that all 6 audited rules are deferred fail-closed and excluded from active pack."""

    def test_all_audited_rules_accounted_for(self):
        assert len(AUDITED_LABOUR_FACTORY_RULE_IDS) == 6

    def test_all_audited_rules_excluded_from_active_pack(self):
        rules = load_mh_approval_rules()
        active_ids = {r.id for r in rules}
        for rule_id in AUDITED_LABOUR_FACTORY_RULE_IDS:
            assert rule_id not in active_ids, f"{rule_id} must not be in active MH rules"
            assert rule_id not in MH_INCLUDED_RULE_IDS

    def test_active_rule_count_unchanged_at_26(self):
        """Active pack rule count must remain exactly 26."""
        assert len(load_mh_approval_rules()) == 26

    def test_all_audited_rules_registered_in_deferred_dict(self):
        for rule_id in AUDITED_LABOUR_FACTORY_RULE_IDS:
            assert rule_id in MH_DEFERRED_RULES, f"{rule_id} must be in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rule_id].strip()) > 30

    def test_encode_raises_for_all_audited_rules(self):
        for rule_id in AUDITED_LABOUR_FACTORY_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rule_id} is deferred:"):
                _encode(rule_id, "APR-TEST", [], [])


class TestLabourFactoryDeferralRationales:
    """Verify specific regulatory/engine rationales for all 6 deferrals."""

    def test_r019_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-019"]
        assert "EXISTS" in reason or "existential quantifier" in reason
        assert "F-HAZ-01" in reason
        assert "Sch 3" in reason and "Sch 2" in reason
        assert "AUT-005" in reason or "authority" in reason

    def test_r020_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-020"]
        assert "EXISTS" in reason or "existential quantifier" in reason
        assert "column 4" in reason or "col 4" in reason
        assert "UR-01" in reason or "APR-012" in reason

    def test_r027_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-027"]
        assert "contractor worker-count" in reason or "F-LAB-03" in reason
        assert "principal employer" in reason or "guessing" in reason

    def test_r022_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-022"]
        assert "s.2(1)(w)" in reason or "definition of factory" in reason
        assert "APR-015" in reason and "APR-016" in reason
        assert "s.85" in reason or "ET-017" in reason
        assert "UNK-029" in reason or "confirmation" in reason

    def test_r023_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-023"]
        assert "DISH_LICENCE_CATEGORY" in reason or "category" in reason.lower()
        assert "MAH/HAZARDOUS" in reason
        assert "classification" in reason or "selector" in reason

    def test_r090_deferral_rationale(self):
        reason = MH_DEFERRED_RULES["R-090"]
        assert "s.2(1)(h)" in reason
        assert "factory" in reason
        assert "ET-126" in reason or "exclusion" in reason


class TestFactRegistryLabourCoverage:
    """Verify state of labour, factory, and hazard facts in facts.py."""

    def test_flab_facts_present(self):
        keys = set(mh_fact_keys())
        expected_flab = {
            "F-LAB-01", "F-LAB-02", "F-LAB-03", "F-LAB-04", "F-LAB-05",
            "F-LAB-06", "F-LAB-07", "F-LAB-08", "F-LAB-09", "F-LAB-10",
        }
        assert expected_flab <= keys

    def test_flab_fact_types(self):
        assert get_fact_spec("IN-MH", "F-LAB-01").value_type == FactValueType.INTEGER
        assert get_fact_spec("IN-MH", "F-LAB-02").value_type == FactValueType.BOOLEAN
        assert get_fact_spec("IN-MH", "F-LAB-03").value_type == FactValueType.INTEGER
        assert get_fact_spec("IN-MH", "F-LAB-04").value_type == FactValueType.BOOLEAN
        assert get_fact_spec("IN-MH", "F-LAB-05").value_type == FactValueType.INTEGER
        assert get_fact_spec("IN-MH", "F-LAB-06").value_type == FactValueType.INTEGER
        assert get_fact_spec("IN-MH", "F-LAB-07").value_type == FactValueType.BOOLEAN
        assert get_fact_spec("IN-MH", "F-LAB-08").value_type == FactValueType.NUMBER
        assert get_fact_spec("IN-MH", "F-LAB-09").value_type == FactValueType.BOOLEAN
        assert get_fact_spec("IN-MH", "F-LAB-10").value_type == FactValueType.BOOLEAN

    def test_fhaz_and_fprc_facts_present(self):
        assert get_fact_spec("IN-MH", "F-HAZ-01").value_type == FactValueType.LIST
        assert get_fact_spec("IN-MH", "F-HAZ-02").value_type == FactValueType.LIST
        assert get_fact_spec("IN-MH", "F-HAZ-03").value_type == FactValueType.LIST
        assert get_fact_spec("IN-MH", "F-PRC-03").value_type == FactValueType.BOOLEAN
        assert get_fact_spec("IN-MH", "F-PRC-03").derived is True

    def test_unmodeled_facts_confirmed_absent(self):
        """Confirm facts that must NOT be guessed are absent from the registry."""
        from app.rules.facts import MH_FACTS
        # Contractor's own workforce count
        # (distinct from principal employer contract labour F-LAB-03)
        assert "F-LAB-CONTRACTOR-WORKERS" not in MH_FACTS
        assert "contractor_workers" not in MH_FACTS
        # BOCW factory construction exclusion flag under s.2(1)(h)
        assert "F-BOCW-FACTORY-EXCLUSION" not in MH_FACTS
        # DISH licence category string
        assert "DISH_LICENCE_CATEGORY" not in MH_FACTS


class TestSemanticRiskDemonstrations:
    """Demonstrate why naive implementation of these 6 rules causes serious legal hazards."""

    def test_r022_sub_threshold_false_negative_hazard(self):
        """R-022: Under OSH Code s.2(1)(w), a factory is >=20 workers (with power) or >=40.

        If naively encoded as:
            (F-LAB-02 == True and F-LAB-01 >= 20) or (F-LAB-02 == False and F-LAB-01 >= 40)

        A chemical manufacturing plant with power and 15 workers would evaluate to DOES_NOT_APPLY.
        However, under Section 85 of the Factories Act 1948 (saved under OSH Code Section 143(3))
        and OSH Code Section 81, State Government notifications apply factory provisions to
        small units carrying on dangerous operations / hazardous processes regardless of headcount.
        ET-017 explicitly requires:
            inputs: power=TRUE; workers=19 -> FACTORY_BY_HEADCOUNT=FALSE; overall=CONDITIONAL.
        A naive boolean rule would falsely tell a chemical unit that factory plan approval and
        licensing do not apply, creating a severe regulatory violation.
        """
        power = True
        workers = 19
        naive_factory_applies = (power and workers >= 20) or (not power and workers >= 40)
        assert naive_factory_applies is False

        # But under regulatory truth (ET-017 / UNK-030 / s.85 savings):
        # Result cannot be FALSE; it must be CONDITIONAL / UNKNOWN.
        assert "R-022" in MH_DEFERRED_RULES

    def test_r022_dual_approval_lifecycle_conflation(self):
        """R-022 targets both APR-015 (Plan Approval) and APR-016 (Licence).

        Plan approval is pre-construction (prior to building erection/extension).
        Licence is pre-operation (prior to running manufacturing process).
        Conflating two distinct statutory lifecycle gates under a single ApprovalRule
        violates the 1:1 approval identity model.
        """
        assert "APR-015" in MH_DEFERRED_RULES["R-022"]
        assert "APR-016" in MH_DEFERRED_RULES["R-022"]

    def test_r023_classification_vs_applicability_hazard(self):
        """R-023 condition: DISH_LICENCE_CATEGORY := 'MAH/HAZARDOUS' IF MAH==TRUE ELSE 'OTHER'.

        This is a licence category selector determining DISH scrutiny stream, fee schedule,
        and SLA (30 days vs 7 days), NOT an approval applicability predicate.
        It returns a string category, not a boolean APPLIES / DOES_NOT_APPLY.
        Encoding it as an ApprovalRule predicate would be a severe semantics violation.
        """
        category_mah = "MAH/HAZARDOUS"
        category_other = "OTHER"
        assert category_mah not in [True, False]
        assert category_other not in [True, False]
        assert "R-023" in MH_DEFERRED_RULES

    def test_r027_contractor_vs_principal_employer_guessing_hazard(self):
        """R-027 condition: CONTRACTOR_LIC := F-LAB-04 == TRUE AND contractor_workers >= 50.

        F-LAB-04 is is_contractor.
        F-LAB-03 is max_contract_labour engaged by the principal employer.
        Mapping contractor_workers to F-LAB-03 would conflate the number of contract workers
        hired by the plant with the contractor's own workforce.
        Furthermore, our applicant is the industrial manufacturing occupier (principal employer),
        whereas APR-020 is an obligation of the independent contractor providing manpower.
        """
        assert "contractor worker-count" in MH_DEFERRED_RULES["R-027"]
        assert "principal employer" in MH_DEFERRED_RULES["R-027"]

    def test_r090_bocw_factory_exclusion_omission_hazard(self):
        """R-090 condition: BOCW := F-LAB-05 >= 10 AND construction NOT excluded by s.2(1)(h).

        Section 2(1)(h) of the OSH Code 2020 explicitly excludes:
            'any building or other construction work to which the provisions of the
             Factories Act, 1948 or the provisions of this Code relating to factories apply'.

        If naively encoded as F-LAB-05 >= 10:
        A factory project with 25 construction workers would evaluate to APPLIES.
        However, whether new factory construction is covered by the s.2(1)(h) factory exclusion
        is an unresolved legal interpretation in Maharashtra (ET-126 explicitly requires UNKNOWN).
        Encoding F-LAB-05 >= 10 alone silently omits the statutory exclusion and contradicts ET-126.
        """
        construction_workers = 25
        naive_bocw_applies = construction_workers >= 10
        assert naive_bocw_applies is True

        # But statutory truth under ET-126: expected is UNKNOWN due to s.2(1)(h) exclusion.
        assert "R-090" in MH_DEFERRED_RULES
        assert "s.2(1)(h)" in MH_DEFERRED_RULES["R-090"]

    def test_r019_msihc_quantifier_and_routing_complexity(self):
        """R-019: Site notification under Rule 7 MSIHC requires existential quantifier

        (EXISTS c: agg_qty(c) >= col3(c)), multi-schedule evaluation (Sch 4 / Sch 3 vs
        Sch 2 isolated storage), and multi-authority routing under Schedule 5.
        It cannot be expressed using flat ConditionNode primitives or mapped to F-PRC-03 alone.
        """
        assert "EXISTS" in MH_DEFERRED_RULES["R-019"]
        assert "R-019" in MH_DEFERRED_RULES

    def test_r020_msihc_col4_threshold_divergence_and_evidence_gap(self):
        """R-020: Safety report under Rule 10 MSIHC requires column 4 thresholds.

        Column 4 thresholds are significantly higher than column 3 (site notification).
        derive_mah_status() only evaluates column 3.
        In addition, official gazette scans contain unconfirmed values (UR-01: ethylene oxide
        printed '501' in S.O. 2882; ET-v4-06 and ET-v5-05 require UNKNOWN).
        """
        assert "column 4" in MH_DEFERRED_RULES["R-020"]
        assert "UR-01" in MH_DEFERRED_RULES["R-020"]
        assert "R-020" in MH_DEFERRED_RULES


class TestExistingLabourRulesUnaffected:
    """Verify that previously implemented labour/establishment rules remain fully functional."""

    def test_r026_principal_employer_active_and_correct(self):
        """R-026: Principal employer registration under CLRA / OSH s.45 (APR-019)."""
        rule = _by_id("R-026")
        assert rule.approval_id == "APR-019"
        # >= 50 and not casual -> APPLIES
        res_applies = evaluate_rule(rule, {"F-LAB-03": 50, "F-LAB-09": False})
        assert res_applies.result == ApprovalResult.APPLIES
        # < 50 -> DOES_NOT_APPLY
        res_below = evaluate_rule(rule, {"F-LAB-03": 49, "F-LAB-09": False})
        assert res_below.result == ApprovalResult.DOES_NOT_APPLY
        # Casual exception -> DOES_NOT_APPLY
        res_casual = evaluate_rule(rule, {"F-LAB-03": 50, "F-LAB-09": True})
        assert res_casual.result == ApprovalResult.DOES_NOT_APPLY
        # Missing exception fact -> INSUFFICIENT_DATA (fail-closed)
        assert evaluate_rule(rule, {"F-LAB-03": 50}).result == ApprovalResult.INSUFFICIENT_DATA

    def test_r070_safety_officer_active_and_correct(self):
        """R-070: Safety officer headcount bands under OSH s.22(2) (CMP-018)."""
        rule = _by_id("R-070")
        assert rule.approval_id == "CMP-018"
        # Non-hazardous: >= 500
        assert evaluate_rule(
            rule, {"F-LAB-07": False, "F-LAB-01": 500}
        ).result == ApprovalResult.APPLIES
        assert evaluate_rule(
            rule, {"F-LAB-07": False, "F-LAB-01": 499}
        ).result == ApprovalResult.DOES_NOT_APPLY
        # Hazardous: >= 250
        assert evaluate_rule(
            rule, {"F-LAB-07": True, "F-LAB-01": 250}
        ).result == ApprovalResult.APPLIES
        assert evaluate_rule(
            rule, {"F-LAB-07": True, "F-LAB-01": 249}
        ).result == ApprovalResult.DOES_NOT_APPLY

    def test_r089_ismw_active_and_correct(self):
        """R-089: Inter-State Migrant Workers threshold >= 10 under OSH s.59 (APR-022)."""
        rule = _by_id("R-089")
        assert rule.approval_id == "APR-022"
        assert evaluate_rule(rule, {"F-LAB-08": 10}).result == ApprovalResult.APPLIES
        assert evaluate_rule(rule, {"F-LAB-08": 9}).result == ApprovalResult.DOES_NOT_APPLY
        assert evaluate_rule(rule, {}).result == ApprovalResult.INSUFFICIENT_DATA


class TestJurisdictionIsolation:
    """Verify that IN-MH labour/factory audit does not affect IN-GJ."""

    def test_gj_pack_isolation(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        gj_rule_ids = {r.id for r in gj_pack.approval_rules}
        for rule_id in AUDITED_LABOUR_FACTORY_RULE_IDS:
            assert rule_id not in gj_rule_ids, f"{rule_id} must not be in GJ pack"

    def test_gj_rule_count_unchanged(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19

    def test_global_default_remains_gujarat(self):
        assert DEFAULT_JURISDICTION == IN_GJ == "IN-GJ"
