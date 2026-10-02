"""Tests for Maharashtra Environmental Protection & Extended Producer Responsibility (EPR) Pack.

This suite performs the authoritative audit and verification for:
1. Plastic Waste Management Rules / EPR (EPR-PWM, EPRS-01, EPRS-02, EPRS-13, CND-023, SRC-159):
   Classified as OPERATING_DUTY / REGISTRATION in OPERATION stage, NOT an industrial approval.
   Canonical chemical manufacturing project alone never triggers EPR without specific role facts;
   missing role facts fail closed to INSUFFICIENT_DATA per ET-v5-18. Kept out of approval graph.
2. Battery Waste Management Rules 2022 (EPR-BAT, EPRS-03, EPRS-04, EPRS-13, CND-023, SRC-161):
   Classified as OPERATING_DUTY / REGISTRATION (PRE_OPERATION / RENEWAL), NOT an approval.
   Chemical units using batteries internally are consumers, not statutory producers (r.3(1)(n)).
   Role UNKNOWN evaluates to UNKNOWN per ET-v4-17 / INSUFFICIENT_DATA per ET-v5-18.
3. E-Waste (Management) Rules 2022 (EPR-EWASTE, EPRS-05, EPRS-06, R-094 / CMP-025, SRC-135):
   Distinguishes bulk consumer duty (Rule 8, handover if F-EEE-01 >= 1000, already actively
   encoded in R-094 targeting CMP-025) from EEE Producer EPR registration (EPRS-06).
4. Hazardous Waste Import / Export (HOWM Rules 2016 r.11-15, Schedules III/IV/VI, SRC-013):
   Step H5 in howm_decision_path.csv; transboundary movement requires MoEFCC Form 5 permission.
   No import/export trade facts exist in fact registry; fails closed (UNKNOWN / INSUFFICIENT_DATA).
5. Environmental Statement / Form V (CMP-005, EP Rules 1986 r.14, SRC-065):
   Annual operational compliance return (RETURN in OPERATION stage, due 30 Sept to MPCB AUT-003).
   NOT an industrial approval; belongs strictly to compliance / deadline workflow layer.
6. Additional environmental/EPR regimes audited:
   - EPR-OIL: Used oil EPR under HOWM Second Amendment 2023 (SRC-162, SRC-184).
   - EPR-TYRE: Waste tyre EPR under HOWM Schedule IX (SRC-182, SRC-163).
   - EPR-NFM / CND-005: Non-ferrous scrap EPR under HOWM G.S.R. 438(E) (SRC-014, SRC-183).
   - EBWGR-SWM: Extended Bulk Waste Generator Responsibility under Solid Waste Rules (SRC-160).
   - SWM-RDF: Solid-fuel substitution by RDF/SCF under Solid Waste Rules 2026 r.11 (SRC-160).
   - R-072 / CMP-014: Environment Audit under Environment Audit Rules 2025 (SRC-066).

Active MH rules remain strictly 26 (R-094 already active).
Active GJ rules remain strictly 19.
Deferred MH rules remain strictly 50.
Default jurisdiction remains strictly IN-GJ.
Zero new active rules added.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.rules.applicability import evaluate_rule
from app.rules.facts import (
    FactValidationError,
    FactValueType,
    get_fact_spec,
    is_unknown_value,
    validate_fact_value,
)
from app.rules.models import ApprovalResult
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, IN_MH, load_regulatory_pack

CSV_DIR = (
    Path(__file__).resolve().parents[2]
    / "UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)"
    / "csv"
)


def _read_csv(filename: str) -> list[dict[str, str]]:
    path = CSV_DIR / filename
    assert path.exists(), f"Missing CSV: {path}"
    with open(path, encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


class TestEnvironmentalEprCandidateIdentity:
    """Verify exact candidate identities, registers, and legal instruments."""

    def test_epr_regimes_inventory(self):
        """All 9 EPR regimes from epr_regimes.csv are present with exact IDs and instruments."""
        rows = _read_csv("epr_regimes.csv")
        regime_ids = {r["regime_id"] for r in rows}
        expected_ids = {
            "EPR-PWM", "EPR-BAT", "EPR-OIL", "EPR-TYRE", "EPR-EWASTE",
            "EBWGR-SWM", "SWM-RDF", "EPR-OTHER", "EPR-NFM",
        }
        assert expected_ids.issubset(regime_ids)

        pwm = next(r for r in rows if r["regime_id"] == "EPR-PWM")
        assert "PWM Rules 2016" in pwm["current_instrument"]
        assert "SRC-159" in pwm["source_ids"]
        assert pwm["final_status"] == "VERIFIED_CONDITIONAL"

        bat = next(r for r in rows if r["regime_id"] == "EPR-BAT")
        assert "Battery Waste Management Rules 2022" in bat["current_instrument"]
        assert "SRC-161" in bat["source_ids"]
        assert "SRC-181" in bat["source_ids"]

        ewaste = next(r for r in rows if r["regime_id"] == "EPR-EWASTE")
        assert "E-Waste (Management) Rules 2022" in ewaste["current_instrument"]
        assert "1000 units" in ewaste["threshold"]
        assert ewaste["final_status"] == "VERIFIED_CONDITIONAL"

    def test_epr_role_screening_inventory(self):
        """Verify role screening rows EPRS-01 through EPRS-13 from epr_role_screening.csv."""
        rows = _read_csv("epr_role_screening.csv")
        screen_ids = {r["screen_id"] for r in rows}
        for i in range(1, 14):
            assert f"EPRS-{i:02d}" in screen_ids

        eprs13 = next(r for r in rows if r["screen_id"] == "EPRS-13")
        assert eprs13["regime"] == "ALL"
        assert "synthetic organic chemical manufacturer" in eprs13["role_required"]
        assert "INSUFFICIENT_DATA" in eprs13["applicability"]
        assert "chemical manufacturing alone never triggers EPR" in eprs13["applicability"]

    def test_environmental_statement_form_v_identity(self):
        """Verify CMP-005 in compliance.csv: EP Rules 1986 r.14, due 30 Sept, MPCB AUT-003."""
        rows = _read_csv("compliance.csv")
        cmp005 = next((r for r in rows if r["compliance_id"] == "CMP-005"), None)
        assert cmp005 is not None
        assert "Environmental Statement Form V" in cmp005["obligation"]
        assert "EP Rules 1986 r.14" in cmp005["legal_basis"]
        assert "30 September" in cmp005["frequency_deadline"]
        assert cmp005["authority_id"] == "AUT-003"
        assert cmp005["record_type"] == "RETURN"
        assert cmp005["lifecycle_stage"] == "OPERATION"
        assert cmp005["implement_status"] == "SAFE"
        assert cmp005["final_status"] == "VERIFIED_CONDITIONAL"

    def test_hazardous_waste_howm_decision_path_step_h5(self):
        """Verify howm_decision_path.csv step H5 for Schedule III/IV import/export."""
        rows = _read_csv("howm_decision_path.csv")
        h5 = next((r for r in rows if r["step"] == "H5"), None)
        assert h5 is not None
        assert "Schedule III/IV (import-export / recyclables) relevance" in h5["question"]
        assert "trade facts" in h5["inputs"]
        assert "UNKNOWN" in h5["if_insufficient"]
        assert h5["source_id"] == "SRC-013"

    def test_active_bulk_ewaste_rule_r094_identity(self):
        """Verify R-094 is actively loaded in MH pack targeting CMP-025."""
        rules = load_mh_approval_rules()
        r094 = next((r for r in rules if r.id == "R-094"), None)
        assert r094 is not None
        assert r094.approval_id == "CMP-025"
        assert "SRC-135" in [ref.source_id for ref in r094.source_refs]

    def test_environment_audit_r072_and_cmp014_identity(self):
        """Verify R-072 / CMP-014 under Environment Audit Rules 2025 S.O. 3973(E)."""
        rule_rows = _read_csv("rule_register_v5.csv")
        r072 = next((r for r in rule_rows if r["rule_id"] == "R-072"), None)
        assert r072 is not None
        assert r072["approval_id"] == "CMP-014"
        assert "ENV_AUDIT" in r072["title"]
        assert r072["source_id"] == "SRC-066"

        comp_rows = _read_csv("compliance.csv")
        cmp014 = next((r for r in comp_rows if r["compliance_id"] == "CMP-014"), None)
        assert cmp014 is not None
        assert cmp014["implement_status"] == "DO_NOT_IMPLEMENT_YET"
        assert cmp014["record_type"] == "AUDIT"
        assert cmp014["lifecycle_stage"] == "OPERATION"


class TestApprovalVsComplianceClassification:
    """Verify strict separation between approvals and compliance obligations / registrations."""

    def test_epr_regimes_are_not_approvals(self):
        """None of the EPR regimes exists as an APR-xxx industrial approval in approvals.csv."""
        rows = _read_csv("approvals.csv")
        approval_ids = {r["approval_id"] for r in rows}
        for apr in ["APR-EPR", "APR-PWM", "APR-BAT", "APR-OIL", "APR-TYRE"]:
            assert apr not in approval_ids

        for r in rows:
            assert "Extended Producer Responsibility" not in r.get("title", "")
            assert "Plastic Waste EPR" not in r.get("title", "")
            assert "Battery Waste EPR" not in r.get("title", "")

    def test_form_v_is_compliance_return_not_approval(self):
        """Form V Environmental Statement (CMP-005) is an operational return, not an approval."""
        comp_rows = _read_csv("compliance.csv")
        cmp005 = next(r for r in comp_rows if r["compliance_id"] == "CMP-005")
        assert cmp005["record_type"] == "RETURN"
        assert cmp005["lifecycle_stage"] == "OPERATION"

        apr_rows = _read_csv("approvals.csv")
        apr_ids = {r["approval_id"] for r in apr_rows}
        assert "CMP-005" not in apr_ids
        for r in apr_rows:
            assert "Form V" not in r.get("title", "")
            assert "Environmental Statement" not in r.get("title", "")

    def test_epr_role_screening_record_classes(self):
        """All role screening records are OPERATING_DUTY / REGISTRATION, not project approvals."""
        rows = _read_csv("epr_role_screening.csv")
        for r in rows:
            assert "OPERATING_DUTY" in r["record_class"] or "REGISTRATION" in r["record_class"]
            assert "not a project-stage approval" in r["record_class"]

    def test_conditional_regs_classification(self):
        """CND-005 and CND-023 in conditional_regs.csv are conditional regulations."""
        rows = _read_csv("conditional_regs.csv")
        cnd005 = next(r for r in rows if r["cond_id"] == "CND-005")
        assert "HOWM EPR" in cnd005["regulation"]
        assert cnd005["determination"] == "CONDITIONAL"

        cnd023 = next(r for r in rows if r["cond_id"] == "CND-023")
        assert "Plastic / Battery / E-waste EPR registrations" in cnd023["regulation"]
        assert cnd023["determination"] == "CONDITIONAL"
        assert "F-OTH-05" in cnd023["deciding_facts"]


class TestAuthorityAndSourceMapping:
    """Verify competent authorities, administrative portals, and authoritative legal sources."""

    def test_epr_authorities_and_portals(self):
        """Verify CPCB centralized portals vs SPCB state roles across EPR regimes."""
        rows = _read_csv("epr_regimes.csv")
        pwm = next(r for r in rows if r["regime_id"] == "EPR-PWM")
        assert "CPCB" in pwm["authority"]
        assert "portal" in pwm["portal"].lower() or "cpcb" in pwm["portal"].lower()

        bat = next(r for r in rows if r["regime_id"] == "EPR-BAT")
        assert "CPCB" in bat["authority"]
        assert "eprbatterycpcb.in" in bat["portal"]

        oil = next(r for r in rows if r["regime_id"] == "EPR-OIL")
        assert "CPCB" in oil["authority"]
        assert "eprusedoil.cpcb.gov.in" in oil["portal"]

        tyre = next(r for r in rows if r["regime_id"] == "EPR-TYRE")
        assert "CPCB" in tyre["authority"]
        assert "eprtyres.cpcb.gov.in" in tyre["portal"]

    def test_form_v_authority_is_mpcb(self):
        """Form V Environmental Statement is submitted to MPCB (AUT-003)."""
        rows = _read_csv("compliance.csv")
        cmp005 = next(r for r in rows if r["compliance_id"] == "CMP-005")
        assert cmp005["authority_id"] == "AUT-003"

    def test_hw_import_export_authority_is_moefcc(self):
        """Transboundary movement under HOWM Chapter III is administered by MoEFCC and Customs."""
        path_rows = _read_csv("howm_decision_path.csv")
        h5 = next(r for r in path_rows if r["step"] == "H5")
        assert "Schedules III-VI" in h5["locator"]
        assert h5["source_id"] == "SRC-013"

    def test_source_corpus_and_evidence_tiers(self):
        """Verify source IDs, issuing authorities, publication dates, and trust tiers."""
        rows = _read_csv("sources.csv")
        sources_by_id = {r["source_id"]: r for r in rows}

        src013 = sources_by_id["SRC-013"]
        assert src013["tier"] == "T1"
        assert "Hazardous and Other Wastes" in src013["title"]
        assert "2016-04-04" in src013["effective_date"]

        src014 = sources_by_id["SRC-014"]
        assert src014["tier"] == "T1"
        assert "G.S.R. 438(E)" in src014["title"]

        src065 = sources_by_id["SRC-065"]
        assert src065["tier"] == "T4"
        assert "Environment (Protection) Rules 1986" in src065["title"]
        assert "Form V" in src065["title"]

        src066 = sources_by_id["SRC-066"]
        assert src066["tier"] == "T1"
        assert "Environment Audit Rules 2025" in src066["title"]

        src120 = sources_by_id["SRC-120"]
        assert src120["tier"] == "T2"
        assert "Schedule II" in src120["title"]

        src135 = sources_by_id["SRC-135"]
        assert src135["tier"] == "T1"
        assert "E-Waste (Management) Rules 2022" in src135["title"]

        src159 = sources_by_id["SRC-159"]
        assert src159["tier"] == "T1"
        assert "Plastic Waste Management (Amendment) Rules 2026" in src159["title"]
        assert "G.S.R. 237(E)" in src159["title"]

        src160 = sources_by_id["SRC-160"]
        assert src160["tier"] == "T1"
        assert "Solid Waste Management Rules 2026" in src160["title"]
        assert "S.O. 388(E)" in src160["title"]

        src181 = sources_by_id["SRC-181"]
        assert src181["tier"] == "T1"
        assert "Battery Waste Management (Amendment) Rules 2025" in src181["title"]

        src182 = sources_by_id["SRC-182"]
        assert src182["tier"] == "T1"
        assert "Schedule IX" in src182["title"]

        src183 = sources_by_id["SRC-183"]
        assert src183["tier"] == "T1"
        assert "non-ferrous metals" in src183["title"]


class TestFactRegistryAndUnknownSemantics:
    """Verify fact registry coverage, typing, allowed values, and UNKNOWN propagation."""

    def test_epr_and_waste_facts_in_registry(self):
        """Verify F-OTH-05, F-EEE-01, F-HW-01..F-HW-04 exist in IN-MH registry."""
        spec_oth05 = get_fact_spec(IN_MH, "F-OTH-05")
        assert spec_oth05.value_type == FactValueType.ENUM_SET
        assert spec_oth05.allowed_values == ("PIBO", "BATTERY", "EWASTE", "NONE", "UNKNOWN")

        spec_eee01 = get_fact_spec(IN_MH, "F-EEE-01")
        assert spec_eee01.value_type == FactValueType.NUMBER
        assert spec_eee01.unit == "units"

        spec_hw01 = get_fact_spec(IN_MH, "F-HW-01")
        assert spec_hw01.value_type == FactValueType.BOOLEAN

        spec_hw02 = get_fact_spec(IN_MH, "F-HW-02")
        assert spec_hw02.value_type == FactValueType.LIST

        spec_hw03 = get_fact_spec(IN_MH, "F-HW-03")
        assert spec_hw03.value_type == FactValueType.BOOLEAN

        spec_hw04 = get_fact_spec(IN_MH, "F-HW-04")
        assert spec_hw04.value_type == FactValueType.LIST

    def test_f_oth_05_validation(self):
        """Validate F-OTH-05 with valid enum set and invalid values."""
        validate_fact_value(IN_MH, "F-OTH-05", ["PIBO"])
        validate_fact_value(IN_MH, "F-OTH-05", ["BATTERY", "EWASTE"])
        validate_fact_value(IN_MH, "F-OTH-05", ["NONE"])
        validate_fact_value(IN_MH, "F-OTH-05", None)

        with pytest.raises(FactValidationError):
            validate_fact_value(IN_MH, "F-OTH-05", ["INVALID_ROLE"])

    def test_f_eee_01_validation(self):
        """Validate F-EEE-01 with numbers and invalid types."""
        validate_fact_value(IN_MH, "F-EEE-01", 1000)
        validate_fact_value(IN_MH, "F-EEE-01", 0)
        validate_fact_value(IN_MH, "F-EEE-01", None)

        with pytest.raises(FactValidationError):
            validate_fact_value(IN_MH, "F-EEE-01", "one_thousand")

        with pytest.raises(FactValidationError):
            validate_fact_value(IN_MH, "F-EEE-01", True)

    def test_no_speculative_facts_in_registry(self):
        """Non-existent facts like imports_hazardous_waste raise FactValidationError."""
        speculative_facts = [
            "imports_hazardous_waste",
            "exports_hazardous_waste",
            "plastic_packaging_tpa",
            "battery_producer_flag",
            "F-EPR-01",
            "F-HW-05",
        ]
        for fact_key in speculative_facts:
            with pytest.raises(FactValidationError) as exc_info:
                get_fact_spec(IN_MH, fact_key)
            assert exc_info.value.code == FactValidationError.UNKNOWN_FIELD

    def test_unknown_semantics_not_coerced_to_false(self):
        """None and permitted UNKNOWN token are recognized as unknown, never false."""
        spec_oth05 = get_fact_spec(IN_MH, "F-OTH-05")
        assert is_unknown_value(spec_oth05, None) is True
        assert is_unknown_value(spec_oth05, ["PIBO"]) is False

        spec_eee01 = get_fact_spec(IN_MH, "F-EEE-01")
        assert is_unknown_value(spec_eee01, None) is True
        assert is_unknown_value(spec_eee01, 1000) is False


class TestDomainApplicabilityAndBoundaries:
    """Verify domain applicability, non-applicability boundaries, and fail-closed logic."""

    def test_chemical_manufacturer_alone_never_triggers_epr(self):
        """Chemical manufacturing without PIBO/producer facts evaluates to INSUFFICIENT_DATA."""
        edge_rows = _read_csv("edge_tests.csv")
        et_v5_18 = next((r for r in edge_rows if r["test_id"] == "ET-v5-18"), None)
        assert et_v5_18 is not None
        assert "chemical manufacturer, no role facts" in et_v5_18["inputs"]
        assert "INSUFFICIENT_DATA" in et_v5_18["expected"]
        assert "never APPLIES" in et_v5_18["expected"]

    def test_battery_role_unknown_produces_unknown(self):
        """Battery producer role unknown evaluates to UNKNOWN per ET-v4-17."""
        edge_rows = _read_csv("edge_tests.csv")
        et_v4_17 = next((r for r in edge_rows if r["test_id"] == "ET-v4-17"), None)
        assert et_v4_17 is not None
        assert "battery producer role UNKNOWN" in et_v4_17["inputs"]
        assert et_v4_17["expected"] == "UNKNOWN"

    def test_bulk_ewaste_handover_r094_evaluations(self):
        """Verify R-094 threshold and three-valued logic."""
        rules = load_mh_approval_rules()
        r094 = next(r for r in rules if r.id == "R-094")

        res_applies = evaluate_rule(r094, {"F-EEE-01": 1000})
        assert res_applies.result == ApprovalResult.APPLIES

        res_applies_more = evaluate_rule(r094, {"F-EEE-01": 2500})
        assert res_applies_more.result == ApprovalResult.APPLIES

        res_does_not_apply = evaluate_rule(r094, {"F-EEE-01": 999})
        assert res_does_not_apply.result == ApprovalResult.DOES_NOT_APPLY

        res_zero = evaluate_rule(r094, {"F-EEE-01": 0})
        assert res_zero.result == ApprovalResult.DOES_NOT_APPLY

        res_unknown = evaluate_rule(r094, {})
        assert res_unknown.result == ApprovalResult.INSUFFICIENT_DATA

    def test_hazardous_waste_on_site_rules_boundaries(self):
        """Verify on-site HW rules R-018 and R-096 evaluate deterministically."""
        rules = load_mh_approval_rules()
        r018 = next(r for r in rules if r.id == "R-018")
        r096 = next(r for r in rules if r.id == "R-096")

        assert evaluate_rule(r018, {"F-HW-01": True}).result == ApprovalResult.APPLIES
        assert evaluate_rule(r018, {"F-HW-01": False}).result == ApprovalResult.DOES_NOT_APPLY
        assert evaluate_rule(r018, {}).result == ApprovalResult.INSUFFICIENT_DATA

        assert evaluate_rule(r096, {"F-HW-04": ["CLASS_A_TCLP"]}).result == ApprovalResult.APPLIES
        assert (
            evaluate_rule(r096, {"F-HW-04": ["NON_HAZARDOUS"]}).result
            == ApprovalResult.DOES_NOT_APPLY
        )
        assert evaluate_rule(r096, {}).result == ApprovalResult.INSUFFICIENT_DATA

    def test_hazardous_waste_import_export_is_unmodeled_and_fails_closed(self):
        """Transboundary HW movement has no approval rule and must not be guessed."""
        assert "APR-010" in {r.approval_id for r in load_mh_approval_rules()}
        assert "APR-054" in {r.approval_id for r in load_mh_approval_rules()}
        for r in load_mh_approval_rules():
            assert "import" not in r.id.lower()
            assert "export" not in r.id.lower()


class TestJurisdictionIsolationAndSafety:
    """Verify strict jurisdiction isolation, baseline counts, and safety invariants."""

    def test_default_jurisdiction_is_in_gj(self):
        """DEFAULT_JURISDICTION must remain IN-GJ."""
        assert DEFAULT_JURISDICTION == IN_GJ
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_active_rule_counts(self):
        """Active rule counts must remain strictly 26 for IN-MH and 19 for IN-GJ."""
        mh_rules = load_mh_approval_rules()
        assert len(mh_rules) == 26
        assert len(MH_INCLUDED_RULE_IDS) == 26

        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19

    def test_deferred_mh_rules_count_remains_50(self):
        """Deferred MH rules must be at least 50 (50 baseline from EPR cluster)."""
        assert len(MH_DEFERRED_RULES) >= 50

    def test_active_and_deferred_sets_strictly_disjoint(self):
        """Active and deferred rule sets must have zero overlap."""
        assert set(MH_INCLUDED_RULE_IDS).isdisjoint(set(MH_DEFERRED_RULES))

    def test_zero_new_active_rules_in_this_cluster(self):
        """Zero new active rules were activated in this cluster audit."""
        active_ids = {r.id for r in load_mh_approval_rules()}
        expected_active_26 = {
            "R-002", "R-007", "R-009", "R-011", "R-012", "R-018", "R-026",
            "R-028", "R-030", "R-035", "R-043", "R-044", "R-046", "R-056",
            "R-067", "R-070", "R-089", "R-093", "R-094", "R-073", "R-086",
            "R-087", "R-077", "R-083", "R-084", "R-096",
        }
        assert active_ids == expected_active_26

    def test_jurisdiction_mismatch_guards(self):
        """MH facts rejected in IN-GJ; GJ facts rejected in IN-MH."""
        with pytest.raises(FactValidationError) as exc_mh_in_gj:
            get_fact_spec(IN_GJ, "F-OTH-05")
        assert exc_mh_in_gj.value.code == FactValidationError.JURISDICTION_MISMATCH

        with pytest.raises(FactValidationError) as exc_gj_in_mh:
            get_fact_spec(IN_MH, "plot_area_sqm")
        assert exc_gj_in_mh.value.code == FactValidationError.JURISDICTION_MISMATCH
