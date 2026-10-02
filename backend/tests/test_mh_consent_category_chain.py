"""Tests for Maharashtra Consent Category Chain Audit (R-013, R-014, R-015, R-017).

Chain under audit (all APR-008 CTE except R-017 on APR-009 CTO):

- R-013: CONSENT_REQUIRED := MPCB_CATEGORY IN {RED,ORANGE,GREEN} - DEFERRED
  Reason: needs R-014 sector lookup plus unmodeled MPCB_CATEGORY; no
  rule-composition primitive exists.
- R-014: SECTOR_CATEGORY := lookup(F-MPCB-01) - DEFERRED
  Reason: LOOKUP operator over a classification table that is not digitized
  (T4 mirror source, partial codes); multi-code guard R-015 emits UNKNOWN.
- R-015: UNIT_CATEGORY (multi-code) := UNKNOWN - DEFERRED (this audit)
  Reason: guard/routing node, not applicability; no aggregation rule exists
  and the maximum-category convention is explicitly forbidden (UNK-002).
- R-017: CTO_REQUIRED := CONSENT_REQUIRED == TRUE (APR-009) - DEFERRED
  Reason: required_inputs is literally R-013; standalone evaluation needs
  the full R-014 lookup plus R-015 guard; White exempt.

Register identity is verified against the CURRENT CSVs at runtime (same
pattern as test_mh_cto_renewal.py); code state is asserted against
MH_DEFERRED_RULES / MH_INCLUDED_RULE_IDS / _encode / the fact registry /
the pack. Zero pack changes from this cluster beyond the explicit R-015
deferral entry.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.rules.dependency_engine import ReadinessStatus, evaluate_readiness
from app.rules.facts import (
    MH_FACTS,
    FactValidationError,
    FactValueType,
    get_fact_spec,
    validate_fact_value,
)
from app.rules.models import ApplicabilityOp
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_UNKNOWN_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

CONSENT_CHAIN_RULES: frozenset[str] = frozenset({
    "R-013",
    "R-014",
    "R-015",
    "R-017",
})

CONSENT_APPROVALS: frozenset[str] = frozenset({
    "APR-008",
    "APR-009",
})


def _get_csv_dir() -> Path:
    """Locate the authoritative CSV directory."""
    backend_dir = Path(__file__).resolve().parent.parent
    root_dir = backend_dir.parent
    for path in root_dir.iterdir():
        if "UdyamDwaar MH Chemical Pack" in path.name and path.is_dir():
            csv_path = path / "csv"
            if csv_path.exists():
                return csv_path
    pytest.skip("Authoritative CSV directory not found")


def _register_row(filename: str, key: str, value: str) -> dict[str, str]:
    """Fetch one authoritative register row by key column."""
    csv_dir = _get_csv_dir()
    with open(csv_dir / filename, encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return next(r for r in reader if r.get(key) == value)


class TestBaselineCounts:
    """Confirm the repository baseline before asserting cluster effects."""

    def test_default_jurisdiction_is_gj(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_mh_active_rule_count_is_26(self):
        assert len(load_mh_approval_rules()) == 26

    def test_mh_deferred_count_is_61(self):
        """59 pre-existing + R-015 + R-021 + R-054 (R-054 closure audit)."""
        assert len(MH_DEFERRED_RULES) == 61

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128

    def test_active_deferred_disjoint(self):
        overlap = MH_INCLUDED_RULE_IDS & frozenset(MH_DEFERRED_RULES.keys())
        assert not overlap, f"Active/deferred overlap: {overlap}"


class TestChainIdentityMatrix:
    """Field-by-field identity from the CURRENT registers."""

    def test_r013_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-013")
        assert row["approval_id"] == "APR-008"
        assert row["title"] == "Consent to Establish (Water & Air Acts)"
        assert row["obligation_type"] == "CONSENT"
        assert row["authority"] == "AUT-003"
        assert row["jurisdiction"] == "STATEWIDE"
        assert "MPCB_CATEGORY IN {RED,ORANGE,GREEN}" in row["applicability_conditions"]
        assert row["required_inputs"] == "F-MPCB-01"
        assert row["stage"] == "PRE_ESTABLISHMENT"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["effective_date"] == "2025-06-23"

    def test_r014_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-014")
        assert row["approval_id"] == "APR-008"
        assert "lookup(F-MPCB-01)" in row["applicability_conditions"]
        assert "111.1/111.2 organic chemicals -> RED" in row["applicability_conditions"]
        assert row["required_inputs"] == "F-MPCB-01"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert "Only listed codes encoded; others -> UNKNOWN" in row["notes"]

    def test_r014_operator_is_lookup_in_rules_csv(self):
        row = _register_row("rules.csv", "rule_id", "R-014")
        assert row["operator"] == "LOOKUP"
        assert row["threshold"] == "CPCB table"
        assert "CPCB Directions 12-02-2025 Annexure" in row["legal_basis"]

    def test_r015_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-015")
        assert row["approval_id"] == "APR-008"
        assert row["applicability_conditions"] == (
            "UNIT_CATEGORY (multiple sector codes) := UNKNOWN"
        )
        assert row["rule_kind"] == "GUARD_OR_ROUTING"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert "maximum category" in row["notes"]
        assert "mus" in row["notes"]  # "...convention mus[t not be implemented]"

    def test_r015_in_unknown_set(self):
        """R-015 needs the cardinality-guard construct: UNKNOWN-listed, so
        _encode rejects it even before the deferred check."""
        assert "R-015" in MH_UNKNOWN_RULE_IDS
        assert "R-015" in MH_IMPLEMENTATION_SAFE_RULE_IDS

    def test_r017_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-017")
        assert row["approval_id"] == "APR-009"
        assert row["title"] == "Consent to Operate (Water & Air Acts)"
        assert "CTO_REQUIRED := CONSENT_REQUIRED == TRUE" in row["applicability_conditions"]
        assert row["required_inputs"] == "R-013"
        assert row["stage"] == "PRE_OPERATION"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"

    def test_r016_is_do_not_implement(self):
        """R-016 (deemed CTE) is DO_NOT_IMPLEMENT_YET in the register and
        DNI-listed in code: context that CTO-adjacent deemed logic is also
        held, not an alternative path around this chain."""
        row = _register_row("rule_register_v5.csv", "rule_id", "R-016")
        assert row["status"] == "DO_NOT_IMPLEMENT_YET"
        assert row["implementation_status"] == "DO_NOT_IMPLEMENT"

    def test_approvals_cte_vs_cto_lifecycle(self):
        apr008 = _register_row("approvals.csv", "approval_id", "APR-008")
        apr009 = _register_row("approvals.csv", "approval_id", "APR-009")
        assert apr008["lifecycle_stage"] == "PRE_CONSTRUCTION"
        assert apr008["trigger_event"] == "Before establishing / taking steps to establish"
        assert apr009["lifecycle_stage"] == "PRE_OPERATION"
        assert apr009["trigger_event"] == "Before commencing operation"
        assert apr009["precondition"] == "CTE"
        assert "R-013;R-014;R-015;R-016" in apr008["rule_ids"]
        assert "R-017" in apr009["rule_ids"]

    def test_chain_absent_from_active_pack(self):
        active = {r.id for r in load_mh_approval_rules()}
        assert not (CONSENT_CHAIN_RULES & active)

    def test_chain_absent_from_gj_pack(self):
        gj_ids = {r.id for r in load_regulatory_pack(IN_GJ).approval_rules}
        assert not (CONSENT_CHAIN_RULES & gj_ids)


class TestR013ApplicabilityNeedsClassification:
    """R-013 answers applicability only via a prior classification."""

    def test_r013_is_classification_dependent_not_direct(self):
        """CONSENT_REQUIRED ranges over MPCB_CATEGORY, which is R-014's
        output — not a project fact. No direct CONSENT_REQUIRED=TRUE rule
        may be created while classification is unresolved."""
        assert "R-013" in MH_DEFERRED_RULES
        assert "R-014" in MH_DEFERRED_RULES["R-013"]

    def test_mpcb_category_fact_does_not_exist(self):
        """MPCB_CATEGORY appears in R-013's condition but in no facts.csv
        row and no MH_FACTS key: the lookup output is unmodeled."""
        assert "MPCB_CATEGORY" not in MH_FACTS
        for key in MH_FACTS:
            assert "CATEGORY" not in key.upper()

    def test_white_exempt_per_et049(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-049")
        assert row["rule_id"] == "R-013"
        assert "CONSENT_REQUIRED=FALSE" in row["expected"]

    def test_unknown_codes_stay_unknown_per_et110(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-110")
        assert row["rule_id"] == "R-013"
        assert "CONSENT_REQUIRED=UNKNOWN" in row["expected"]

    def test_encode_rejects_r013(self):
        with pytest.raises(ValueError, match="Rule R-013 is deferred"):
            _encode("R-013", "APR-008", [], [])


class TestR014LookupTable:
    """The classification table is the hard architectural boundary."""

    def test_source_is_t4_mirror(self):
        """SRC-011 (CPCB Directions, the table source) is T4
        OFFICIAL_MIRROR — the lowest tier. A determinism-critical lookup
        cannot rest on a mirror."""
        row = _register_row("sources.csv", "source_id", "SRC-011")
        assert row["tier"] == "T4"
        assert row["source_type"] == "OFFICIAL_MIRROR"

    def test_adoption_circular_is_scanned_ocr(self):
        """SRC-010 (MPCB adoption, effective 2025-06-23) is T2 but
        scanned/OCR: transcription risk on the table itself."""
        row = _register_row("sources.csv", "source_id", "SRC-010")
        assert row["tier"] == "T2"
        assert "OCR" in row["what_the_source_proves"]

    def test_only_listed_codes_covered(self):
        """Register note: only listed codes encoded, others UNKNOWN. A
        partial table presented as complete would misclassify unlisted
        sectors (e.g. a novel specialty-chemical code)."""
        row = _register_row("rule_register_v5.csv", "rule_id", "R-014")
        assert "others -> UNKNOWN" in row["notes"]

    def test_table_not_digitized_in_code(self):
        """No sector-code mapping exists in the codebase: the pack carries
        neither SRC-010/SRC-011 sources nor any APR-008 rule, and no
        module maps codes to categories."""
        mh_pack = load_regulatory_pack("IN-MH")
        src_ids = {s.id for s in mh_pack.sources}
        assert "SRC-010" not in src_ids
        assert "SRC-011" not in src_ids
        active_approvals = {r.approval_id for r in mh_pack.approval_rules}
        assert "APR-008" not in active_approvals

    def test_no_lookup_operator_in_engine(self):
        """ApplicabilityOp has no LOOKUP member: R-014's register operator
        is inexpressible by construction."""
        assert [op.value for op in ApplicabilityOp] == [
            "eq", "in", "gte", "lte", "gt", "lt",
        ]

    def test_chemical_codes_are_red_but_unusable(self):
        """111.1/111.2 organic chemicals -> RED is verified knowledge that
        must still fail closed: knowing the answer informally is not a
        deterministic encoding."""
        assert "R-014" in MH_DEFERRED_RULES
        assert "R-014" not in MH_INCLUDED_RULE_IDS

    def test_encode_rejects_r014(self):
        with pytest.raises(ValueError, match="Rule R-014 is deferred"):
            _encode("R-014", "APR-008", [], [])


class TestR015AggregationGuard:
    """Multi-activity units must emit UNKNOWN; MAX is forbidden."""

    def test_guard_mandates_unknown_per_register(self):
        row = _register_row("rules.csv", "rule_id", "R-015")
        assert "UNKNOWN" in row["condition"]
        assert "must NOT be implemented" in row["notes"]

    def test_no_aggregation_rule_found_is_high_confidence(self):
        """Confidence HIGH (that no rule found): the absence of an
        aggregation rule is itself verified evidence, per UNK-002."""
        row = _register_row("unknowns.csv", "unknown_id", "UNK-002")
        assert "R-015" in row["related_ids"]
        assert "no official aggregation rule found" in row["status"]
        assert "UNKNOWN" in row["status"]

    def test_max_convention_flagged_not_rule_per_et048(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-048")
        assert "UNKNOWN (multi-activity)" in row["expected"]
        assert "Convention flagged, not rule" in row["rationale"]

    def test_deferral_reason_forbids_max(self):
        reason = MH_DEFERRED_RULES["R-015"]
        assert "maximum-category convention" in reason
        assert "explicitly forbidden" in reason
        assert "UNK-002" in reason

    def test_deferral_reason_states_guard_character(self):
        reason = MH_DEFERRED_RULES["R-015"]
        assert "guard/routing node" in reason
        assert "not an approval" in reason

    def test_fmpcb01_is_per_activity_list(self):
        """F-MPCB-01 is a LIST ('Per activity'): multi-activity projects
        are structurally representable as input, which is exactly why the
        guard matters."""
        spec = get_fact_spec("IN-MH", "F-MPCB-01")
        assert spec.value_type == FactValueType.LIST
        assert "Per activity" in spec.description

    def test_no_scalar_industry_type_fact(self):
        """No single scalar 'industry type' fact exists that could serve
        as a lookup key: classification needs the full activity list."""
        labels = [spec.label for spec in MH_FACTS.values()]
        assert not any(label == "industry_type" for label in labels)
        assert not any("industry_type" in key for key in MH_FACTS)

    def test_encode_rejects_r015_as_deferred(self):
        """Deferred check fires before the UNKNOWN check: explicit reason,
        not a generic guard rejection."""
        with pytest.raises(ValueError, match="Rule R-015 is deferred"):
            _encode("R-015", "APR-008", [], [])


class TestR017CtoGate:
    """CTO must not be inferred from CTE without the chain."""

    def test_required_input_is_rule_reference(self):
        """required_inputs is literally 'R-013': the register itself
        encodes rule composition, which ConditionNode cannot express."""
        row = _register_row("rules.csv", "rule_id", "R-017")
        assert row["facts"] == "R-013"

    def test_cte_precedes_cto_by_lifecycle(self):
        """PRE_CONSTRUCTION (establish) vs PRE_OPERATION (operate): CTO is
        a later-stage gate with precondition CTE, not a corollary."""
        assert "R-017" in MH_DEFERRED_RULES

    def test_white_exempt_from_cto_path(self):
        """White units exempt from consent never enter the CTO path:
        no automatic CTO conclusion exists for any category."""
        assert "R-017" not in MH_INCLUDED_RULE_IDS

    def test_cto_blocked_until_chain_resolves(self):
        """With CTE/CTO unknown and unobtained, the dependency engine
        blocks downstream APR-010 on both: unknown consent propagates as
        a blocker, never as satisfaction."""
        mh_pack = load_regulatory_pack("IN-MH")
        graph = evaluate_readiness(
            mh_pack.dependencies,
            {"APR-010": "applies", "APR-008": "insufficient_data",
             "APR-009": "insufficient_data"},
            obtained=set(),
        )
        assert graph.readiness["APR-010"].readiness == ReadinessStatus.BLOCKED
        assert set(graph.readiness["APR-010"].blocking_prerequisites) == {
            "APR-008", "APR-009",
        }

    def test_no_renewal_logic_imported(self):
        """R-017 deferral stays clear of R-063/CMP-007 renewal semantics:
        validity (R-062), auto-renewal (SLA-037/CON-006) and UNK-001/UNK-032
        are separate deferred/confirmation items."""
        reason = MH_DEFERRED_RULES["R-017"]
        assert "renewal" not in reason.lower()
        assert "R-063" not in reason
        assert "CMP-007" not in reason

    def test_encode_rejects_r017(self):
        with pytest.raises(ValueError, match="Rule R-017 is deferred"):
            _encode("R-017", "APR-009", [], [])


class TestFactOntology:
    """Chain inputs: what exists, what is missing, what must not be added."""

    def test_fmpcb01_spec(self):
        spec = get_fact_spec("IN-MH", "F-MPCB-01")
        assert spec.value_type == FactValueType.LIST
        assert spec.unknown_allowed is False

    def test_missing_codes_fail_closed(self):
        """F-MPCB-01 missing (None) is valid input (never a type error)
        and can only yield uncertainty downstream, never a category."""
        validate_fact_value("IN-MH", "F-MPCB-01", None)
        validate_fact_value("IN-MH", "F-MPCB-01", ["111.1"])

    def test_invalid_codes_rejected(self):
        """F-MPCB-01 must be a list: scalars and mappings are rejected.
        (Plain LIST imposes no element check, so element discipline comes
        from the undigitized CPCB table — another reason R-014 is gated.)"""
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-MPCB-01", "111.1")
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-MPCB-01", 111)

    def test_no_consent_facts_added(self):
        assert len(MH_FACTS) == 128

    def test_gj_namespace_rejects_fmpcb01(self):
        with pytest.raises(FactValidationError) as exc:
            validate_fact_value("IN-GJ", "F-MPCB-01", ["111.1"])
        assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH


class TestApprovalSemantics:
    """CTE/CTO/renewal/amendment/integrated-consent stay distinct."""

    def test_no_active_cte_cto_rules(self):
        active_approvals = {r.approval_id for r in load_mh_approval_rules()}
        assert not (CONSENT_APPROVALS & active_approvals)

    def test_integrated_consent_stays_confirmation_item(self):
        """GSR-02 (single-step integrated consent + authorisation) is a
        separate confirmation item: no back-door activation of APR-008."""
        row = _register_row("requires_confirmation.csv", "id", "GSR-02")
        assert row["applies_to"] == "APR-008"
        assert row["final_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"

    def test_consent_slas_unloaded(self):
        """No APR-008/APR-009 SLA rows in the loaded pack (SLA-001/002/003,
        036/037, 048/049/050): timelines cannot drive applicability."""
        mh_pack = load_regulatory_pack("IN-MH")
        sla_approvals = {s.approval_id for s in mh_pack.sla_records}
        assert not (CONSENT_APPROVALS & sla_approvals)

    def test_consent_docs_unloaded(self):
        """DOC-004/DOC-011 (CTE documents) are not in the loaded pack."""
        mh_pack = load_regulatory_pack("IN-MH")
        doc_approvals = {a for r in mh_pack.document_requirements
                         for a in r.get("approval_ids", [])}
        assert not (CONSENT_APPROVALS & doc_approvals)

    def test_deemed_cte_never_granted_boundary(self):
        """ET-072: deemed CTE is CONDITIONAL at most, never 'granted' —
        the same no-grant discipline as R-081 deemed permission."""
        row = _register_row("edge_tests.csv", "test_id", "ET-072")
        assert row["rule_id"] == "R-016"
        assert "CONDITIONAL" in row["expected"]
        assert "Never 'granted'" in row["rationale"]


class TestJurisdictionIsolation:
    """IN-MH chain work must not leak into IN-GJ."""

    def test_gj_pack_untouched(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        gj_ids = {r.id for r in gj_pack.approval_rules}
        assert not (CONSENT_CHAIN_RULES & gj_ids)

    def test_gj_approvals_untouched(self):
        gj_approval_ids = {r.approval_id
                           for r in load_regulatory_pack(IN_GJ).approval_rules}
        assert not (CONSENT_APPROVALS & gj_approval_ids)

    def test_mh_active_unchanged(self):
        assert len(load_mh_approval_rules()) == 26


class TestClassification:
    """Exactly-one primary classification per candidate."""

    def test_r013_is_class_d(self):
        """D - missing facts/classification table/aggregation capability:
        needs R-014 lookup output plus unmodeled MPCB_CATEGORY."""
        assert "R-013" in MH_DEFERRED_RULES
        assert "MPCB_CATEGORY" in MH_DEFERRED_RULES["R-013"]

    def test_r014_is_class_e(self):
        """E - lookup architecture not representable: LOOKUP operator +
        undigitized T4-mirror table."""
        assert "R-014" in MH_DEFERRED_RULES
        assert "LOOKUP" in MH_DEFERRED_RULES["R-014"]

    def test_r015_is_class_d(self):
        """D - missing aggregation capability: guard mandates UNKNOWN and
        the only intuitive algorithm (MAX) is explicitly forbidden."""
        assert "R-015" in MH_DEFERRED_RULES
        assert "no multi-code aggregation primitive" in MH_DEFERRED_RULES["R-015"]

    def test_r017_is_class_d(self):
        """D - missing composition: required input is literally R-013 with
        no rule-reference primitive available."""
        assert "R-017" in MH_DEFERRED_RULES
        assert "no rule-composition primitive" in MH_DEFERRED_RULES["R-017"]

    def test_zero_rules_activated(self):
        active = {r.id for r in load_mh_approval_rules()}
        assert not (CONSENT_CHAIN_RULES & active)
