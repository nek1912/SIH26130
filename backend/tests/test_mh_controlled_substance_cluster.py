"""Tests for Maharashtra Controlled-Substance Cluster Audit (R-065 primary).

R-065 (CWC declarations, APR-058) was the inventory's "closest-to-encodable"
remaining rule. This suite falsifies that hypothesis executably: the
registered predicate is a 6-way OR whose four schedule-quantity limbs range
over F-CWC-03 list-of-{schedule, qty} objects - per-element schedule
classification plus numeric comparison plus per-class thresholds - which no
ConditionNode expresses. A scalar-limbs-only partial encoding fails OPEN
(proven below with a probe that never enters the pack). R-065 stays
deferred; R-066/R-067-classification-only, R-050 unrelated chain.

R-066 (NCB Schedule A, APR-057) is structurally list-overlap-shaped but
needs amendment-currency and element-shape evidence first: classified,
not implemented. R-050 (Legal Metrology, APR-048) is a different regime
(REG-OTH packaging law, not controlled substances) with an unextracted
positive duty (r.27 CONDITIONAL ceiling), a missing package-marking fact,
and LOW duty confidence: classified, not implemented.

Register identity is verified against the CURRENT CSVs at runtime (same
pattern as test_mh_ec_core.py). Zero pack/engine/fact changes.
"""
from __future__ import annotations

import csv
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
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

CS_RULES: frozenset[str] = frozenset({"R-065", "R-066", "R-050"})

# Schedule A (domestic manufacture/possession controls) per SRC-099 /
# CND-013. Currency beyond RCS Order 2013 is explicitly unchecked in the
# registers ("later amendments not checked") - the membership probe below
# documents that assumption instead of relying on it.
SCHEDULE_A_2013 = frozenset({
    "acetic anhydride",
    "N-acetylanthranilic acid",
    "anthranilic acid",
    "ephedrine",
    "pseudoephedrine",
    "ANPP",
    "NPP",
})

