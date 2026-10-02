"""Tests for Maharashtra R-054 Audit (EC expansion exemption, APR-052).

R-054 was the last unaudited IMPLEMENTATION_SAFE approval rule. This suite
falsifies the SAFE label executably: the registered predicate is a
6-conjunct AND of which only two conjuncts (F-EXP-01, F-EXP-02 == FALSE)
have fact representation. Schedule-item scope (item IN {2,3,4,5}), the
empanelled-auditor certificate (Appendix XIII, PARIVESH + SPCB), OCMS
>=95% telemetry, and the B2->A/B1 category-change exclusion have no facts;
prior-EC-holder status (which the exemption presupposes) has no fact; the
else-branch routes to Form I under 7(ii)(a), not to DOES_NOT_APPLY. A
facts-only partial encoding therefore fails OPEN (proven below with a
probe that never enters the pack), and approval-level APPLIES would read
"exemption applies" as "approval applies" (the EC R-002 inversion
pattern). R-054 is triaged DEFERRED (class D) with an explicit entry; the
R-021 session pin it once deferred to is complete, so the follow-up is
done here. No engine/fact changes; one deferral entry.

Register identity is verified against the CURRENT CSVs at runtime (same
pattern as test_mh_ec_core.py).
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
    MH_IMPLEMENTATION_SAFE_RULE_IDS,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    _encode,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

# Conjuncts of the registered predicate with no fact representation.
UNMODELED_CONJUNCTS = (
    "item IN {2,3,4,5}",
    "auditor certificate (Appendix XIII)",
    "OCMS >=95%",
    "NOT (B2->A or B2->B1)",
    "prior EC holder",
)

# Protected IDs from prior audits - this cluster must not move them.
PROTECTED_DEFERRED = frozenset({
    "R-001", "R-064", "R-013", "R-014", "R-015", "R-017",
    "R-021", "R-050", "R-065", "R-066",
})
PROTECTED_ACTIVE = frozenset({"R-002", "R-018", "R-096"})


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


def _partial_r054() -> ApprovalRule:
    """The maximal facts-only encoding: 2 of 6 conjuncts."""
    from app.rules.models import AndNode

    return _probe_rule(
        "PROBE-R-054-PARTIAL",
        "APR-052",
        [
            AndNode(
                kind="and",
                conditions=[
                    _leaf("F-EXP-01", "eq", True),
                    _leaf("F-EXP-02", "eq", False),
                ],
            )
        ],
    )


class TestBaselineCounts:
    """Confirm the repository baseline before asserting cluster effects."""

    def test_default_jurisdiction_is_gj(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_mh_active_rule_count_is_26(self):
        assert len(load_mh_approval_rules()) == 26

    def test_mh_deferred_count_is_61(self):
        """60 at R-054-audit time + R-054 (this closure)."""
        assert len(MH_DEFERRED_RULES) == 61

    def test_mh_confirmation_count_is_26(self):
        assert len(MH_REQUIRES_CONFIRMATION_RULE_IDS) == 26

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128

    def test_protected_deferred_unmoved(self):
        for rid in PROTECTED_DEFERRED:
            assert rid in MH_DEFERRED_RULES, rid
        for rid in PROTECTED_ACTIVE:
            assert rid in MH_INCLUDED_RULE_IDS, rid
        assert "R-074" in MH_REQUIRES_CONFIRMATION_RULE_IDS

    def test_active_deferred_disjoint(self):
        overlap = MH_INCLUDED_RULE_IDS & frozenset(MH_DEFERRED_RULES.keys())
        assert not overlap, f"Active/deferred overlap: {overlap}"


class TestR054IdentityMatrix:
    """Field-by-field identity from the CURRENT registers."""

    def test_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-054")
        assert row["approval_id"] == "APR-052"
        assert row["title"] == (
            "EC for expansion / no-increase-in-pollution-load exemption"
        )
        assert row["obligation_type"] == "APPROVAL"
        assert row["authority"] == "AUT-001/AUT-002"
        assert row["jurisdiction"] == "CENTRAL"
        cond = row["applicability_conditions"]
        assert cond.startswith("EC_EXPANSION_EXEMPT := F-EXP-01")
        assert "item IN {2,3,4,5}" in cond
        assert "F-EXP-02 == FALSE" in cond
        assert "Appendix XIII" in cond
        assert "OCMS >=95%" in cond
        assert "B2->A or B2->B1" in cond
        assert "Form I under 7(ii)(a)" in cond
        assert row["required_inputs"] == "F-EXP-01;F-EXP-02"
        assert row["stage"] == "OPERATION"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["effective_date"] == "-"
        assert "UNKNOWN" in row["effective_date_status"]
        assert row["source_id"] == "SRC-001"
        assert row["source_tier"] == "T1"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["rule_kind"] == "DETERMINISTIC"
        assert "items 2-5" in row["notes"]

    def test_rules_csv_identity(self):
        row = _register_row("rules.csv", "rule_id", "R-054")
        assert row["approval_id"] == "APR-052"
        assert row["facts"] == "F-EXP-01;F-EXP-02"
        assert row["operator"] == "AND"
        assert row["legal_basis"] == "EIA 2006 para 7(ii)(b)"
        assert row["source_id"] == "SRC-001"
        assert row["effective_from"] == "-"
        assert row["final_status"] == "VERIFIED_CONDITIONAL"

    def test_code_state_triaged_deferred(self):
        """SAFE-listed, explicitly deferred, still unbuilt and ungated:
        the R-021 session pin it once deferred to is complete, so the
        follow-up triage is done here. Default-absence additionally fails
        closed via _encode's safe-set ordering."""
        assert "R-054" in MH_IMPLEMENTATION_SAFE_RULE_IDS
        assert "R-054" in MH_DEFERRED_RULES
        assert "R-054" not in MH_INCLUDED_RULE_IDS
        assert "R-054" not in MH_REQUIRES_CONFIRMATION_RULE_IDS
        assert [r.id for r in load_mh_approval_rules() if r.id == "R-054"] == []
        with pytest.raises(ValueError, match="Rule R-054 is deferred"):
            _encode("R-054", "APR-052", [], [])

    def test_approval_requires_confirmation(self):
        """The approval itself is ROC/LOW while the rule claims SAFE -
        a second reason no activation could proceed on rule evidence."""
        row = _register_row("approvals.csv", "approval_id", "APR-052")
        assert row["implement_status"] == "REQUIRES_OFFICIAL_CONFIRMATION"
        assert row["rule_ids"] == "R-054"
        assert row["lifecycle_stage"] == "EXPANSION"

    def test_edge_tests_assume_unmodeled_inputs(self):
        et67 = _register_row("edge_tests.csv", "test_id", "ET-067")
        assert et67["rule_id"] == "R-054"
        assert "cert uploaded" in et67["inputs"]
        assert "B2->B2" in et67["inputs"]
        assert "EXEMPT" in et67["expected"]
        et68 = _register_row("edge_tests.csv", "test_id", "ET-068")
        assert "NOT EXEMPT" in et68["expected"]
        et69 = _register_row("edge_tests.csv", "test_id", "ET-069")
        assert et69["expected"] == "UNKNOWN"


