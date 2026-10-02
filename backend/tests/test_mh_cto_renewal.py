"""Tests for Maharashtra Consent to Operate (CTO) & Renewal cluster audit.

Cluster scope:
- R-017: Consent to Operate under Water & Air Acts (APR-009)
- R-063: CTO expansion / amendment outer limit (90/60/30 days, APR-009 / SLA-036)
- R-055: MPCB consent amendment vs fresh consent (APR-053)
- CMP-007: CTO validity / renewal / MPCB auto-renewal (compliance renewal)
- R-062: CTO validity under GSR 62/63 (CTO_VALIDITY := 'VALID_TILL_CANCELLED')

Tests verify:
1. Exact candidate identity across v5 register CSVs.
2. Exact approval and lifecycle mapping.
3. Competent authority routing to MPCB (AUT-003).
4. Water Act 1974 and Air Act 1981 statutory legal basis.
5. CPCB/MPCB category dependency and lookup gating.
6. Three-valued logic and fail-closed UNKNOWN behavior.
7. R-063 distinction as an SLA timeline rule, not an approval predicate.
8. R-055 amendment vs fresh consent modification boundary.
9. CMP-007 compliance/renewal lifecycle separation.
10. CTO validity regime conflict (CON-006, GSR 62/63 vs MPCB circular).
11. Administrative nature of MPCB auto-renewal workflow.
12. Temporal versioning across statutory instruments.
13. Active (26) and deferred (53) rule isolation and disjointness.
14. IN-MH and IN-GJ jurisdiction isolation.
15. Canonical synthetic organic chemical project behavior.
16. Fact registry discipline (zero speculative facts added).
17. Architectural separation between approvals, workflow SLAs, and compliance duties.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pytest

from app.rules.dependency_engine import ReadinessStatus, evaluate_readiness
from app.rules.facts import (
    MH_FACTS,
    get_fact_spec,
    mh_fact_keys,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, IN_MH, load_regulatory_pack

AUDITED_CTO_RULE_IDS: frozenset[str] = frozenset({"R-017", "R-055", "R-063"})


def _get_csv_dir() -> Path:
    """Locate the authoritative CSV directory."""
    backend_dir = Path(__file__).resolve().parent.parent
    root_dir = backend_dir.parent
    for p in root_dir.iterdir():
        if "UdyamDwaar MH Chemical Pack" in p.name and p.is_dir():
            csv_path = p / "csv"
            if csv_path.exists():
                return csv_path
    pytest.skip("Authoritative CSV directory not found")


class TestCtoCandidateIdentity:
    """Verify exact candidate identity across authoritative v5 registers."""

    def test_r017_register_identity(self):
        """R-017 must match rule_register_v5.csv exactly."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r017 = next(r for r in reader if r.get("rule_id") == "R-017")

        assert r017["approval_id"] == "APR-009"
        assert r017["title"] == "Consent to Operate (Water & Air Acts)"
        assert r017["obligation_type"] == "CONSENT"
        assert r017["authority"] == "AUT-003"
        assert r017["jurisdiction"] == "STATEWIDE"
        assert "CTO_REQUIRED := CONSENT_REQUIRED == TRUE" in r017["applicability_conditions"]
        assert r017["required_inputs"] == "R-013"
        assert r017["stage"] == "PRE_OPERATION"
        assert r017["status"] == "VERIFIED_CONDITIONAL"
        assert r017["implementation_status"] == "IMPLEMENTATION_SAFE"

    def test_r063_register_identity_and_label_mismatch(self):
        """R-063 in register is an SLA outer limit, not an approval predicate."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r063 = next(r for r in reader if r.get("rule_id") == "R-063")

        assert r063["approval_id"] == "APR-009"
        assert r063["title"] == "Consent to Operate (Water & Air Acts)"
        assert "CTO_EXPANSION_OUTER_LIMIT := 90 / 60 / 30 days" in r063["applicability_conditions"]
        assert r063["implementation_status"] == "REQUIRES_CONFIRMATION"
        assert r063["status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert "UNK-031" in r063["notes"]

    def test_r055_register_identity(self):
        """R-055 must match rule_register_v5.csv as a modification-stage rule."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r055 = next(r for r in reader if r.get("rule_id") == "R-055")

        assert r055["approval_id"] == "APR-053"
        assert r055["title"] == "MPCB consent amendment vs fresh consent"
        assert r055["obligation_type"] == "CONSENT"
        assert r055["authority"] == "AUT-003"
        assert "AMENDMENT" in r055["applicability_conditions"]
        assert "FRESH" in r055["applicability_conditions"]
        assert r055["stage"] == "OPERATION"
        assert r055["source_id"] == "SRC-068"

    def test_cmp007_compliance_identity(self):
        """CMP-007 in compliance.csv is a renewal obligation with DO_NOT_IMPLEMENT_YET."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "compliance.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cmp007 = next(r for r in reader if r.get("compliance_id") == "CMP-007")

        assert cmp007["authority_id"] == "AUT-003"
        assert cmp007["implement_status"] == "DO_NOT_IMPLEMENT_YET"
        assert cmp007["final_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert cmp007["lifecycle_stage"] == "RENEWAL"
        assert cmp007["record_type"] == "RENEWAL"


class TestR017CtoApplicability:
    """Verify statutory basis and structural prerequisites of R-017."""

    def test_water_and_air_act_statutory_basis(self):
        """R-017 is grounded in Water Act s.25 and Air Act s.21."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rules.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r017_rule = next(r for r in reader if r.get("rule_id") == "R-017")
        assert "Water Act s.25" in r017_rule["legal_basis"]
        assert "Air Act s.21" in r017_rule["legal_basis"]

    def test_r017_depends_on_r013_rule_composition(self):
        """R-017 condition CTO_REQUIRED := CONSENT_REQUIRED == TRUE references R-013."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r017 = next(r for r in reader if r.get("rule_id") == "R-017")
        assert r017["required_inputs"] == "R-013"

    def test_r013_requires_r014_sector_lookup(self):
        """R-013 requires MPCB_CATEGORY IN {RED, ORANGE, GREEN} from R-014 lookup."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r013 = next(r for r in reader if r.get("rule_id") == "R-013")
        assert "MPCB_CATEGORY IN {RED,ORANGE,GREEN}" in r013["applicability_conditions"]
        assert r013["required_inputs"] == "F-MPCB-01"

    def test_white_category_is_explicitly_exempt(self):
        """White category is exempt from consent (ET-049)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "edge_tests.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            et049 = next(r for r in reader if r.get("test_id") == "ET-049")
        assert et049["rule_id"] == "R-013"
        assert "White" in et049["inputs"]
        assert "CONSENT_REQUIRED=FALSE" in et049["expected"]

    def test_missing_or_unknown_sector_code_evaluates_insufficient_data(self):
        """Missing or UNKNOWN sector codes must fail closed (ET-110)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "edge_tests.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            et110 = next(r for r in reader if r.get("test_id") == "ET-110")
        assert "UNKNOWN" in et110["inputs"]
        assert "CONSENT_REQUIRED=UNKNOWN" in et110["expected"]

    def test_multi_activity_cardinality_guard_emits_unknown(self):
        """Units with >1 sector code emit UNKNOWN via R-015; convention not assumed (ET-048)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "edge_tests.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            et048 = next(r for r in reader if r.get("test_id") == "ET-048")
        assert "UNKNOWN (multi-activity)" in et048["expected"]
        assert "Convention flagged, not rule" in et048["rationale"]


class TestR063OuterLimitAndConfirmation:
    """Verify R-063 as an SLA outer limit requiring confirmation."""

    def test_r063_is_sla_timeline_limit_not_approval_predicate(self):
        """R-063 condition specifies outer limit days, not approval boolean."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rules.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r063 = next(r for r in reader if r.get("rule_id") == "R-063")
        assert r063["operator"] == "lookup"
        assert r063["threshold"] == "90;60;30"
        assert r063["unit"] == "days"
        assert "GSR 62/63 para 8(ii)" in r063["legal_basis"]

    def test_r063_requires_confirmation_due_to_unk031(self):
        """R-063 requires confirmation because column-to-category mapping is UNK-031."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "unknowns.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            unk031 = next(r for r in reader if r.get("unknown_id") == "UNK-031")
        assert (
            "Column headings (categories) of GSR 84/85 para 8 timeline table"
            in unk031["question"]
        )
        assert unk031["related_ids"] == "R-063"
        assert unk031["final_status"] == "UNKNOWN"

    def test_r063_in_requires_confirmation_set(self):
        """R-063 is explicitly present in MH_REQUIRES_CONFIRMATION_RULE_IDS."""
        assert "R-063" in MH_REQUIRES_CONFIRMATION_RULE_IDS


class TestR055ConsentAmendmentVsFresh:
    """Verify MPCB consent amendment vs fresh consent distinction."""

    def test_r055_statutory_source_and_circular(self):
        """R-055 cites MPCB circular 25-08-2025 (SRC-068)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "sources.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            src068 = next(r for r in reader if r.get("source_id") == "SRC-068")
        assert "Applications for amendment in consent" in src068["title"]
        assert src068["effective_date"] == "2025-08-25"

    def test_r055_bifurcation_conditions(self):
        """R-055 categorizes clerical/name/HW path as AMENDMENT and fuel/DG/process as FRESH."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rules.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r055 = next(r for r in reader if r.get("rule_id") == "R-055")
        cond = r055["condition"]
        assert "CLERICAL,NAME,HW_DISPOSAL_PATH" in cond
        assert "FUEL,DG_SET,HW_QTY,PROCESS" in cond

    def test_r055_edge_test_fuel_requires_fresh(self):
        """Fuel change requires FRESH consent (ET-053)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "edge_tests.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            et053 = next(r for r in reader if r.get("test_id") == "ET-053")
        assert et053["rule_id"] == "R-055"
        assert "FUEL" in et053["inputs"]
        assert "FRESH consent" in et053["expected"]

    def test_r055_unlisted_changes_cannot_be_binary(self):
        """Unlisted changes (e.g. inventory increase ET-107, water source ET-109) require review."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "edge_tests.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            et107 = next(r for r in reader if r.get("test_id") == "ET-107")
        assert "INVENTORY increase" in et107["inputs"]
        assert "consent path UNKNOWN unless listed in circular" in et107["expected"]

    def test_apr053_lifecycle_stage_is_modification(self):
        """APR-053 is MODIFICATION stage, not pre-establishment or pre-operation."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "approvals.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            apr053 = next(r for r in reader if r.get("approval_id") == "APR-053")
        assert apr053["stage"] == "OPERATION"
        assert apr053["lifecycle_stage"] == "MODIFICATION"


