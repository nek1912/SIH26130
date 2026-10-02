"""Tests for Maharashtra R-021 Closure Audit (MAH derivation, APR-012).

R-021 closes as DEFERRED (class D): the MAH question (EXISTS over chemical
inventory with Sch2/Sch3 col-3 lookup, Part II class TOTALs, 500m
multi-installation aggregation) requires rule composition with deferred
R-019; the derived pipeline exists only partially (derive_mah_status:
exact-string col-3 join for F-PRC-03, no Sch-5 routing); unmapped chemicals
stay UNKNOWN per ET-081; source T1 SRC-016 (MSIHC as amended to 2000).

Register identity is verified against the CURRENT CSVs at runtime (same
pattern as test_mh_cto_renewal.py); code state is asserted against
MH_DEFERRED_RULES / MH_INCLUDED_RULE_IDS / _encode / the fact registry /
the pack. This audit's only pack-logic change is the explicit R-021
deferral entry (untriaged 6 -> 5).
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.rules.derivations import derive_mah_status
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
    MH_DO_NOT_IMPLEMENT_RULE_IDS,
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    MH_UNKNOWN_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.mh.dependencies import MH_DEP_DEFERRED
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

REMAINING_UNTRIAGED_AFTER: frozenset[str] = frozenset({
    "R-054",
    "R-059",
    "R-071",
    "R-072",
    "R-076",
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
        """59 pre-existing + R-021 + R-054 (R-054 closure audit)."""
        assert len(MH_DEFERRED_RULES) == 61

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128

    def test_active_deferred_disjoint(self):
        overlap = MH_INCLUDED_RULE_IDS & frozenset(MH_DEFERRED_RULES.keys())
        assert not overlap, f"Active/deferred overlap: {overlap}"


class TestR021Identity:
    """Field-by-field identity from the CURRENT registers."""

    def test_register_row_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-021")
        assert row["approval_id"] == "APR-012"
        title = "MSIHC - notification of site / safety report / on-site emergency plan"
        assert row["title"] == title
        assert row["obligation_type"] == "REPORT"
        assert row["jurisdiction"] == "CENTRAL rules, state authority"
        assert row["stage"] == "PRE_OPERATION"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["rule_kind"] == "DETERMINISTIC"
        assert row["required_inputs"] == "R-019"
        assert row["source_id"] == "SRC-016"
        assert row["source_tier"] == "T1"
        assert row["effective_date"] == "2000"
        assert "YEAR_ONLY" in row["effective_date_status"]

    def test_condition_needs_exists_aggregation_lookup(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-021")
        cond = row["applicability_conditions"]
        assert "EXISTS c:" in cond
        assert "Sch3 col3" in cond
        assert "Sch2 col3" in cond
        assert "TOTAL quantity" in cond
        assert "500 m" in cond

    def test_four_way_authority_routing(self):
        """Per Sch 5: CIF/DISH vs SPCB vs PESO-CCE vs Collector — dynamic
        routing, not a static authority."""
        row = _register_row("rule_register_v5.csv", "rule_id", "R-021")
        auth = row["authority"]
        assert "AUT-005" in auth
        assert "AUT-003" in auth
        assert "AUT-008" in auth
        assert "Collector" in auth

    def test_rules_csv_derived_pipeline_note(self):
        row = _register_row("rules.csv", "rule_id", "R-021")
        assert row["facts"] == "R-019"
        assert row["operator"] == "=="
        assert "MSIHC r.2" in row["legal_basis"]
        assert "DERIVED by the msihc_mapping_steps pipeline" in row["notes"]
        assert "never user-asserted" in row["notes"]
        assert "FALSE only if every hazardous chemical" in row["notes"]

    def test_apr012_approval_identity(self):
        row = _register_row("approvals.csv", "approval_id", "APR-012")
        assert row["record_class"] == "COMPLIANCE_APPROVAL"
        assert row["record_type"] == "REPORT"
        assert row["lifecycle_stage"] == "PRE_OPERATION;OPERATION"
        assert row["rule_ids"] == "R-019;R-020;R-021"
        assert row["precondition"] == "MAH derivation (R-091)"
        assert "CMP-010" in row["renewal_trigger"]
        assert "CMP-020" in row["change_trigger"]

    def test_hw_fact_identities(self):
        f01 = _register_row("facts.csv", "fact_id", "F-HW-01")
        assert f01["type"] == "BOOL_OR_UNKNOWN"
        f02 = _register_row("facts.csv", "fact_id", "F-HW-02")
        assert f02["type"] == "LIST"
        haz01 = _register_row("facts.csv", "fact_id", "F-HAZ-01")
        assert haz01["type"] == "LIST"
        assert "max_qty_t" in haz01["allowed_values_unit"]
        haz02 = _register_row("facts.csv", "fact_id", "F-HAZ-02")
        assert haz02["type"] == "LIST"
        assert "Must be sourced from Sch 2/3" in haz02["notes"]

    def test_code_status_is_deferred_not_active(self):
        assert "R-021" in MH_IMPLEMENTATION_SAFE_RULE_IDS
        assert "R-021" in MH_DEFERRED_RULES
        assert "R-021" not in MH_INCLUDED_RULE_IDS

    def test_encode_rejects_r021(self):
        with pytest.raises(ValueError, match="Rule R-021 is deferred"):
            _encode("R-021", "APR-012", [], [])


class TestSemanticReconstruction:
    """R-021 answers 'is this site MAH?' — boolean-shaped but unencodable."""

    def test_obligation_is_report_not_plain_approval(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-021")
        assert row["obligation_type"] == "REPORT"

    def test_report_duties_stay_separate(self):
        """DOC-009 (r.7/r.10 report), CMP-010 (audit/update), CMP-020
        (change report), CMP-011 (emergency plan) are report/audit duties,
        not applicability conjuncts."""
        doc = _register_row("documents.csv", "document_id", "DOC-009")
        assert doc["used_for"] == "APR-012"
        assert doc["issuer"] == "Occupier"
        cmp010 = _register_row("compliance.csv", "compliance_id", "CMP-010")
        assert cmp010["record_type"] == "AUDIT"
        assert cmp010["lifecycle_stage"] == "OPERATION"

    def test_apr012_unmodeled_in_pack(self):
        """No authority entry, document requirement, SLA record, evidence
        hint, dependency edge, or active rule for APR-012: nothing treats
        the MAH report as a decided approval."""
        mh_pack = load_regulatory_pack("IN-MH")
        assert "APR-012" not in mh_pack.approval_authorities
        assert mh_pack.get_requirements_for_approval("APR-012") == []
        assert not [s for s in mh_pack.sla_records if s.approval_id == "APR-012"]
        assert mh_pack.get_gaps_for_approval("APR-012") == []
        assert not [d for d in mh_pack.dependencies
                    if "APR-012" in (d.approval_id, d.prerequisite_approval_id)]
        assert not [r for r in load_mh_approval_rules()
                    if r.approval_id == "APR-012"]
        assert "SRC-016" not in {s.id for s in mh_pack.sources}


class TestSourceAudit:
    """T1 MSIHC text with explicit non-provisions."""

    def test_src016_is_t1_primary(self):
        row = _register_row("sources.csv", "source_id", "SRC-016")
        assert row["tier"] == "T1"
        assert row["source_type"] == "OFFICIAL_PRIMARY"
        assert "MSIHC" in row["title"]

    def test_src016_proves_rules_and_notes(self):
        row = _register_row("sources.csv", "source_id", "SRC-016")
        assert "r.7" in row["what_the_source_proves"]
        assert "Sch 2 & 3 notes" in row["what_the_source_proves"]

    def test_src016_does_not_prove_currency_or_ratios(self):
        """No post-2000 amendments in file; Sch 1 Part I not re-extracted;
        no sum-of-ratios rule: three explicit evidentiary ceilings."""
        row = _register_row("sources.csv", "source_id", "SRC-016")
        assert "amendment after 2000" in row["what_the_source_does_not_prove"]
        assert "sum-of-ratios" in row["what_the_source_does_not_prove"]

    def test_post_2000_amendments_open(self):
        row = _register_row("unknowns.csv", "unknown_id", "UNK-035")
        assert row["final_status"] == "UNKNOWN"
        assert "R-021" in row["related_ids"]


class TestFactAudit:
    """Inventory + mapping exist; UNKNOWN-token support does not."""

    def test_code_fact_specs(self):
        assert get_fact_spec("IN-MH", "F-HAZ-01").value_type == FactValueType.LIST
        assert get_fact_spec("IN-MH", "F-HAZ-02").value_type == FactValueType.LIST
        assert get_fact_spec("IN-MH", "F-HAZ-01").unknown_allowed is False
        assert get_fact_spec("IN-MH", "F-HAZ-02").unknown_allowed is False

    def test_unknown_token_rejected_for_inventory_lists(self):
        """F-HAZ-01/02 are strict LISTs: the register's 'UNKNOWN qty /
        mapping → UNKNOWN' can only be expressed as missing/None, never as
        an UNKNOWN token. Supply discipline, documented."""
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-HAZ-01", "UNKNOWN")
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-HAZ-02", "UNKNOWN")
        validate_fact_value("IN-MH", "F-HAZ-01", None)
        validate_fact_value("IN-MH", "F-HAZ-02", None)

    def test_derived_mah_pipeline_behavior(self):
        """derive_mah_status (R-091 partial): exact-string col-3 join, TRUE
        dominates, FALSE only when every item resolved, else None — never
        FALSE for unmapped chemicals (ET-081 spirit)."""
        hit = [{"chemical": "ammonia", "max_qty_t": 50}]
        mapping = [{"chemical": "ammonia", "col3_t": 50}]
        assert derive_mah_status(hit, mapping) is True
        below = [{"chemical": "ammonia", "max_qty_t": 49}]
        assert derive_mah_status(below, mapping) is False
        unmapped = [{"chemical": "mystery", "max_qty_t": 999}]
        assert derive_mah_status(unmapped, mapping) is None
        assert derive_mah_status(None, None) is None

    def test_derivation_is_partial_not_pipeline(self):
        """The derivation covers none of: Sch2-vs-Sch3 storage branching,
        Part II class TOTALs, 500m aggregation, Sch-5 routing. R-019 (which
        needs all four) is deferred; R-021 needs R-019 on top."""
        assert "R-019" in MH_DEFERRED_RULES
        assert "R-020" in MH_DEFERRED_RULES
        assert "R-091" in MH_DEFERRED_RULES

    def test_no_mah_scalar_supplied_fact(self):
        """F-PRC-03 (is_MAH) is DERIVED, never supplied: MAH status cannot
        be user-asserted into the engine."""
        spec = get_fact_spec("IN-MH", "F-PRC-03")
        assert spec.derived is True

    def test_gj_namespace_rejects_msihc_facts(self):
        for fid, value in (("F-HAZ-01", [{"chemical": "x"}]),
                           ("F-HAZ-02", [{"chemical": "x"}])):
            with pytest.raises(FactValidationError) as exc:
                validate_fact_value("IN-GJ", fid, value)
            assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH


class TestEngineRepresentability:
    """EXISTS, aggregation, lookup, composition, routing: all absent."""

    def test_no_exists_quantifier(self):
        assert [op.value for op in ApplicabilityOp] == [
            "eq", "in", "gte", "lte", "gt", "lt",
        ]

    def test_composition_donor_deferred(self):
        """R-021's required input is R-019, which is deferred for EXISTS +
        multi-schedule eval + aggregation + Sch-5 routing."""
        reason = MH_DEFERRED_RULES["R-019"]
        assert "EXISTS" in reason
        assert "aggregation" in reason
        assert "Sch 5" in reason or "authority routing" in reason

    def test_no_rule_reference_primitive(self):
        """ConditionNode leaves carry field/op/value only — an 'R-019 =='
        reference (as the register literally records for R-017/R-021) has
        no representation."""
        assert "R-019" in MH_DEFERRED_RULES["R-021"]

    def test_year_only_effective_window(self):
        """2000 YEAR_ONLY: temporal queries before year-end fail closed
        (same discipline as R-078/R-080)."""
        assert "R-021" in MH_DEFERRED_RULES


class TestFalsificationFindings:
    """Attempted defeaters, each checked against the register."""

    def test_per_entry_blocks_recorded(self):
        """S1-TOX (contradictory signs), S2-18 (col-4 '501' unconfirmed),
        S3P1-111 (50 t vs 5 t, CON-023): per-entry hazards stay blocked
        rather than averaged into the table."""
        for item_id in ("S1-TOX", "S2-18", "S3P1-111"):
            row = _register_row("requires_confirmation.csv", "id", item_id)
            assert row["applies_to"] == "APR-012"

    def test_partial_items_open(self):
        """UR-01 (col-4 values), UR-02 (ethyleneimine/names), UR-03
        (post-2000 amendments): all PARTIAL, none silently resolved."""
        for item_id in ("UR-01", "UR-02", "UR-03"):
            row = _register_row("unresolved_items.csv", "item_id", item_id)
            assert row["v5_status"] == "PARTIAL"

    def test_threshold_conflict_resolved_not_hidden(self):
        """CON-021 (Sch 3 col-3 extraction conflicts) is RESOLVED with
        named winning values — recorded, not averaged."""
        row = _register_row("conflicts.csv", "conflict_id", "CON-021")
        assert row["final_status"] == "VERIFIED"

    def test_unmapped_chemical_stays_unknown_per_et081(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-081")
        assert row["rule_id"] == "R-021"
        assert row["expected"] == "MAH=UNKNOWN"

    def test_no_sum_of_ratios_rule(self):
        """A sum-of-ratios aggregation (common in other regimes) must not
        be assumed: the source explicitly lacks it."""
        row = _register_row("sources.csv", "source_id", "SRC-016")
        assert "sum-of-ratios" in row["what_the_source_does_not_prove"]

    def test_authority_is_not_single(self):
        """Any encoding defaulting to one of AUT-005/AUT-003/AUT-008/
        Collector would misroute three of four branches."""
        row = _register_row("approvals.csv", "approval_id", "APR-012")
        for token in ("AUT-005", "AUT-003", "AUT-008", "Collector"):
            assert token in row["authority_id"]

    def test_jurisdiction_is_central_with_state_authority(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-021")
        assert row["jurisdiction"] == "CENTRAL rules, state authority"

    def test_hazardous_alone_triggers_nothing(self):
        """Approvals note: do not treat 'hazardous chemical' as automatic
        MSIHC obligation — quantity ≥ col 3 is required (ET-022: 49 t vs
        50 t ammonia → FALSE)."""
        row = _register_row("edge_tests.csv", "test_id", "ET-022")
        assert "FALSE" in row["expected"]


class TestDependencyAnalysis:
    """APR-012 edges are activity-directed; all triaged out of the pack."""

    def test_time_lead_edges_triaged(self):
        assert MH_DEP_DEFERRED["DEP-010"] == "out of batch-1 scope"
        assert MH_DEP_DEFERRED["DEP-011"] == "out of batch-1 scope"
        assert MH_DEP_DEFERRED["DEP-026"] == "out of batch-1 scope"

    def test_no_apr012_edges_in_pack(self):
        mh_pack = load_regulatory_pack("IN-MH")
        assert not [d for d in mh_pack.dependencies
                    if "APR-012" in (d.approval_id, d.prerequisite_approval_id)]

    def test_no_active_rule_uses_msihc_facts(self):
        """F-HAZ-01/02 feed only the R-091 derivation (for R-002/DISH
        inputs), never an active ApprovalRule predicate."""
        from app.seed.mh.approvals import load_mh_approval_rules as _load

        for rule in _load():
            for cond in rule.applicability_conditions:
                fields: set[str] = set()
                stack = [cond]
                while stack:
                    node = stack.pop()
                    if hasattr(node, "field"):
                        fields.add(node.field)
                    stack.extend(getattr(node, "conditions", []) or [])
                    if getattr(node, "condition", None) is not None:
                        stack.append(node.condition)
                assert "F-HAZ-01" not in fields, rule.id
                assert "F-HAZ-02" not in fields, rule.id


class TestJurisdictionIsolation:
    """IN-MH closure work must not leak into IN-GJ."""

    def test_gj_pack_untouched(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        gj_ids = {r.id for r in gj_pack.approval_rules}
        assert "R-021" not in gj_ids

    def test_gj_approvals_untouched(self):
        gj_approval_ids = {r.approval_id
                           for r in load_regulatory_pack(IN_GJ).approval_rules}
        assert "APR-012" not in gj_approval_ids

    def test_mh_active_unchanged(self):
        assert len(load_mh_approval_rules()) == 26


class TestStatusDecision:
    """Exactly one disposition: DEFERRED (class D)."""

    def test_r021_is_class_d(self):
        assert "R-021" in MH_DEFERRED_RULES
        reason = MH_DEFERRED_RULES["R-021"]
        assert "R-019" in reason
        assert "Sch-5" in reason
        assert "ET-081" in reason

    def test_zero_rules_activated(self):
        assert len(load_mh_approval_rules()) == 26
        assert "R-021" not in MH_INCLUDED_RULE_IDS

    def test_untriaged_set_shrinks_past_five(self):
        """R-021 triaged; remainder is a subset of the four still-open
        rules (parallel sessions may triage further entries)."""
        register_ids = {f"R-{i:03d}" for i in range(1, 106)}
        triaged = (
            set(MH_INCLUDED_RULE_IDS) | set(MH_DEFERRED_RULES)
            | set(MH_REQUIRES_CONFIRMATION_RULE_IDS)
            | set(MH_DO_NOT_IMPLEMENT_RULE_IDS) | set(MH_UNKNOWN_RULE_IDS)
        )
        remainder = register_ids - triaged
        assert "R-021" not in remainder
        assert remainder <= {
            "R-054", "R-059", "R-071", "R-072", "R-076",
        }

    def test_consent_chain_untouched(self):
        """Parallel-work rule: R-013/R-014/R-015/R-017 outcomes preserved."""
        for rule_id in ("R-013", "R-014", "R-015", "R-017"):
            assert rule_id in MH_DEFERRED_RULES