class TestFactLinkage:
    """Two conjuncts have facts; four-plus-presupposition do not."""

    def test_exp_facts_present(self):
        assert get_fact_spec(MH_JURISDICTION, "F-EXP-01").value_type.value == (
            "boolean"
        )
        assert get_fact_spec(MH_JURISDICTION, "F-EXP-02").value_type.value == (
            "boolean"
        )

    def test_no_item_scope_fact(self):
        assert not [
            k for k, s in MH_FACTS.items() if "sched" in s.label.lower()
            and "item" in s.label.lower()
        ]
        assert "F-ITEM-01" not in MH_FACTS

    def test_no_certificate_fact(self):
        """No empanelled-auditor / Appendix-XIII / PARIVESH certificate
        fact exists. (F-ELE-02 self-certification voltage and F-BLR-08
        boiler certificate expiry are unrelated labels that merely
        contain 'cert'.)"""
        assert not [
            k
            for k, s in MH_FACTS.items()
            if "auditor" in s.label.lower()
            or "appendix" in s.label.lower()
            or "parivesh" in s.label.lower()
        ]

    def test_no_ocms_fact(self):
        assert not [
            k
            for k, s in MH_FACTS.items()
            if "ocms" in s.label.lower() or "uptime" in s.label.lower()
        ]

    def test_no_category_facts(self):
        assert not [k for k in MH_FACTS if "CAT" in k]
        assert "MPCB_CATEGORY" not in MH_FACTS

    def test_no_prior_ec_holder_fact(self):
        """The exemption presupposes the expanding unit holds a prior EC.
        F-LOC-03 is estate-level coverage (R-005's gate), not
        project-level holder status - and no project-level prior-EC
        fact exists."""
        assert MH_FACTS["F-LOC-03"].label == (
            "estate_holds_prior_EC_covering_units"
        )
        # F-LOC-03 is the estate-coverage gate (R-005), not project-level
        # holder status: its group is LOC and its use is EIA SC. No other
        # prior-EC-holder fact exists.
        assert MH_FACTS["F-LOC-03"].group == "LOC"
        others = [
            k
            for k, s in MH_FACTS.items()
            if k != "F-LOC-03"
            and ("unit" in s.label.lower() or "project" in s.label.lower())
            and ("prior" in s.label.lower() or "holds_ec" in s.label.lower())
        ]
        assert others == []
        assert "F-EC-01" not in MH_FACTS


