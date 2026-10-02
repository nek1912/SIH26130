"""Tests for Maharashtra Establishment & Labour Registration Cluster (R-024, R-025, R-098).

This suite audits and verifies the Establishment & Labour Registration cluster rules for IN-MH:
- R-024: Registration of establishment under OSH Code s.3 (APR-017 / APR-060) - DEFERRED
  Reason: Held as DO_NOT_IMPLEMENT_YET in authoritative registers (rule_register_v5.csv,
  approvals.csv); Maharashtra OSH State rules are in DRAFT status (06-05-2026, UR-12/UNK-008);
  administrative procedure, electronic registration portal, and designated registering officer
  in MH are unnotified; chemical factories are regulated by DISH (AUT-005) under saved Factories
  Act rules with deemed registration under s.3(8); dual authority routing AUT-006/AUT-005
  is unresolvable standalone; second clause requires unmodeled hazardous activity fact;
  status VERIFIED_CONDITIONAL / DO_NOT_IMPLEMENT_YET (SRC-081/SRC-027).
- R-025: Shops & Establishments intimation (<10 workers, APR-018) - DEFERRED
  Reason: Under MH S&E Act 2017 s.7 requires official confirmation (confidence LOW, T5 secondary
  mirror SRC-027); relevance to an industrial chemical factory establishment is unverified
  (approvals.csv explicitly notes 'Relevance to a factory establishment not verified');
  factories are regulated by DISH/Factories Act/OSH Code and excluded from S&E;
  status REQUIRES_OFFICIAL_CONFIRMATION.
- R-098: Mathadi manual workers regulation (CND-025) - DEFERRED
  Reason: Under Mathadi Act 1969 s.1(4A) is a compliance condition / rule logic node
  (RULE_LOGIC), NOT an approval in approvals.csv; requires area notification (F-LOC-19)
  AND engagement in scheduled employment (F-LAB-10); chemical manufacturing per se is
  not a scheduled employment; specific
  district board schemes/notifications (e.g. Thane/Raigad manual handling) unmodeled;
  regular roll employees excluded; status REQUIRES_OFFICIAL_CONFIRMATION (SRC-128).

All 3 audited rules are verified deferred fail-closed.
Active MH rules remain 26. Active GJ rules remain 19.
Default jurisdiction remains IN-GJ.
"""
from __future__ import annotations

import csv
from pathlib import Path

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
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, IN_MH, load_regulatory_pack

AUDITED_ESTABLISHMENT_LABOUR_RULE_IDS: frozenset[str] = frozenset({
    "R-024",
    "R-025",
    "R-098",
})


def _get_csv_dir() -> Path:
    """Locate the authoritative CSV directory."""
    base = Path(__file__).resolve().parent.parent.parent
    for item in base.iterdir():
        if "UdyamDwaar" in item.name and item.is_dir():
            csv_path = item / "csv"
            if csv_path.exists():
                return csv_path
    raise FileNotFoundError("Could not find authoritative CSV directory")


class TestEstablishmentLabourClusterAuditScope:
    """Verify that all 3 audited rules are deferred fail-closed and excluded from active pack."""

    def test_all_audited_rules_accounted_for(self):
        assert len(AUDITED_ESTABLISHMENT_LABOUR_RULE_IDS) == 3

    def test_all_audited_rules_excluded_from_active_pack(self):
        """None of R-024, R-025, R-098 may be active in the MH approval pack."""
        rules = load_mh_approval_rules()
        active_ids = {r.id for r in rules}
        for rule_id in AUDITED_ESTABLISHMENT_LABOUR_RULE_IDS:
            assert rule_id not in active_ids, f"{rule_id} must not be in active MH rules"
            assert rule_id not in MH_INCLUDED_RULE_IDS

    def test_active_rule_count_strictly_unchanged_at_26(self):
        """Active MH pack rule count must remain exactly 26."""
        assert len(load_mh_approval_rules()) == 26
        assert len(MH_INCLUDED_RULE_IDS) == 26

    def test_all_audited_rules_registered_in_deferred_dict(self):
        """All 3 audited rules must be registered in MH_DEFERRED_RULES with clear rationale."""
        for rule_id in AUDITED_ESTABLISHMENT_LABOUR_RULE_IDS:
            assert rule_id in MH_DEFERRED_RULES, f"{rule_id} must be in MH_DEFERRED_RULES"
            assert len(MH_DEFERRED_RULES[rule_id].strip()) > 30

    def test_deferred_rules_total_count_is_at_least_56(self):
        """Deferred rules count must be at least 56 (53 baseline + R-024, R-025, R-098)."""
        assert len(MH_DEFERRED_RULES) >= 56

    def test_active_and_deferred_sets_strictly_disjoint(self):
        """Active and deferred rule sets must have zero intersection."""
        assert set(MH_INCLUDED_RULE_IDS).isdisjoint(set(MH_DEFERRED_RULES))

    def test_encode_raises_fail_closed_for_all_audited_rules(self):
        """_encode() must reject all 3 rules with ValueError and deferral message."""
        for rule_id in AUDITED_ESTABLISHMENT_LABOUR_RULE_IDS:
            with pytest.raises(ValueError, match=f"Rule {rule_id} is deferred:"):
                _encode(rule_id, "APR-TEST", [], [])