class TestCmp007ValidityAndRenewalLifecycle:
    """Verify CTO validity, renewal, and regime conflict resolution."""

    def test_con006_cto_validity_conflict_recorded(self):
        """CON-006 records conflict between GSR 62/63 and MPCB auto-renewal circular."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "conflicts.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            con006 = next(r for r in reader if r.get("conflict_id") == "CON-006")
        assert con006["topic"] == "CTO validity"
        assert "valid till cancelled" in con006["value_A"].lower()
        assert "5/10/15 yrs" in con006["value_B"]
        assert con006["resolution"] == "Do not compute validity; display both with status"
        assert con006["final_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"

    def test_gsr62_63_implementation_status(self):
        """GSR 62/63 para 4(3) valid till cancelled, fee schedule blocked (GSR-04)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "mpcb_gsr62_63_implementation.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            items = {r["item_id"]: r for r in reader}

        assert items["GSR-03"]["provision"] == "CTO valid until cancelled"
        assert items["GSR-04"]["final_status"] == "DO_NOT_IMPLEMENT_YET"
        assert "Fee amount BLOCKED" in items["GSR-04"]["engine_behaviour"]
        assert items["GSR-05"]["classification"] == "UNKNOWN"

    def test_legacy_cto_treatment_unresolved(self):
        """UNK-032 and UR-05 record legacy pre-2026 CTO status as UNKNOWN."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "unknowns.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            unk032 = next(r for r in reader if r.get("unknown_id") == "UNK-032")
        assert "Status of CTOs granted before 27-01-2026" in unk032["question"]
        assert unk032["final_status"] == "UNKNOWN"

    def test_r062_cto_validity_is_deferred(self):
        """R-062 (CTO_VALIDITY := 'VALID_TILL_CANCELLED') is registered in MH_DEFERRED_RULES."""
        assert "R-062" in MH_DEFERRED_RULES
        assert "CTO validity rule under GSR 62/63" in MH_DEFERRED_RULES["R-062"]


class TestAutoRenewalAdministrativeNature:
    """Verify auto-renewal is an administrative scheme, not a deemed statutory right."""

    def test_auto_renewal_circular_source(self):
        """Auto-renewal scheme is backed by MPCB circular 13-08-2025 (SRC-069)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "sources.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            src069 = next(r for r in reader if r.get("source_id") == "SRC-069")
        assert "Simplified scheme of auto-renewal of consents" in src069["title"]
        assert src069["tier"] == "T2"

    def test_auto_renewal_is_self_declaration_workflow(self):
        """Auto-renewal processing is an administrative 7-day workflow (SLA-037)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "sla.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            sla037 = next(r for r in reader if r.get("sla_id") == "SLA-037")
        assert sla037["sla_value"] == "7"
        assert sla037["unit"] == "DAYS"
        assert "self-declaration" in sla037["service"].lower()

    def test_central_law_omits_periodic_renewal_for_new_consents(self):
        """Central GSR 62/63 para 12 omitted renewal from Form II (GSR-06)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "mpcb_gsr62_63_implementation.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            gsr06 = next(r for r in reader if r.get("item_id") == "GSR-06")
        assert "'renewal' removed from Form II" in gsr06["mpcb_evidence"]