class TestPartialEncodingFalsification:
    """The maximal facts-only encoding fails OPEN (probe, never pack)."""

    def test_partial_reports_exempt_without_checks(self):
        """DOCUMENTED FALSIFICATION: expansion + no-load-increase alone
        report APPLIES, while the register additionally requires item
        scope, auditor certificate, OCMS >=95%, and no B2 category
        change - none of which the probe can see."""
        facts = {"F-EXP-01": True, "F-EXP-02": False}
        assert evaluate_rule(_partial_r054(), facts).result == "applies"

    def test_unmodeled_conjuncts_invisible(self):
        """Even a known-violated conjunct (B2->A change, no certificate,
        OCMS down) cannot flip the probe: the inputs do not exist."""
        facts = {
            "F-EXP-01": True,
            "F-EXP-02": False,
            "F-CAT-CHANGE": "B2->A",
            "F-OCMS-UPTIME": 40,
        }
        assert evaluate_rule(_partial_r054(), facts).result == "applies"

    def test_no_expansion_vacuous_negative(self):
        """F-EXP-01 FALSE -> DOES_NOT_APPLY reads as 'expansion EC does
        not apply' when there is simply no expansion - the else-branch
        (Form I vs exemption) is not a negative verdict."""
        assert evaluate_rule(
            _partial_r054(), {"F-EXP-01": False, "F-EXP-02": False}
        ).result == "does_not_apply"

    def test_missing_and_unknown_fail_closed(self):
        assert evaluate_rule(_partial_r054(), {}).result == (
            "insufficient_data"
        )
        assert evaluate_rule(
            _partial_r054(), {"F-EXP-01": True, "F-EXP-02": "UNKNOWN"}
        ).result == "insufficient_data"
        assert evaluate_rule(
            _partial_r054(), {"F-EXP-01": True, "F-EXP-02": None}
        ).result == "insufficient_data"


class TestApprovalLevelInversion:
    """APPLIES would mean 'exempt', read as 'approval applies'."""

    def test_no_live_apr052_rule(self):
        evals = evaluate_approval_applicability(
            load_mh_approval_rules(),
            {"F-EXP-01": True, "F-EXP-02": False},
            approval_ids=["APR-052"],
        )
        assert evals == []
        assert summarize_by_approval(evals) == {}

    def test_else_branch_is_not_negative(self):
        """ET-068: B2->A routes to Form I under 7(ii)(a) - a different
        procedure, not DOES_NOT_APPLY. Encoding the exemption as an
        ApprovalRule would erase that routing."""
        row = _register_row("edge_tests.csv", "test_id", "ET-068")
        assert "Form I" in _register_row(
            "rule_register_v5.csv", "rule_id", "R-054"
        )["applicability_conditions"]
        assert "NOT EXEMPT" in row["expected"]


class TestDownstreamContainment:
    """APR-052 touches no loaded edge, document, or SLA."""

    def test_no_loaded_edges_or_docs(self):
        pack = load_regulatory_pack("IN-MH")
        for dep in pack.dependencies:
            assert dep.approval_id != "APR-052"
            assert dep.prerequisite_approval_id != "APR-052"
        for req in pack.document_requirements:
            assert "APR-052" not in set(req.get("approval_ids", []))

    def test_gj_isolation(self):
        gj_ids = {
            r.id for r in load_regulatory_pack(IN_GJ).approval_rules
        }
        assert gj_ids & {"R-054"} == set()
        assert "APR-052" not in {
            r.approval_id for r in load_regulatory_pack(IN_GJ).approval_rules
        }