# Protected IDs from prior audits - this cluster must not move them.
PROTECTED_IDS = frozenset({
    "R-001", "R-002", "R-064", "R-074",
    "R-013", "R-014", "R-015", "R-017",
    "R-018", "R-096",
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


def _probe_rule(
    rule_id: str, approval_id: str, conditions: list
) -> ApprovalRule:
    """Build a throwaway probe rule (never _encode, never the pack)."""
    return ApprovalRule(
        id=rule_id,
        approval_id=approval_id,
        applicability_conditions=conditions,
        source_refs=[SourceRef(source_id="SRC-PROBE", citation_span="probe")],
        version="probe",
    )


def _leaf(field: str, op: str, value) -> ApplicabilityCondition:
    return ApplicabilityCondition(
        kind="condition", field=field, op=op, value=value
    )


class TestBaselineCounts:
    """Confirm the repository baseline before asserting cluster effects."""

    def test_default_jurisdiction_is_gj(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_mh_active_rule_count_is_26(self):
        assert len(load_mh_approval_rules()) == 26

    def test_mh_deferred_count_is_61(self):
        # 59 at EC-core time + R-021 (MAH pipeline) + R-054, deferred by
        # parallel sessions during this audit - observed, untouched.
        assert len(MH_DEFERRED_RULES) == 61
        assert "R-021" in MH_DEFERRED_RULES
        assert "R-054" in MH_DEFERRED_RULES

    def test_mh_confirmation_count_is_26(self):
        assert len(MH_REQUIRES_CONFIRMATION_RULE_IDS) == 26

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128

    def test_cluster_not_active(self):
        assert CS_RULES & set(MH_INCLUDED_RULE_IDS) == set()

    def test_protected_ids_unmoved(self):
        assert "R-002" in MH_INCLUDED_RULE_IDS
        assert "R-018" in MH_INCLUDED_RULE_IDS
        assert "R-096" in MH_INCLUDED_RULE_IDS
        for rid in PROTECTED_IDS - {"R-002", "R-018", "R-096"}:
            assert rid in MH_DEFERRED_RULES or rid in (
                MH_REQUIRES_CONFIRMATION_RULE_IDS
            ), rid


class TestCSIdentityMatrix:
    """Field-by-field identity from the CURRENT registers."""

    def test_r065_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-065")
        assert row["approval_id"] == "APR-058"
        assert row["title"] == "CWC declarations (initial/annual) to NACWC"
        assert row["obligation_type"] == "RETURN"
        assert row["authority"] == "National Authority CWC (Cabinet Secretariat)"
        assert row["jurisdiction"] == "CENTRAL"
        assert "F-CWC-01 > 200" in row["applicability_conditions"]
        assert "Sch2A*>1 kg" in row["applicability_conditions"]
        assert "Sch3>30 t" in row["applicability_conditions"]
        assert row["required_inputs"] == "F-CWC-01;F-CWC-02;F-CWC-03"
        assert row["stage"] == "OPERATION"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["effective_date"] == "-"
        assert "UNKNOWN" in row["effective_date_status"]
        assert row["source_id"] == "SRC-098"
        assert row["source_tier"] == "T2"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["rule_kind"] == "DETERMINISTIC"
        assert row["notes"] == "Strictly greater-than"

    def test_r065_rules_csv_identity(self):
        row = _register_row("rules.csv", "rule_id", "R-065")
        assert row["facts"] == "F-CWC-01;F-CWC-02;F-CWC-03"
        assert row["operator"] == ">"
        assert row["unit"] == "t/yr"
        assert row["legal_basis"] == "NACWC declaration guidance"
        assert row["final_status"] == "VERIFIED_CONDITIONAL"

    def test_r065_code_state_deferred(self):
        assert "R-065" in MH_DEFERRED_RULES
        assert "quantifier" in MH_DEFERRED_RULES["R-065"]
        assert "R-065" not in MH_INCLUDED_RULE_IDS
        assert "R-065" not in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_r066_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-066")
        assert row["approval_id"] == "APR-057"
        assert row["title"] == (
            "NCB registration - controlled substances (Schedule A)"
        )
        assert row["obligation_type"] == "REGISTRATION"
        assert row["authority"] == "Narcotics Control Bureau"
        assert row["jurisdiction"] == "CENTRAL"
        assert "Schedule A substance" in row["applicability_conditions"]
        assert row["required_inputs"] == "F-NDPS-01"
        assert row["stage"] == "PRE_OPERATION"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["effective_date"] == "2013"
        assert row["source_id"] == "SRC-099"
        assert row["source_tier"] == "T2"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"

    def test_r066_rules_csv_operator_is_in(self):
        row = _register_row("rules.csv", "rule_id", "R-066")
        assert row["operator"] == "IN"
        assert row["threshold"] == "Schedule A list"
        assert row["legal_basis"] == "RCS Order 2013"

    def test_r066_code_state_deferred(self):
        assert "R-066" in MH_DEFERRED_RULES
        assert "lookup" in MH_DEFERRED_RULES["R-066"]
        assert "R-066" not in MH_INCLUDED_RULE_IDS

    def test_r050_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-050")
        assert row["approval_id"] == "APR-048"
        assert row["title"] == "Legal Metrology packer registration"
        assert row["obligation_type"] == "REGISTRATION"
        assert row["authority"] == "AUT-019"
        assert row["jurisdiction"] == "STATEWIDE"
        assert "F-OTH-01 == TRUE" in row["applicability_conditions"]
        assert "package marked" in row["applicability_conditions"]
        assert "r.27" in row["applicability_conditions"]
        assert row["required_inputs"] == "F-OTH-01;F-LM-01;F-LM-02"
        assert row["stage"] == "OPERATION"
        assert row["source_id"] == "SRC-095;SRC-062"
        assert row["source_tier"] == "T2;T3"
        assert "LOW" in row["confidence"]

    def test_r050_approval_confirmation_status(self):
        row = _register_row("approvals.csv", "approval_id", "APR-048")
        assert row["implement_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert row["confidence"] == "LOW"
        assert "not re-extracted" in row["legal_basis"]

    def test_r050_code_state_deferred(self):
        assert "R-050" in MH_DEFERRED_RULES
        assert "marking" in MH_DEFERRED_RULES["R-050"]
        assert "R-050" not in MH_INCLUDED_RULE_IDS


class TestEvidenceLinkage:
    """Sources, edge tests, unknowns, and branch rows that bound the audit."""

    def test_src098_guidance_bounded(self):
        row = _register_row("sources.csv", "source_id", "SRC-098")
        assert row["tier"] == "T2"
        assert row["source_type"] == "OFFICIAL_GUIDANCE"
        assert row["issuing_authority"] == (
            "National Authority Chemical Weapons Convention, "
            "Cabinet Secretariat"
        )
        assert "Sch 2A* >1 kg" in row["what_the_source_proves"]
        assert "section numbers" in row["what_the_source_does_not_prove"]
        assert "DOC/PSF" in row["what_the_source_does_not_prove"]

    def test_src099_list_bounded(self):
        row = _register_row("sources.csv", "source_id", "SRC-099")
        assert row["tier"] == "T2"
        assert row["source_type"] == "OFFICIAL_LIST"
        for name in ("acetic anhydride", "ephedrine", "ANPP"):
            assert name in row["what_the_source_proves"]
        assert "later amendments" in row["what_the_source_does_not_prove"]

    def test_src095_duty_unextracted(self):
        row = _register_row("sources.csv", "source_id", "SRC-095")
        assert row["tier"] == "T2"
        assert "r.27" in row["what_the_source_does_not_prove"]

    def test_strict_greater_than_pinned(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-104")
        assert row["rule_id"] == "R-065"
        assert "FALSE / TRUE" in row["expected"]
        assert "Strict >" in row["rationale"]

    def test_r066_single_edge_test(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-105")
        assert row["rule_id"] == "R-066"
        assert "acetic anhydride" in row["inputs"]
        assert "TRUE" in row["expected"]

    def test_lm_exclusion_boundaries(self):
        assert "does not apply" in _register_row(
            "edge_tests.csv", "test_id", "ET-102"
        )["expected"]
        assert "does not apply" in _register_row(
            "edge_tests.csv", "test_id", "ET-103"
        )["expected"]

    def test_unk022_closed_branches_classified(self):
        row = _register_row("unknowns.csv", "unknown_id", "UNK-022")
        assert "CLOSED_V3" in row["status"]

    def test_apr058_return_record_class(self):
        row = _register_row("approvals.csv", "approval_id", "APR-058")
        assert row["record_class"] == "COMPLIANCE_APPROVAL"
        assert row["record_type"] == "RETURN"
        assert row["applicability_class"] == "THRESHOLD_DEPENDENT"
        assert row["rule_ids"] == "R-065"

    def test_cmp021_trigger_reads_thresholds(self):
        row = _register_row("compliance.csv", "compliance_id", "CMP-021")
        assert row["trigger"] == "APR-058 thresholds met"
        assert row["record_type"] == "RETURN"


class TestFactOntology:
    """Fact shapes that decide representability."""

    def test_cwc_scalar_facts(self):
        for fid in ("F-CWC-01", "F-CWC-02"):
            spec = get_fact_spec(MH_JURISDICTION, fid)
            assert spec.value_type.value == "number"
            assert spec.unit == "t/yr"

    def test_cwc03_is_unitless_object_list(self):
        """F-CWC-03 elements carry {schedule, qty} with no unit field -
        per-element quantities cannot be compared against kg/t thresholds
        without a unit assumption the registers never supply."""
        spec = get_fact_spec(MH_JURISDICTION, "F-CWC-03")
        assert spec.value_type.value == "list"
        assert spec.unit is None

    def test_ndps01_is_bare_list(self):
        """F-NDPS-01 carries no element-shape contract - ET-105 suggests
        substance-name strings, but nothing pins strings vs objects."""
        spec = get_fact_spec(MH_JURISDICTION, "F-NDPS-01")
        assert spec.value_type.value == "list"

    def test_lm01_unit_conflated(self):
        """F-LM-01 merges kg and L into one number - the r.3 exclusion
        (>25 kg or 25 L) is package-type-dependent, the fact is not."""
        spec = get_fact_spec(MH_JURISDICTION, "F-LM-01")
        assert spec.unit == "kg_or_L"

    def test_no_package_marking_fact(self):
        assert "F-LM-03" not in MH_FACTS
        assert not [
            k for k, s in MH_FACTS.items() if "mark" in s.label.lower()
        ]

    def test_nacwc_ncb_have_no_authority_record(self):
        """APR-057/APR-058 authority_ids are free text with no AUT row -
        consistent with zero active rules there; display metadata only."""
        pack = load_regulatory_pack("IN-MH")
        assert "APR-057" not in pack.approval_authorities
        assert "APR-058" not in pack.approval_authorities
        assert "APR-048" not in pack.approval_authorities


class TestR065Falsification:
    """Scalar limbs work; the disjunction cannot be closed - the rule
    cannot enter the engine even partially."""

    def test_scalar_limbs_evaluate(self):
        probe = _probe_rule(
            "PROBE-R-065-SCALAR",
            "APR-058",
            [
                _leaf("F-CWC-01", "gt", 200),
                _leaf("F-CWC-02", "gt", 30),
            ],
        )
        # OR across top-level trees: any TRUE wins; strict > holds.
        assert evaluate_rule(
            probe, {"F-CWC-01": 200.1, "F-CWC-02": 5}
        ).result == "applies"
        assert evaluate_rule(
            probe, {"F-CWC-01": 200, "F-CWC-02": 5}
        ).result == "does_not_apply"
        assert evaluate_rule(probe, {}).result == "insufficient_data"
        # One limb unevaluable + one limb false = CONDITIONAL (engine
        # priority: any-TRUE > all-FALSE > mixed > all-missing). A real
        # encoding with unrepresentable schedule limbs could therefore
        # never even reach a clean FALSE - the disjunction stays open.
        assert evaluate_rule(
            probe, {"F-CWC-01": None, "F-CWC-02": 5}
        ).result == "conditional"

    def test_partial_encoding_fails_open(self):
        """DOCUMENTED FALSIFICATION: a scalar-only R-065 reports
        DOES_NOT_APPLY for a project with live Schedule 2A* activity
        (5 kg > 1 kg threshold), where the register mandates APPLIES.
        Narrowing the disjunction to the encodable limbs is therefore
        unsafe - the full predicate needs list quantifiers."""
        probe = _probe_rule(
            "PROBE-R-065-PARTIAL",
            "APR-058",
            [
                _leaf("F-CWC-01", "gt", 200),
                _leaf("F-CWC-02", "gt", 30),
            ],
        )
        facts = {
            "F-CWC-01": 50,
            "F-CWC-02": 5,
            "F-CWC-03": [{"schedule": "Sch2A*", "qty": 5}],
        }
        assert evaluate_rule(probe, facts).result == "does_not_apply"

    def test_schedule_limbs_have_no_leaf_form(self):
        """No ConditionNode leaf can address F-CWC-03 elements: leaves
        bind whole fields, and `gt` on a list value is a type error
        direction (fails closed, never a verdict)."""
        probe = _probe_rule(
            "PROBE-R-065-SCH",
            "APR-058",
            [_leaf("F-CWC-03", "gt", 1)],
        )
        result = evaluate_rule(
            probe, {"F-CWC-03": [{"schedule": "Sch2A*", "qty": 5}]}
        ).result
        assert result in ("does_not_apply", "insufficient_data")
        # Either way it is not a legal verdict: the limb is
        # unrepresentable, so the disjunction stays open.

    def test_no_active_rule_consumes_cwc_facts(self):
        for rule in load_mh_approval_rules():
            for node in rule.applicability_conditions:
                fields = _collect(node)
                assert "F-CWC-01" not in fields
                assert "F-CWC-02" not in fields
                assert "F-CWC-03" not in fields


class TestR066MembershipShape:
    """List-overlap works mechanically - currency and element shape do
    not (classification evidence, no implementation)."""

    def test_overlap_mechanics(self):
        probe = _probe_rule(
            "PROBE-R-066",
            "APR-057",
            [_leaf("F-NDPS-01", "in", sorted(SCHEDULE_A_2013))],
        )
        assert evaluate_rule(
            probe, {"F-NDPS-01": ["acetic anhydride"]}
        ).result == "applies"
        assert evaluate_rule(
            probe, {"F-NDPS-01": ["toluene"]}
        ).result == "does_not_apply"
        assert evaluate_rule(probe, {}).result == "insufficient_data"
        # UNKNOWN element with no match fails closed (tree fix).
        assert evaluate_rule(
            probe, {"F-NDPS-01": ["toluene", "UNKNOWN"]}
        ).result in ("insufficient_data", "conditional")

    def test_schedule_a_currency_unchecked_in_registers(self):
        row = _register_row("approvals.csv", "approval_id", "APR-057")
        assert "later amendments not checked" in row["notes"]
        cnd = _register_row("conditional_regs.csv", "cond_id", "CND-013")
        assert "ephedrine" in cnd["why"]

    def test_r066_independent_of_r065(self):
        """Disjoint statutes, authorities, stages, inputs - no refinement,
        no composition, no shared chain."""
        r065 = _register_row("rules.csv", "rule_id", "R-065")
        r066 = _register_row("rules.csv", "rule_id", "R-066")
        assert r065["approval_id"] != r066["approval_id"]
        assert set(r065["facts"].split(";")) & set(
            r066["facts"].split(";")
        ) == set()
        assert r065["regime"] != r066["regime"]


class TestR050UnrelatedChain:
    """Legal Metrology packaging law is not a controlled-substance rule."""

    def test_regime_and_scope_differ(self):
        r050 = _register_row("rules.csv", "rule_id", "R-050")
        r065 = _register_row("rules.csv", "rule_id", "R-065")
        assert r050["regime"] == "REG-OTH"
        assert r065["regime"] == "REG-CWC"
        assert set(r050["facts"].split(";")) & set(
            r065["facts"].split(";")
        ) == set()

    def test_positive_duty_unextracted_ceiling(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-050")
        assert "stays CONDITIONAL" in row["applicability_conditions"]

    def test_authority_confirmation_gated(self):
        row = _register_row("authorities.csv", "authority_id", "AUT-019")
        assert row["final_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"


class TestAttackMatrixCore:
    """Legally relevant scenarios with engine outcomes (probes only)."""

    def test_zero_quantities(self):
        probe = _probe_rule(
            "PROBE-ZERO", "APR-058", [_leaf("F-CWC-01", "gt", 200)]
        )
        assert evaluate_rule(probe, {"F-CWC-01": 0}).result == (
            "does_not_apply"
        )

    def test_empty_schedule_list_decides_nothing(self):
        """[] carries no register completeness rule ('no scheduled
        chemicals' vs 'not yet inventoried') - scalar limbs alone decide
        only themselves, never the declaration duty."""
        probe = _probe_rule(
            "PROBE-EMPTY",
            "APR-058",
            [
                _leaf("F-CWC-01", "gt", 200),
                _leaf("F-CWC-02", "gt", 30),
            ],
        )
        facts = {"F-CWC-01": 10, "F-CWC-02": 5, "F-CWC-03": []}
        assert evaluate_rule(probe, facts).result == "does_not_apply"
        # The probe verdict is mechanically correct for its two limbs and
        # legally void for the duty - exactly why partial encoding stays
        # out of the pack.

    def test_contradictory_inputs_stay_fail_closed(self):
        probe = _probe_rule(
            "PROBE-CONTRA", "APR-058", [_leaf("F-CWC-01", "gt", 200)]
        )
        assert evaluate_rule(
            probe, {"F-CWC-01": "UNKNOWN"}
        ).result == "insufficient_data"

    def test_approval_aggregation_empty_for_cluster(self):
        evals = evaluate_approval_applicability(
            load_mh_approval_rules(),
            {"F-CWC-01": 500},
            approval_ids=["APR-058", "APR-057", "APR-048"],
        )
        assert evals == []
        assert summarize_by_approval(evals) == {}


class TestDownstreamContainment:
    """UNKNOWN on R-065/066/050 cannot ready anything downstream."""

    def test_no_loaded_edges_or_docs(self):
        pack = load_regulatory_pack("IN-MH")
        trio = {"APR-048", "APR-057", "APR-058"}
        for dep in pack.dependencies:
            assert dep.approval_id not in trio
            assert dep.prerequisite_approval_id not in trio
        for req in pack.document_requirements:
            assert trio & set(req.get("approval_ids", [])) == set()

    def test_gj_isolation(self):
        gj_ids = {
            r.id for r in load_regulatory_pack(IN_GJ).approval_rules
        }
        assert gj_ids & CS_RULES == set()


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