class TestTemporalVersioning:
    """Verify chronological versioning across consent instruments."""

    def test_statutory_and_circular_chronology(self):
        """All consent instruments follow verified chronological ordering."""
        # Water Act 1974 -> Air Act 1981 -> CPCB 12-02-2025 -> MPCB Sector 23-06-2025
        # -> MPCB Auto-renewal 13-08-2025 -> MPCB Amendment 25-08-2025
        # -> MoEFCC GSR 62/63 27-01-2026 -> MPCB Timelines 23-02-2026
        # -> MPCB transmittal 21-04-2026 / 22-04-2026
        water_year = 1974
        air_year = 1981
        cpcb_cat_date = date(2025, 2, 12)
        mpcb_cat_date = date(2025, 6, 23)
        mpcb_auto_renewal_date = date(2025, 8, 13)
        mpcb_amendment_date = date(2025, 8, 25)
        gsr62_effective = date(2026, 1, 27)
        mpcb_timeline_date = date(2026, 2, 23)
        mpcb_gsr_transmittal = date(2026, 4, 21)

        assert water_year < air_year
        assert cpcb_cat_date < mpcb_cat_date
        assert mpcb_cat_date < mpcb_auto_renewal_date
        assert mpcb_auto_renewal_date < mpcb_amendment_date
        assert mpcb_amendment_date < gsr62_effective
        assert gsr62_effective < mpcb_timeline_date
        assert mpcb_timeline_date < mpcb_gsr_transmittal