class TestR054ClosureAudit:
    """Independent closure angles (R-054 triage session)."""

    def test_deferral_entry_is_substantive(self):
        reason = MH_DEFERRED_RULES["R-054"]
        assert "F-EXP-01" in reason
        assert "Appendix XIII" in reason
        assert "OCMS" in reason
        assert "Form I" in reason
        assert "ET-068" in reason
        assert "SRC-001" in reason

    def test_no_overlap_with_r002_small_unit_rule(self):
        """R-002 (active, APR-001, item 5(f) new small units) vs R-054
        (deferred, APR-052, items 2-5 expansions): different approvals,
        different item scopes, different lifecycle questions. No duplicate,
        no shared trigger."""
        row = _register_row("rule_register_v5.csv", "rule_id", "R-002")
        assert row["approval_id"] == "APR-001"
        assert "5(f)" in row["title"]
        r054 = _register_row("rule_register_v5.csv", "rule_id", "R-054")
        assert "2,3,4,5" in r054["applicability_conditions"]
        assert "R-002" in MH_INCLUDED_RULE_IDS
        assert "R-054" in MH_DEFERRED_RULES

    def test_authorities_static_and_verified(self):
        """AUT-001 (MoEFCC/EAC, Cat A) and AUT-002 (SEIAA MH, Cat B) are
        both VERIFIED with no routing condition: authority is not a
        blocker, but the rule lists the pair unresolved, so an APPLIES
        verdict could not name its deciding authority."""
        for aut in ("AUT-001", "AUT-002"):
            row = _register_row("authorities.csv", "authority_id", aut)
            assert row["authority_status"] == "VERIFIED"
        assert "R-054" in MH_DEFERRED_RULES

    def test_expansion_flag_is_strict_boolean(self):
        """F-EXP-01 (BOOL, no UNKNOWN) vs F-EXP-02 (BOOL_OR_UNKNOWN): an
        unknown expansion status has no representation — missing/None is
        the only fail-closed form, and ET-069 pins OCMS-UNKNOWN →
        UNKNOWN for the telemetry conjunct."""
        assert get_fact_spec(MH_JURISDICTION, "F-EXP-01").value_type.value == (
            "boolean"
        )
        assert get_fact_spec(MH_JURISDICTION, "F-EXP-02").value_type.value == (
            "boolean"
        )
        assert (
            get_fact_spec(MH_JURISDICTION, "F-EXP-01").unknown_allowed is False
        )
        assert (
            get_fact_spec(MH_JURISDICTION, "F-EXP-02").unknown_allowed is True
        )

    def test_effective_date_unknown(self):
        """No effective date ('-'/UNKNOWN temporal status): temporal
        queries fail closed; no window can be evaluated."""
        row = _register_row("rule_register_v5.csv", "rule_id", "R-054")
        assert row["effective_date"] == "-"
        assert "UNKNOWN" in row["effective_date_status"]

    def test_untriaged_closure_arithmetic(self):
        """R-054 triaged: it leaves the untriaged remainder, which is a
        subset of the four still-open rules (R-059/071/072/076) — robust
        to parallel sessions triaging further entries."""
        register_ids = {f"R-{i:03d}" for i in range(1, 106)}
        from app.seed.mh.approvals import (
            MH_DO_NOT_IMPLEMENT_RULE_IDS,
            MH_UNKNOWN_RULE_IDS,
        )

        triaged = (
            set(MH_INCLUDED_RULE_IDS)
            | set(MH_DEFERRED_RULES)
            | set(MH_REQUIRES_CONFIRMATION_RULE_IDS)
            | set(MH_DO_NOT_IMPLEMENT_RULE_IDS)
            | set(MH_UNKNOWN_RULE_IDS)
        )
        remainder = register_ids - triaged
        assert "R-054" not in remainder
        assert remainder <= {
            "R-059",
            "R-071",
            "R-072",
            "R-076",
        }

    def test_r021_closure_preserved(self):
        """The R-021 closure this triage once deferred to is complete and
        intact: R-021 stays deferred, counts compose (60 + R-054 = 61)."""
        assert "R-021" in MH_DEFERRED_RULES
        assert len(MH_DEFERRED_RULES) == 61
