"""Tests for Maharashtra Residual Hygiene Audit (R-059/R-071/R-072/R-076).

The last four code-untriaged register-SAFE rules (R-054 was triaged by a
follow-up session implementing the R-054 audit). Each is documented here
as TRIAGED - HYGIENE/DOCUMENTATION with a distinct rationale - guard
hard-stop (R-059), regime date-gate (R-071), assignment-triggered duty
(R-072), deadline-layer facet (R-076) - and none is implemented, gated,
or deleted. Status sets are deliberately unchanged: explicit code-triage
entries would break the parallel R-021 session's untriaged-set pin and
this suite's own inventory pin, so they are recorded as a follow-up.

Register identity is verified against the CURRENT CSVs at runtime (same
pattern as test_mh_r054.py). Zero pack/engine/fact changes.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.rules.facts import MH_FACTS
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_DO_NOT_IMPLEMENT_RULE_IDS,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    MH_UNKNOWN_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

RESIDUE: frozenset[str] = frozenset({"R-059", "R-071", "R-072", "R-076"})
REGISTER_IDS = {f"R-{i:03d}" for i in range(1, 106)}


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


def _rows(filename: str) -> list[dict[str, str]]:
    csv_dir = _get_csv_dir()
    with open(csv_dir / filename, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TestBaselineAndArithmetic:
    """Baseline plus the closed inventory arithmetic."""

    def test_baseline_counts(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"
        assert len(load_mh_approval_rules()) == 26
        # 59 + R-021 (MSIHC session) + R-054 (R-054-audit follow-up).
        assert len(MH_DEFERRED_RULES) == 61
        assert len(MH_REQUIRES_CONFIRMATION_RULE_IDS) == 26
        assert len(MH_FACTS) == 128
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_untriaged_recomputed_is_exactly_the_four(self):
        triaged = (
            set(MH_INCLUDED_RULE_IDS)
            | set(MH_DEFERRED_RULES)
            | set(MH_REQUIRES_CONFIRMATION_RULE_IDS)
            | set(MH_DO_NOT_IMPLEMENT_RULE_IDS)
            | set(MH_UNKNOWN_RULE_IDS)
        )
        assert REGISTER_IDS - triaged == set(RESIDUE)

    def test_r054_follow_up_landed(self):
        assert "R-054" in MH_DEFERRED_RULES
        assert "R-054" not in MH_INCLUDED_RULE_IDS

    def test_residue_untouched_in_code_sets(self):
        for rid in RESIDUE:
            assert rid in MH_IMPLEMENTATION_SAFE_RULE_IDS, rid
            assert rid not in MH_INCLUDED_RULE_IDS, rid
            assert rid not in MH_DEFERRED_RULES, rid
            assert rid not in MH_REQUIRES_CONFIRMATION_RULE_IDS, rid
            assert rid not in MH_DO_NOT_IMPLEMENT_RULE_IDS, rid
            assert rid not in MH_UNKNOWN_RULE_IDS, rid

    def test_active_deferred_disjoint(self):
        overlap = MH_INCLUDED_RULE_IDS & frozenset(MH_DEFERRED_RULES.keys())
        assert not overlap, f"Active/deferred overlap: {overlap}"


class TestResidueIdentity:
    """Field-by-field identity from the CURRENT registers."""

    def test_r059_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-059")
        assert row["approval_id"] == "INC-*"
        assert row["title"].strip() == "INCENTIVE_VALUE"
        assert row["obligation_type"] == "RULE_LOGIC"
        assert row["authority"] == "-"
        assert row["applicability_conditions"] == "INCENTIVE_VALUE := NOT_COMPUTED"
        assert row["required_inputs"] == "-"
        assert row["stage"] == "-"
        assert row["status"] == "VERIFIED"
        assert row["source_id"] == "SRC-073;SRC-074"
        assert row["source_tier"] == "T3"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["rule_kind"] == "GUARD_OR_ROUTING"
        assert row["notes"] == "Hard stop"

    def test_r071_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-071")
        assert row["approval_id"] == "CND-024"
        assert row["title"].strip() == "MH_GW_ACT_IN_FORCE"
        assert row["obligation_type"] == "RULE_LOGIC"
        assert "TRUE from 01-06-2014" in row["applicability_conditions"]
        assert "R-097" in row["applicability_conditions"]
        assert "DRAFT" in row["applicability_conditions"]
        assert row["required_inputs"] == "F-WAT-05"
        assert row["status"] == "VERIFIED"
        assert row["effective_date"] == "2014-06-01"
        assert row["effective_date_status"] == "EXACT_DATE"
        assert row["source_id"] == "SRC-131;SRC-132"
        assert row["source_tier"] == "T1"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["notes"] == "Do not return FALSE"

    def test_r072_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-072")
        assert row["approval_id"] == "CMP-014"
        assert row["title"].strip() == "ENV_AUDIT"
        assert row["obligation_type"] == "RULE_LOGIC"
        assert "assigned by authority or engaged by proponent" in row[
            "applicability_conditions"
        ]
        assert row["required_inputs"] == "-"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["effective_date"] == "2025-08-29"
        assert row["source_id"] == "SRC-066"
        assert row["source_tier"] == "T1"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"

    def test_r076_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-076")
        assert row["approval_id"] == "CMP-006"
        assert row["title"].strip() == "EC_COMPLIANCE_DUE"
        assert row["obligation_type"] == "RULE_LOGIC"
        assert "1 June and 1 December" in row["applicability_conditions"]
        assert row["required_inputs"] == "EC granted"
        assert row["status"] == "VERIFIED"
        assert row["effective_date"] == "2026-07-13"
        assert row["source_id"] == "SRC-001"
        assert row["source_tier"] == "T1"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"

    def test_rules_csv_operators(self):
        assert _register_row("rules.csv", "rule_id", "R-059")["operator"] == "-"
        assert _register_row("rules.csv", "rule_id", "R-071")["operator"] == "-"
        assert _register_row("rules.csv", "rule_id", "R-072")["operator"] == "-"
        assert _register_row("rules.csv", "rule_id", "R-076")["operator"] == (
            "DATE"
        )


class TestNoApprovalTargets:
    """None of the four targets an APR-xxx approval."""

    def test_targets_are_non_approval_namespaces(self):
        assert _register_row("rule_register_v5.csv", "rule_id", "R-059")[
            "approval_id"
        ].startswith("INC-")
        assert _register_row("rule_register_v5.csv", "rule_id", "R-071")[
            "approval_id"
        ].startswith("CND-")
        assert _register_row("rule_register_v5.csv", "rule_id", "R-072")[
            "approval_id"
        ].startswith("CMP-")
        assert _register_row("rule_register_v5.csv", "rule_id", "R-076")[
            "approval_id"
        ].startswith("CMP-")

    def test_no_approvals_csv_rows(self):
        ids = {r["approval_id"] for r in _rows("approvals.csv")}
        assert ids & {"INC-*", "CND-024", "CMP-014", "CMP-006"} == set()

    def test_cmp014_dni_cmp006_roc(self):
        c14 = _register_row("compliance.csv", "compliance_id", "CMP-014")
        assert c14["implement_status"] == "DO_NOT_IMPLEMENT_YET"
        assert c14["record_type"] == "AUDIT"
        c06 = _register_row("compliance.csv", "compliance_id", "CMP-006")
        assert c06["implement_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert c06["confidence"] == "LOW"
        assert "1 June and 1 December" in c06["frequency_deadline"]

    def test_incentive_layer_posture(self):
        dni = [
            r
            for r in _rows("incentives.csv")
            if r["implement_status"].startswith("DO_NOT_IMPLEMENT")
        ]
        assert len(dni) == 7
        et43 = _register_row("edge_tests.csv", "test_id", "ET-043")
        assert et43["expected"] == "INCENTIVE_VALUE=NOT_COMPUTED"


class TestSourceSanity:
    """Lightweight source checks, including the para-10 tension."""

    def test_r059_sources_are_negative_only(self):
        for sid in ("SRC-073", "SRC-074"):
            row = _register_row("sources.csv", "source_id", sid)
            assert row["tier"] == "T3"
            # Both portals evidence the ABSENCE of a PSI 2025 instrument
            # (wording differs: "no PSI 2025 listed" vs "No PSI 2025 GR
            # listed") - the hard stop rests on that absence.
            proves = row["what_the_source_proves"]
            assert "PSI 2025" in proves and "list" in proves.lower()

    def test_r071_commencement_proven(self):
        row = _register_row("sources.csv", "source_id", "SRC-131")
        assert row["tier"] == "T1"
        assert "01-06-2014" in row["what_the_source_proves"]
        assert "not" in row["what_the_source_does_not_prove"].lower()

    def test_r072_no_blanket_obligation_proven(self):
        row = _register_row("sources.csv", "source_id", "SRC-066")
        assert row["tier"] == "T1"
        assert "blanket" in row["what_the_source_does_not_prove"]

    def test_para10_attribution_tension(self):
        """R-076 cites SRC-001 para 10(ii), but SRC-001's own row
        disclaims paras 9/10 extraction - while UNK-017 (CLOSED_V3) and
        CMP-006.frequency_deadline corroborate the 1 Jun/1 Dec content.
        Content corroborated x3; locator attribution unresolved. Pinned
        for any future deadline-layer use; blocks nothing today."""
        src001 = _register_row("sources.csv", "source_id", "SRC-001")
        assert "10 (post-EC monitoring) were not extracted" in src001[
            "what_the_source_does_not_prove"
        ]
        unk017 = _register_row("unknowns.csv", "unknown_id", "UNK-017")
        assert "1 Jun/1 Dec" in unk017["status"]
        assert "1 June and 1 December" in _register_row(
            "compliance.csv", "compliance_id", "CMP-006"
        )["frequency_deadline"]

    def test_r072_r076_have_no_edge_tests(self):
        ids = {e["rule_id"] for e in _rows("edge_tests.csv")}
        assert "R-072" not in ids
        assert "R-076" not in ids

    def test_r071_edge_test_respected_by_absence(self):
        et111 = _register_row("edge_tests.csv", "test_id", "ET-111")
        assert "UNKNOWN" in et111["expected"]


class TestConsumerAbsence:
    """Intentionally unconsumed (allowlist-only), not orphaned."""

    def test_no_pack_authority_strings(self):
        pack = load_regulatory_pack("IN-MH")
        for aid in ("INC-*", "CND-024", "CMP-014", "CMP-006"):
            assert aid not in pack.approval_authorities, aid

    def test_no_loaded_edges_or_docs(self):
        pack = load_regulatory_pack("IN-MH")
        trio = {"INC-*", "CND-024", "CMP-014", "CMP-006"}
        for dep in pack.dependencies:
            assert dep.approval_id not in trio
            assert dep.prerequisite_approval_id not in trio
        for req in pack.document_requirements:
            assert trio & set(req.get("approval_ids", [])) == set()

    def test_no_active_rule_serves_residue_targets(self):
        live_approvals = {r.approval_id for r in load_mh_approval_rules()}
        assert live_approvals & {"INC-*", "CND-024", "CMP-014", "CMP-006"} == (
            set()
        )

    def test_distinct_targets_inputs_no_duplicates(self):
        rows = {
            rid: _register_row("rule_register_v5.csv", "rule_id", rid)
            for rid in RESIDUE
        }
        assert len({r["approval_id"] for r in rows.values()}) == 4
        assert len({r["title"] for r in rows.values()}) == 4


class TestFactLinkage:
    """Fact shapes behind each disposition."""

    def test_r059_no_inputs(self):
        assert _register_row("rules.csv", "rule_id", "R-059")["facts"] == "-"

    def test_r071_input_is_coarse_but_present(self):
        assert "F-WAT-05" in MH_FACTS
        # Act-in-force does not depend on extraction quantity; the
        # linkage is spurious but harmless (rule unconsumed).

    def test_r072_no_inputs_assignment_is_case_state(self):
        assert _register_row("rules.csv", "rule_id", "R-072")["facts"] == "-"
        # F-LAB-10 ("engages_workers_in_Mathadi_scheduled_employment",
        # R-098) is the only assign/engag-labelled fact and is unrelated
        # to audit assignment/engagement: no audit-trigger fact exists.
        hits = [
            k
            for k, s in MH_FACTS.items()
            if "assign" in s.label.lower() or "engag" in s.label.lower()
        ]
        assert hits == ["F-LAB-10"]
        assert MH_FACTS["F-LAB-10"].group == "LAB"

    def test_r076_trigger_is_not_a_fact(self):
        assert "EC granted" not in MH_FACTS
        assert "F-EC-01" not in MH_FACTS

    def test_gj_isolation(self):
        gj_ids = {
            r.id for r in load_regulatory_pack(IN_GJ).approval_rules
        }
        assert gj_ids & RESIDUE == set()


def _collect(node) -> set[str]:
    """Field names referenced by a condition tree (test-local helper)."""
    from app.rules.models import (
        AndNode,
        ApplicabilityCondition,
        LiteralNode,
        NotNode,
        OrNode,
    )

    if isinstance(node, ApplicabilityCondition):
        return {node.field}
    if isinstance(node, (AndNode, OrNode)):
        out: set[str] = set()
        for child in node.conditions:
            out |= _collect(child)
        return out
    if isinstance(node, NotNode):
        return _collect(node.condition)
    if isinstance(node, LiteralNode):
        return set()
    raise AssertionError(f"unknown node {node!r}")