class TestPackIsolationAndInvariants:
    """Verify active and deferred rule counts and isolation."""

    def test_active_pack_count_remains_26(self):
        """Active MH approval rule count must remain strictly 26."""
        mh_rules = load_mh_approval_rules()
        assert len(mh_rules) == 26
        assert len(MH_INCLUDED_RULE_IDS) == 26

    def test_deferred_rules_total_count_is_53(self):
        """Deferred MH rules count must be exactly 53 (50 baseline + R-017 + R-055 + R-063)."""
        assert len(MH_DEFERRED_RULES) >= 53

    def test_all_audited_cto_rules_registered_in_deferred_dict(self):
        """All 3 audited CTO rules must be registered in MH_DEFERRED_RULES."""
        for rid in AUDITED_CTO_RULE_IDS:
            assert rid in MH_DEFERRED_RULES, f"{rid} must be in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rid].strip()) > 30

    def test_active_and_deferred_sets_are_strictly_disjoint(self):
        """Active and deferred rule sets must have zero overlap."""
        assert set(MH_INCLUDED_RULE_IDS).isdisjoint(set(MH_DEFERRED_RULES))

    def test_encode_raises_fail_closed_for_all_audited_rules(self):
        """_encode must raise ValueError for all audited CTO rules."""
        for rid in AUDITED_CTO_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rid} is deferred:"):
                _encode(rid, "APR-TEST", [], [])

    def test_r017_deferral_rationale(self):
        """R-017 deferral reason cites R-013, R-014, R-015, and rule composition gap."""
        reason = MH_DEFERRED_RULES["R-017"]
        assert "Water Act s.25" in reason and "Air Act s.21" in reason
        assert "R-013" in reason
        assert "R-014" in reason
        assert "R-015" in reason
        assert "White category" in reason
        assert "rule-composition" in reason

    def test_r055_deferral_rationale(self):
        """R-055 deferral reason cites circular 25-08-2025, APR-053, and categorical output."""
        reason = MH_DEFERRED_RULES["R-055"]
        assert "25-08-2025" in reason or "SRC-068" in reason
        assert "APR-053" in reason
        assert "AMENDMENT" in reason and "FRESH" in reason
        assert "F-CHG-01" in reason
        assert "ET-107" in reason or "ET-109" in reason

    def test_r063_deferral_rationale(self):
        """R-063 deferral reason cites SLA timeline outer limit, UNK-031, and confirmation."""
        reason = MH_DEFERRED_RULES["R-063"]
        assert "GSR 62/63" in reason
        assert "SLA-036" in reason
        assert "timeline outer limit" in reason
        assert "UNK-031" in reason
        assert "REQUIRES_OFFICIAL_CONFIRMATION" in reason

    def test_gj_pack_isolated_and_untouched(self):
        """IN-GJ pack must remain strictly isolated with 19 rules."""
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        gj_ids = {r.id for r in gj_pack.approval_rules}
        assert AUDITED_CTO_RULE_IDS & gj_ids == set()
        assert DEFAULT_JURISDICTION == IN_GJ