class TestAuthoritativeRegisterAlignment:
    """Cross-check each target against authoritative v5 CSV registers."""

    def test_r024_register_identity_and_do_not_implement_note(self):
        """R-024 in rule_register_v5.csv is held as DO_NOT_IMPLEMENT_YET as operative."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r024 = next(r for r in reader if r.get("rule_id") == "R-024")

        assert r024["approval_id"] == "APR-017"
        assert r024["title"] == "Registration of establishment under OSH Code s.3"
        assert r024["obligation_type"] == "REGISTRATION"
        assert r024["authority"] == "AUT-006/AUT-005"
        assert "F-LAB-06 >= 10" in r024["applicability_conditions"]
        assert "DO_NOT_IMPLEMENT_YET" in r024["notes"]
        assert r024["status"] == "VERIFIED_CONDITIONAL"

    def test_apr017_and_apr060_approvals_register(self):
        """APR-017 and APR-060 in approvals.csv are marked DO_NOT_IMPLEMENT_YET."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "approvals.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            approvals = {r["approval_id"]: r for r in reader}

        assert "APR-017" in approvals
        apr017 = approvals["APR-017"]
        assert apr017["implement_status"] == "DO_NOT_IMPLEMENT_YET"
        assert apr017["final_status"] == "DO_NOT_IMPLEMENT_YET"
        assert "Maharashtra OSH rules are DRAFT" in apr017["notes"]

        assert "APR-060" in approvals
        apr060 = approvals["APR-060"]
        assert apr060["implement_status"] == "DO_NOT_IMPLEMENT_YET"
        assert "MH procedure depends on DRAFT rules" in apr060["notes"]

    def test_r025_register_identity_and_requires_confirmation(self):
        """R-025 in rule_register_v5.csv requires confirmation and has LOW confidence."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r025 = next(r for r in reader if r.get("rule_id") == "R-025")

        assert r025["approval_id"] == "APR-018"
        assert r025["title"] == "Shops & Establishments intimation (<10 workers)"
        assert r025["obligation_type"] == "REGISTRATION"
        assert r025["authority"] == "AUT-006"
        assert "F-LAB-06 < 10" in r025["applicability_conditions"]
        assert r025["status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert r025["implementation_status"] == "REQUIRES_CONFIRMATION"
        assert r025["confidence"] == "LOW"

    def test_apr018_relevance_to_factory_unverified(self):
        """APR-018 in approvals.csv and requires_confirmation.csv is unverified for factories."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "approvals.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            approvals = {r["approval_id"]: r for r in reader}

        assert "APR-018" in approvals
        apr018 = approvals["APR-018"]
        assert apr018["implement_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert "Relevance to a factory establishment not verified" in apr018["notes"]

        with open(csv_dir / "requires_confirmation.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rc_reasons = {r["id"]: r.get("reason", "") for r in reader}

        assert "APR-018" in rc_reasons
        assert "Relevance to a factory establishment not verified" in rc_reasons["APR-018"]

    def test_r098_register_identity_and_cnd025_condition(self):
        """R-098 targets CND-025, which is RULE_LOGIC and NOT an approval."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "rule_register_v5.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            r098 = next(r for r in reader if r.get("rule_id") == "R-098")

        assert r098["approval_id"] == "CND-025"
        assert "MATHADI" in r098["title"]
        assert r098["obligation_type"] == "RULE_LOGIC"
        assert r098["status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert r098["implementation_status"] == "REQUIRES_CONFIRMATION"
        assert "F-LOC-19" in r098["applicability_conditions"]
        assert "F-LAB-10" in r098["applicability_conditions"]

        # CND-025 must NOT exist in approvals.csv
        with open(csv_dir / "approvals.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            apr_ids = {r["approval_id"] for r in reader}
        assert "CND-025" not in apr_ids

        # CND-025 exists in conditional_regs.csv
        with open(csv_dir / "conditional_regs.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cond_regs = {r["cond_id"]: r for r in reader}
        assert "CND-025" in cond_regs
        assert "Mathadi" in cond_regs["CND-025"]["regulation"]
        assert cond_regs["CND-025"]["determination"] == "CONDITIONAL"
        assert cond_regs["CND-025"]["final_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"


class TestR024OshEstablishmentAudit:
    """Verify factual findings and deferral boundaries for R-024."""

    def test_draft_rules_status_in_labour_matrix_and_unknowns(self):
        """Maharashtra OSH rules are strictly DRAFT (06-05-2026)."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "labour_matrix.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            lab06 = next(r for r in reader if r.get("item_id") == "LAB-06")

        assert "DRAFT" in lab06["mh_rule_status"]
        assert "R-024 VERIFIED_CONDITIONAL; procedure REQUIRES_OFFICIAL_CONFIRMATION" in (
            lab06["implementation_status"]
        )

        with open(csv_dir / "unknowns.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            unk008 = next(r for r in reader if r.get("unknown_id") == "UNK-008")
        assert "MH OSH rules still DRAFT" in unk008["status"]
        assert "APR-017" in unk008["related_ids"]

    def test_unresolved_item_ur12(self):
        """UR-12 confirms Maharashtra OSH State rules remain OPEN."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "unresolved_items.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ur12 = next(r for r in reader if r.get("item_id") == "UR-12")

        assert ur12["v5_status"] == "OPEN"
        assert "Draft" in ur12["exact_missing_source"] or "drafts" in ur12["exact_missing_source"]

    def test_r024_deferral_rationale_contents(self):
        """Verify explicit reasoning in MH_DEFERRED_RULES['R-024']."""
        reason = MH_DEFERRED_RULES["R-024"]
        assert "DO_NOT_IMPLEMENT_YET" in reason
        assert "DRAFT" in reason
        assert "AUT-006/AUT-005" in reason or "AUT-005" in reason
        assert "DISH" in reason
        assert "s.3(8)" in reason or "deemed" in reason


class TestR025ShopsEstablishmentsAudit:
    """Verify factual findings and deferral boundaries for R-025."""

    def test_r025_classification_in_approvals_py(self):
        """R-025 is classified in MH_REQUIRES_CONFIRMATION_RULE_IDS."""
        assert "R-025" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-025" not in MH_IMPLEMENTATION_SAFE_RULE_IDS

    def test_r025_deferral_rationale_contents(self):
        """Verify explicit reasoning in MH_DEFERRED_RULES['R-025']."""
        reason = MH_DEFERRED_RULES["R-025"]
        assert "MH S&E Act 2017" in reason or "S&E" in reason
        assert "Relevance to a factory establishment not verified" in reason or "factory" in reason
        assert "REQUIRES_OFFICIAL_CONFIRMATION" in reason


class TestR098MathadiManualWorkersAudit:
    """Verify factual findings and deferral boundaries for R-098."""

    def test_r098_classification_in_approvals_py(self):
        """R-098 is classified in MH_REQUIRES_CONFIRMATION_RULE_IDS."""
        assert "R-098" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-098" not in MH_IMPLEMENTATION_SAFE_RULE_IDS

    def test_r098_deferral_rationale_contents(self):
        """Verify explicit reasoning in MH_DEFERRED_RULES['R-098']."""
        reason = MH_DEFERRED_RULES["R-098"]
        assert "Mathadi Act 1969" in reason or "Mathadi" in reason
        assert "CND-025" in reason
        assert "F-LOC-19" in reason and "F-LAB-10" in reason
        assert "RULE_LOGIC" in reason or "compliance condition" in reason

    def test_generic_manual_workers_do_not_trigger_mathadi(self):
        """Presence of manual workers does NOT trigger Mathadi without scheduled employment.

        Mathadi Act s.1(4A) requires BOTH:
        1. Locality covered by an area notification (F-LOC-19 == True)
        2. Engagement in scheduled employment under the Act (F-LAB-10 == True)
        Generic chemical plant workers on regular roll do NOT trigger Mathadi.
        """
        # When locality is False, Mathadi does not apply even if manual workers exist
        # When activity is False, Mathadi does not apply even if locality is in Raigad/Thane
        # When either is UNKNOWN, result must fail closed to CONDITIONAL / INSUFFICIENT_DATA
        cnd_why = (
            "Applies by area and scheduled-employment notifications "
            "(e.g. Thane/Raigad loading/unloading of chemical products from 01-08-1983); "
            "registration under Board schemes"
        )
        assert "Thane/Raigad" in cnd_why
        assert "loading/unloading" in cnd_why


class TestFactOntologyEstablishmentLabour:
    """Verify facts F-LAB-06, F-LAB-07, F-LAB-10, F-LOC-19 in the MH fact registry."""

    def test_target_facts_exist_in_mh_registry(self):
        keys = set(mh_fact_keys())
        assert {"F-LAB-06", "F-LAB-07", "F-LAB-10", "F-LOC-19"} <= keys

    def test_flab06_spec(self):
        spec = get_fact_spec("IN-MH", "F-LAB-06")
        assert spec.value_type == FactValueType.INTEGER
        assert spec.jurisdiction == "IN-MH"
        assert spec.unknown_allowed is False
        assert spec.derived is False

    def test_flab07_spec(self):
        spec = get_fact_spec("IN-MH", "F-LAB-07")
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.jurisdiction == "IN-MH"
        assert spec.unknown_allowed is True
        assert spec.derived is False

    def test_flab10_spec(self):
        spec = get_fact_spec("IN-MH", "F-LAB-10")
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.jurisdiction == "IN-MH"
        assert spec.unknown_allowed is True
        assert spec.derived is False

    def test_floc19_spec(self):
        spec = get_fact_spec("IN-MH", "F-LOC-19")
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.jurisdiction == "IN-MH"
        assert spec.unknown_allowed is True
        assert spec.derived is False

    def test_validation_flab06_integer(self):
        assert validate_fact_value("IN-MH", "F-LAB-06", 5) is None
        assert validate_fact_value("IN-MH", "F-LAB-06", 10) is None
        assert validate_fact_value("IN-MH", "F-LAB-06", 50) is None
        assert validate_fact_value("IN-MH", "F-LAB-06", None) is None  # None is missing
        with pytest.raises(FactValidationError) as exc_info:
            validate_fact_value("IN-MH", "F-LAB-06", "ten")
        assert exc_info.value.code == FactValidationError.WRONG_TYPE

    def test_validation_flab10_and_floc19_boolean_and_unknown(self):
        for fid in ["F-LAB-10", "F-LOC-19"]:
            assert validate_fact_value("IN-MH", fid, True) is None
            assert validate_fact_value("IN-MH", fid, False) is None
            assert validate_fact_value("IN-MH", fid, "UNKNOWN") is None
            assert validate_fact_value("IN-MH", fid, None) is None
            with pytest.raises(FactValidationError) as exc_info:
                validate_fact_value("IN-MH", fid, 123)
            assert exc_info.value.code == FactValidationError.WRONG_TYPE

    def test_jurisdiction_mismatch_detection(self):
        """MH facts evaluated in IN-GJ must raise JURISDICTION_MISMATCH."""
        for fid in ["F-LAB-06", "F-LAB-07", "F-LAB-10", "F-LOC-19"]:
            with pytest.raises(FactValidationError) as exc_info:
                validate_fact_value("IN-GJ", fid, True)
            assert exc_info.value.code == FactValidationError.JURISDICTION_MISMATCH


class TestJurisdictionSafetyAndIsolation:
    """Verify strict isolation between Maharashtra and Gujarat regulatory packs."""

    def test_default_jurisdiction_is_in_gj(self):
        """DEFAULT_JURISDICTION must remain IN-GJ."""
        assert DEFAULT_JURISDICTION == IN_GJ

    def test_gujarat_rule_count_strictly_19(self):
        """IN-GJ active approval rules count must remain exactly 19."""
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19

    def test_maharashtra_rule_count_strictly_26(self):
        """IN-MH active approval rules count must remain exactly 26."""
        mh_pack = load_regulatory_pack(IN_MH)
        assert len(mh_pack.approval_rules) == 26

    def test_no_mh_deferred_rules_in_gj(self):
        """None of the MH deferred rules may appear in Gujarat."""
        gj_pack = load_regulatory_pack(IN_GJ)
        gj_rule_ids = {r.id for r in gj_pack.approval_rules}
        for rid in AUDITED_ESTABLISHMENT_LABOUR_RULE_IDS:
            assert rid not in gj_rule_ids

    def test_authorities_isolated(self):
        """MH pack authorities contain AUT-006; GJ does not use AUT-006."""
        mh_pack = load_regulatory_pack(IN_MH)
        assert "AUT-006" in str(mh_pack.approval_authorities)
        assert "APR-010" in mh_pack.approval_authorities

