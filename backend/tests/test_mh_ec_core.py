"""Tests for Maharashtra EC Core Audit (R-001, R-064, R-074).

Cluster under audit (all APR-001 Prior EC, item 5(f)):

- R-001: EC_5F_REQUIRED := F-PRD-01 == TRUE AND F-PRD-03 IN
  {SYNTHESIS,MIXED} - DEFERRED. Reason: the register note forbids
  auto-FALSE on FORMULATION_ONLY (must stay UNKNOWN pending appraisal
  view); a naive boolean encoding fails OPEN on formulation-only
  projects. Proven below via engine semantics without encoding it.
- R-064: EC_5F_SCOPE product-membership predicate - DEFERRED. Reason:
  the condition cell is truncated mid-token in the register itself and
  UNK-033 (non-drug blending/formulation scope) is OPEN; the register
  operator is `scope`, which no ConditionNode supports.
- R-074: EC_5F_AND_8A combination guard - confirmation-gated + UNKNOWN.
  Reason: UNK-010/UR-06 (no authoritative 5(f)+8(a) statement) and
  cross-rule composition over R-001/R-007 outputs, which the engine
  cannot reference.
- Context R-002 (SMALL_UNIT, active): the only live APR-001 facet. Its
  rule-level behavior is correct, but at approval level a complete,
  not-small fact set aggregates to DOES_NOT_APPLY - i.e. the system
  reports "EC does not apply" for the textbook Category-A project.
  Pinned here as a documented defect; no status change is made.

Register identity is verified against the CURRENT CSVs at runtime (same
pattern as test_mh_consent_category_chain.py). Zero pack/engine/fact
changes from this audit.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pytest

from app.rules.applicability import (
    evaluate_approval_applicability,
    evaluate_rule,
    summarize_by_approval,
)
from app.rules.facts import MH_FACTS, MH_JURISDICTION, get_fact_spec
from app.rules.models import ApplicabilityCondition, ApprovalRule, SourceRef
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    MH_UNKNOWN_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.pack import (
    DEFAULT_JURISDICTION,
    IN_GJ,
    IN_MH,
    load_regulatory_pack,
)

EC_CORE_RULES: frozenset[str] = frozenset({"R-001", "R-064", "R-074"})
EC_APPROVAL = "APR-001"


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


def _apr001_rules() -> list:
    return [
        r for r in load_mh_approval_rules() if r.approval_id == EC_APPROVAL
    ]


class TestBaselineCounts:
    """Confirm the repository baseline before asserting cluster effects."""

    def test_default_jurisdiction_is_gj(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_mh_active_rule_count_is_26(self):
        assert len(load_mh_approval_rules()) == 26

    def test_mh_deferred_count_is_61(self):
        # 59 at EC-audit time + R-021 (parallel MSIHC session) + R-054
        # (follow-up implementing that audit's recommendation).
        assert len(MH_DEFERRED_RULES) == 61

    def test_mh_confirmation_count_is_26(self):
        assert len(MH_REQUIRES_CONFIRMATION_RULE_IDS) == 26

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128

    def test_active_deferred_disjoint(self):
        overlap = MH_INCLUDED_RULE_IDS & frozenset(MH_DEFERRED_RULES.keys())
        assert not overlap, f"Active/deferred overlap: {overlap}"

    def test_consent_chain_untouched(self):
        for rid in ("R-013", "R-014", "R-015", "R-017"):
            assert rid in MH_DEFERRED_RULES, rid
            assert rid not in MH_INCLUDED_RULE_IDS, rid


class TestECIdentityMatrix:
    """Field-by-field identity from the CURRENT registers."""

    def test_r001_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-001")
        assert row["approval_id"] == EC_APPROVAL
        assert row["title"] == (
            "Prior Environmental Clearance - Schedule item 5(f) "
            "Synthetic organic chemicals"
        )
        assert row["obligation_type"] == "APPROVAL"
        assert row["authority"] == "AUT-001 (Cat A) / AUT-002 (Cat B)"
        assert row["jurisdiction"] == "CENTRAL (state-level appraisal for B)"
        assert "F-PRD-01 == TRUE" in row["applicability_conditions"]
        assert "F-PRD-03 IN {SYNTHESIS,MIXED}" in row[
            "applicability_conditions"
        ]
        assert row["required_inputs"] == "F-PRD-01;F-PRD-03"
        assert row["stage"] == "PRE_ESTABLISHMENT"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["effective_date"] == "2006-09-14"
        assert row["effective_date_status"] == "EXACT_DATE"
        assert row["source_id"] == "SRC-001"
        assert row["source_tier"] == "T1"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["rule_kind"] == "DETERMINISTIC"
        assert "FORMULATION_ONLY" in row["notes"]

    def test_r001_rules_csv_identity(self):
        row = _register_row("rules.csv", "rule_id", "R-001")
        assert row["approval_id"] == EC_APPROVAL
        assert row["facts"] == "F-PRD-01;F-PRD-03"
        assert row["legal_basis"] == "EIA 2006 Sch item 5(f)"
        assert row["source_id"] == "SRC-001"
        assert row["effective_from"] == "2006-09-14"
        assert row["final_status"] == "VERIFIED_CONDITIONAL"

    def test_r001_code_state_deferred(self):
        assert "R-001" in MH_DEFERRED_RULES
        assert "FORMULATION_ONLY" in MH_DEFERRED_RULES["R-001"]
        assert "R-001" not in MH_INCLUDED_RULE_IDS
        assert "R-001" not in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_r064_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-064")
        assert row["approval_id"] == EC_APPROVAL
        assert row["authority"] == "AUT-001 (Cat A) / AUT-002 (Cat B)"
        assert row["required_inputs"] == "F-PRD-01;F-PRD-02;F-PRD-03"
        assert row["stage"] == "PRE_ESTABLISHMENT"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["effective_date"] == "2014-06-25"
        assert row["source_id"] == "SRC-001"
        assert row["source_tier"] == "T1"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert "drug formulation-only -> OUTSIDE 5(f)" in row[
            "applicability_conditions"
        ]
        assert row["notes"] == "UNK-033"

    def test_r064_condition_truncated_in_register(self):
        """The condition cell ends mid-token; scope text is incomplete."""
        row = _register_row("rule_register_v5.csv", "rule_id", "R-064")
        cell = row["applicability_conditions"]
        assert cell.endswith("produ"), cell[-40:]
        assert "blending/formulation-only of non-drug" in cell

    def test_r064_rules_csv_operator_is_scope(self):
        row = _register_row("rules.csv", "rule_id", "R-064")
        assert row["operator"] == "scope"
        assert row["legal_basis"] == "EIA Sch 5(f) col 2"

    def test_r064_code_state_deferred(self):
        assert "R-064" in MH_DEFERRED_RULES
        assert "UNK-033" in MH_DEFERRED_RULES["R-064"]
        assert "R-064" not in MH_INCLUDED_RULE_IDS

    def test_r074_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-074")
        assert row["approval_id"] == EC_APPROVAL
        assert "UNKNOWN when EC_5F_REQUIRED==TRUE AND EC_8A==TRUE" in row[
            "applicability_conditions"
        ]
        assert row["required_inputs"] == "F-PRD-01;F-BLD-01"
        assert row["status"] == "UNKNOWN"
        assert row["source_id"] == "SRC-001"
        assert row["implementation_status"] == "REQUIRES_CONFIRMATION"
        assert row["rule_kind"] == "GUARD_OR_ROUTING"
        assert "UNK-010" in row["notes"]

    def test_r074_code_state_gated_unknown(self):
        assert "R-074" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-074" in MH_UNKNOWN_RULE_IDS
        assert "R-074" not in MH_DEFERRED_RULES
        assert "R-074" not in MH_INCLUDED_RULE_IDS

    def test_r002_context_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-002")
        assert row["approval_id"] == EC_APPROVAL
        assert "F-PRC-01 < 25" in row["applicability_conditions"]
        assert "F-PRC-03 == FALSE" in row["applicability_conditions"]
        assert row["effective_date"] == "2014-06-25"
        assert "R-002" in MH_INCLUDED_RULE_IDS


class TestFormulationOnlyTrap:
    """The register forbids what the engine would otherwise compute."""

    def test_process_mode_values_include_non_synthesis_modes(self):
        spec = get_fact_spec(MH_JURISDICTION, "F-PRD-03")
        assert "SYNTHESIS" in spec.allowed_values
        assert "MIXED" in spec.allowed_values
        assert "FORMULATION_ONLY" in spec.allowed_values
        assert "BLENDING_ONLY" in spec.allowed_values

    def test_naive_r001_encoding_fails_open_on_formulation_only(self):
        """A boolean `in {SYNTHESIS,MIXED}` encoding of R-001 evaluates a
        formulation-only project to FALSE (DOES_NOT_APPLY). The register
        note requires UNKNOWN instead - the encoding is therefore
        unsafe and stays deferred. Built here as a bare condition (never
        via _encode, which correctly refuses R-001)."""
        naive = ApplicabilityCondition(
            kind="condition",
            field="F-PRD-03",
            op="in",
            value=["SYNTHESIS", "MIXED"],
        )
        probe = ApprovalRule(
            id="PROBE-R-001",
            approval_id=EC_APPROVAL,
            applicability_conditions=[naive],
            source_refs=[
                SourceRef(source_id="SRC-001", citation_span="probe")
            ],
            version="probe",
        )
        result = evaluate_rule(
            probe, {"F-PRD-03": "FORMULATION_ONLY"}
        ).result
        assert result == "does_not_apply"
        # BLENDING_ONLY fails the same open direction (ET-071: UNKNOWN).
        result_blend = evaluate_rule(
            probe, {"F-PRD-03": "BLENDING_ONLY"}
        ).result
        assert result_blend == "does_not_apply"

    def test_register_edge_tests_require_unknown_not_false(self):
        assert _register_row(
            "edge_tests.csv", "test_id", "ET-016"
        )["expected"].startswith("EC_5F_REQUIRED=UNKNOWN")
        assert "UNKNOWN" in _register_row(
            "edge_tests.csv", "test_id", "ET-071"
        )["expected"]

    def test_no_category_fact_exists(self):
        """Category A/B is nowhere stored, derived, or looked up."""
        assert "MPCB_CATEGORY" not in MH_FACTS
        assert "EC_CATEGORY" not in MH_FACTS
        assert not [
            k for k in MH_FACTS if k.startswith("F-CAT")
        ]


class TestExceptionFacetBehavior:
    """APR-001 is served only by the R-002 exception facet (pinned)."""

    def test_only_r002_serves_apr001(self):
        assert [r.id for r in _apr001_rules()] == ["R-002"]

    def test_large_unit_reports_does_not_apply(self):
        """P0 MIGRATION (§16 design): R-002 is CLASSIFICATION, so the
        former fail-OPEN defect (complete not-small facts aggregating to
        DOES_NOT_APPLY) is gone: with no trigger rule built, the
        composed verdict is honest INSUFFICIENT_DATA. Moved deliberately
        from the EC audit's defect pin."""
        facts = {
            "F-PRD-01": True,
            "F-PRD-03": "SYNTHESIS",
            "F-PRC-01": 500,
            "F-PRC-02": 200,
            "F-PRC-03": False,
            "F-LOC-02": False,
        }
        compositions = load_regulatory_pack(IN_MH).approval_compositions
        evals = evaluate_approval_applicability(_apr001_rules(), facts)
        assert summarize_by_approval(
            evals, compositions=compositions
        )[EC_APPROVAL].result == ("insufficient_data")

    def test_small_unit_reports_applies(self):
        """P0 MIGRATION (§16 design): the small-unit facet alone no
        longer reports APPLIES at approval level (that was the
        exception-facet defect). Moved deliberately."""
        facts = {
            "F-PRD-01": True,
            "F-PRD-03": "SYNTHESIS",
            "F-PRC-01": 10,
            "F-PRC-02": 10,
            "F-PRC-03": False,
        }
        compositions = load_regulatory_pack(IN_MH).approval_compositions
        evals = evaluate_approval_applicability(_apr001_rules(), facts)
        assert summarize_by_approval(
            evals, compositions=compositions
        )[EC_APPROVAL].result == ("insufficient_data")

    def test_missing_inputs_fail_closed(self):
        evals = evaluate_approval_applicability(_apr001_rules(), {})
        assert summarize_by_approval(evals)[EC_APPROVAL].result == (
            "insufficient_data"
        )

    def test_r002_boundaries(self):
        by_id = {r.id: r for r in load_mh_approval_rules()}
        rule = by_id["R-002"]
        assert evaluate_rule(
            rule, {"F-PRC-01": 24.99, "F-PRC-02": 24.99, "F-PRC-03": False}
        ).result == "applies"
        assert evaluate_rule(
            rule, {"F-PRC-01": 25, "F-PRC-02": 10, "F-PRC-03": False}
        ).result == "does_not_apply"
        assert evaluate_rule(
            rule, {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": True}
        ).result == "does_not_apply"
        # MAH unknown can never clear the exception (ET-010).
        assert evaluate_rule(
            rule,
            {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": "UNKNOWN"},
        ).result == "insufficient_data"
        assert evaluate_rule(rule, {}).result == "insufficient_data"
        # Effective window 2014-06-25 (register EXACT_DATE).
        assert rule.effective_from == date(2014, 6, 25)
        assert evaluate_rule(
            rule,
            {"F-PRC-01": 10, "F-PRC-02": 10, "F-PRC-03": False},
            evaluation_date=date(2014, 6, 24),
        ).result == "does_not_apply"


class TestEvidenceRegisters:
    """UNK-033 / UNK-010 / UR-06 / SRC-001 / category-coupling inputs."""

    def test_unk033_open(self):
        row = _register_row("unknowns.csv", "unknown_id", "UNK-033")
        assert "blending/formulation-only" in row["question"]
        assert "R-064" in row["related_ids"]
        assert row["status"] == "OPEN"
        assert row["final_status"] == "UNKNOWN"

    def test_unk010_open(self):
        row = _register_row("unknowns.csv", "unknown_id", "UNK-010")
        assert "8(a)" in row["question"]
        assert row["status"].startswith("OPEN")
        assert row["final_status"] == "UNKNOWN"

    def test_ur06_open(self):
        row = _register_row("unresolved_items.csv", "item_id", "UR-06")
        assert "R-074" in row["item"]
        assert "R-074 UNKNOWN" in row["current_safe_engine_behaviour"]
        assert row["v5_status"] == "OPEN"

    def test_src001_primary_and_bounded(self):
        row = _register_row("sources.csv", "source_id", "SRC-001")
        assert row["tier"] == "T1"
        assert row["source_type"] == "OFFICIAL_PRIMARY"
        assert row["issuing_authority"] == "MoEFCC (PARIVESH)"
        assert "13-07-2026" in row["title"]
        assert "does not state whether a 5(f) project also needs 8(a)" in (
            row["what_the_source_does_not_prove"]
        )

    def test_category_coupling_inputs_exist_but_uncomposed(self):
        """Every input the EC chain needs exists as a fact or a deferred
        rule output - but no composition primitive joins them."""
        assert get_fact_spec(MH_JURISDICTION, "F-PRD-01").value_type.value == (
            "boolean"
        )
        assert get_fact_spec(MH_JURISDICTION, "F-LOC-02").value_type.value == (
            "boolean"
        )
        assert get_fact_spec(MH_JURISDICTION, "F-LOC-03").value_type.value == (
            "boolean"
        )
        assert get_fact_spec(MH_JURISDICTION, "F-LOC-07").value_type.value == (
            "object"
        )
        # R-003 consumes R-002's output; R-074 consumes R-001/R-007
        # outputs - register-level rule references, unrepresentable.
        r003 = _register_row("rules.csv", "rule_id", "R-003")
        assert r003["facts"] == "F-LOC-02;R-002"
        assert r003["operator"] == "CASE"
        r004 = _register_row("rules.csv", "rule_id", "R-004")
        assert r004["operator"] == "ANY"
        assert "R-003" in MH_DEFERRED_RULES
        assert "R-004" in MH_DEFERRED_RULES

    def test_r003_r004_r005_r008_r075_code_states(self):
        assert "R-003" in MH_DEFERRED_RULES
        assert "R-004" in MH_DEFERRED_RULES
        assert "R-008" in MH_DEFERRED_RULES
        assert "R-075" in MH_DEFERRED_RULES
        assert "R-005" in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert "R-005" not in MH_DEFERRED_RULES
        assert "R-005" not in MH_INCLUDED_RULE_IDS


class TestDependencyPropagation:
    """EC uncertainty cannot falsely satisfy any loaded downstream edge."""

    def test_no_loaded_edge_consumes_apr001(self):
        pack = load_regulatory_pack("IN-MH")
        assert len(pack.dependencies) == 2  # DEP-009 x2 only
        for dep in pack.dependencies:
            assert dep.approval_id != EC_APPROVAL
            assert dep.prerequisite_approval_id != EC_APPROVAL

    def test_dep002_inferred_unknown_not_loaded(self):
        row = _register_row("dependencies.csv", "dep_id", "DEP-002")
        assert row["final_status"] == "UNKNOWN"
        assert row["inferred"] == "YES_INFERRED"
        loaded = {
            (d.prerequisite_approval_id, d.approval_id)
            for d in load_regulatory_pack("IN-MH").dependencies
        }
        assert ("APR-001", "APR-008") not in loaded

    def test_gj_isolation(self):
        gj_ids = {
            r.id for r in load_regulatory_pack(IN_GJ).approval_rules
        }
        assert gj_ids & EC_CORE_RULES == set()
        assert gj_ids & {"R-002"} == set()