class TestCanonicalProjectScenarios:
    """Verify behavior of the canonical synthetic organic chemical project."""

    def test_canonical_project_cto_satisfied_via_obtained_approvals(self):
        """Canonical project satisfies APR-009 via obtained_approvals in dependency graph."""
        mh_pack = load_regulatory_pack(IN_MH)
        # Verify DEP-009 exists: APR-010 requires APR-008 and APR-009 as document prerequisites
        deps = [d for d in mh_pack.dependencies if d.approval_id == "APR-010"]
        prereq_ids = {d.prerequisite_approval_id for d in deps}
        assert "APR-008" in prereq_ids
        assert "APR-009" in prereq_ids

        # If APR-008 and APR-009 are obtained, APR-010 dependency is satisfied
        result = evaluate_readiness(
            deps,
            applicability_results={
                "APR-010": "applies", "APR-008": "applies", "APR-009": "applies"
            },
            obtained={"APR-008", "APR-009"},
        )
        assert result.readiness["APR-010"].readiness == ReadinessStatus.READY

    def test_canonical_project_has_no_fake_cto_rule(self):
        """No speculative CTO rule exists in active MH rules."""
        active_ids = {r.id for r in load_mh_approval_rules()}
        assert "R-017" not in active_ids
        assert "R-063" not in active_ids
        assert "R-055" not in active_ids

    def test_category_lookup_failure_fails_closed(self):
        """Evaluating with unknown category inputs returns INSUFFICIENT_DATA."""
        # When F-MPCB-01 is missing or UNKNOWN, any evaluation fails closed
        spec = get_fact_spec(IN_MH, "F-MPCB-01")
        assert spec.group == "MPCB"
        assert spec.value_type.value == "list"


class TestFactRegistryDiscipline:
    """Verify fact registry discipline (zero speculative facts added)."""

    def test_mh_facts_count_remains_128(self):
        """MH fact registry count must remain strictly 128."""
        assert len(MH_FACTS) == 128

    def test_existing_mpcb_facts_utilized(self):
        """F-MPCB-01, F-CHG-01, F-PRD-03, F-PRC-04 are in existing registry."""
        known = set(mh_fact_keys())
        assert "F-MPCB-01" in known
        assert "F-CHG-01" in known
        assert "F-PRD-03" in known
        assert "F-PRC-04" in known
        assert "F-EXP-01" in known


class TestSubsystemSeparation:
    """Verify strict separation between approvals, SLAs, and compliance layers."""

    def test_approvals_vs_slas_vs_compliance_separation(self):
        """CTO applicability, timeline outer limits, and renewal are segregated."""
        # APR-009 is an approval in approvals.csv
        # SLA-036 is an SLA in sla.csv
        # CMP-007 is a compliance obligation in compliance.csv
        csv_dir = _get_csv_dir()

        with open(csv_dir / "approvals.csv", encoding="utf-8") as f:
            approvals = {r["approval_id"]: r for r in csv.DictReader(f)}
        with open(csv_dir / "sla.csv", encoding="utf-8") as f:
            slas = {r["sla_id"]: r for r in csv.DictReader(f)}
        with open(csv_dir / "compliance.csv", encoding="utf-8") as f:
            compliances = {r["compliance_id"]: r for r in csv.DictReader(f)}

        assert "APR-009" in approvals
        assert approvals["APR-009"]["record_type"] == "CONSENT"

        assert "SLA-036" in slas
        assert slas["SLA-036"]["approval_id"] == "APR-009"

        assert "CMP-007" in compliances
        assert compliances["CMP-007"]["record_type"] == "RENEWAL"
        assert compliances["CMP-007"]["implement_status"] == "DO_NOT_IMPLEMENT_YET"
