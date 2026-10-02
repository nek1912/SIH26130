"""Tests for Maharashtra HW Authorization Content-Chain Audit (R-018, R-096).

Active-rule audit: R-018 and R-096 both target APR-010 (MPCB hazardous
waste authorisation, AUT-003). The burden of proof is on the current
implementation — these tests try to falsify it.

- R-018: HW_AUTH := F-HW-01 == TRUE (broad generation trigger, T1 SRC-013
  r.6(1), EXACT 2016-04-04). Classification under audit: A (safe as
  implemented).
- R-096: HW_SCH2_TEST over F-HW-04 lab characteristics (operator ANY, T2
  SRC-120 Schedule II, EXACT 2016-04-04). Classification: B (safe with
  bounded limitations: UNK-034 threshold currency, [] supply discipline,
  lab-conclusion token discipline).

Register identity is verified against the CURRENT CSVs at runtime (same
pattern as test_mh_cto_renewal.py / test_mh_consent_category_chain.py);
engine behavior is asserted against the live rules. No pack, engine (beyond
one surgical fail-closed fix), fact, or source changes except the
list-embedded-UNKNOWN correction in _evaluate_leaf, which this suite pins.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pytest

from app.rules.applicability import (
    evaluate_rule,
    summarize_by_approval,
)
from app.rules.dependency_engine import ReadinessStatus, evaluate_readiness
from app.rules.facts import (
    MH_FACTS,
    FactValidationError,
    FactValueType,
    get_fact_spec,
    validate_fact_value,
)
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
    LiteralNode,
    NotNode,
    OrNode,
)
from app.seed.mh.approvals import (
    MH_DEFERRED_RULES,
    MH_INCLUDED_RULE_IDS,
    MH_REQUIRES_CONFIRMATION_RULE_IDS,
    load_mh_approval_rules,
)
from app.seed.pack import DEFAULT_JURISDICTION, IN_GJ, load_regulatory_pack

HW_CHAIN_RULES: frozenset[str] = frozenset({
    "R-018",
    "R-096",
})

SCHEDULE_II_TOKENS: frozenset[str] = frozenset({
    "CLASS_A", "CLASS_B", "CLASS_C1", "CLASS_C2", "CLASS_C3",
    "CLASS_A_TCLP", "CLASS_C1_FLAMMABLE", "CLASS_C2_CORROSIVE",
    "CLASS_C3_REACTIVE", "HAZARDOUS", "MEETS_SCHEDULE_II",
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


def _live_rule(rule_id: str) -> ApprovalRule:
    """Fetch a live rule from the MH pack builders."""
    return next(r for r in load_mh_approval_rules() if r.id == rule_id)


def _leaf_fields(node: object) -> set[str]:
    if isinstance(node, ApplicabilityCondition):
        return {node.field}
    if isinstance(node, (AndNode, OrNode)):
        out: set[str] = set()
        for child in node.conditions:
            out |= _leaf_fields(child)
        return out
    if isinstance(node, NotNode):
        return _leaf_fields(node.condition)
    if isinstance(node, LiteralNode):
        return set()
    raise AssertionError(f"unknown node {node!r}")


def _approval_result(facts: dict, evaluation_date: date | None = None) -> str:
    """APR-010 verdict across both live chain rules (priority aggregation)."""
    rules = [_live_rule("R-018"), _live_rule("R-096")]
    evals = [
        evaluate_rule(r, facts, evaluation_date=evaluation_date) for r in rules
    ]
    return summarize_by_approval(evals)["APR-010"].result


class TestBaselineCounts:
    """Confirm the repository baseline before asserting chain effects."""

    def test_default_jurisdiction_is_gj(self):
        assert DEFAULT_JURISDICTION == "IN-GJ"

    def test_mh_active_rule_count_is_26(self):
        assert len(load_mh_approval_rules()) == 26

    def test_mh_deferred_count_is_61(self):
        """59 at HW-audit time + R-021 + R-054 (R-054 closure audit)."""
        assert len(MH_DEFERRED_RULES) == 61

    def test_mh_confirmation_count_is_26(self):
        assert len(MH_REQUIRES_CONFIRMATION_RULE_IDS) == 26

    def test_gj_active_rule_count_is_19(self):
        assert len(load_regulatory_pack(IN_GJ).approval_rules) == 19

    def test_mh_fact_count_is_128(self):
        assert len(MH_FACTS) == 128


class TestExecutableIdentity:
    """Field-by-field identity from the CURRENT registers."""

    def test_r018_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-018")
        assert row["approval_id"] == "APR-010"
        assert row["title"] == "Hazardous waste authorisation (Form 1 -> Form 2)"
        assert row["authority"] == "AUT-003"
        assert row["jurisdiction"] == "STATEWIDE"
        assert row["applicability_conditions"] == "HW_AUTH := F-HW-01 == TRUE"
        assert row["required_inputs"] == "F-HW-01"
        assert row["source_id"] == "SRC-013"
        assert row["source_tier"] == "T1"
        assert row["effective_date"] == "2016-04-04"
        assert row["effective_date_status"] == "EXACT_DATE"
        assert row["status"] == "VERIFIED_CONDITIONAL"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert row["dependencies"] == "APR-008;APR-009"
        assert "F-HW-02 (supplied), never inferred" in row["notes"]

    def test_r096_register_identity(self):
        row = _register_row("rule_register_v5.csv", "rule_id", "R-096")
        assert row["approval_id"] == "APR-010"
        assert row["authority"] == "AUT-003"
        assert "F-HW-04" in row["required_inputs"]
        assert "without lab data -> INSUFFICIENT_DATA" in row["applicability_conditions"]
        assert row["source_id"] == "SRC-120"
        assert row["source_tier"] == "T2"
        assert row["effective_date"] == "2016-04-04"
        assert row["implementation_status"] == "IMPLEMENTATION_SAFE"
        assert "UNK-034" in row["notes"]

    def test_r096_operator_is_any_in_rules_csv(self):
        row = _register_row("rules.csv", "rule_id", "R-096")
        assert row["operator"] == "ANY"
        assert "Sch II" in row["threshold"]
        assert "HOWM Rules 2016 r.3(17), Schedule II" in row["legal_basis"]

    def test_r018_operator_is_eq_in_rules_csv(self):
        row = _register_row("rules.csv", "rule_id", "R-018")
        assert row["operator"] == "=="
        assert row["facts"] == "F-HW-01"
        assert "HOWM 2016 r.6" in row["legal_basis"]

    def test_apr010_register_identity(self):
        row = _register_row("approvals.csv", "approval_id", "APR-010")
        assert row["record_class"] == "APPROVAL"
        assert row["applicability_class"] == "ACTIVITY_DEPENDENT"
        assert row["authority_id"] == "AUT-003"
        assert row["lifecycle_stage"] == "PRE_OPERATION"
        assert row["trigger_event"] == "Generation/handling of HW"
        assert row["precondition"] == "Consent"
        assert "R-018" in row["rule_ids"]

    def test_hw_fact_identities(self):
        f01 = _register_row("facts.csv", "fact_id", "F-HW-01")
        assert f01["type"] == "BOOL_OR_UNKNOWN"
        f04 = _register_row("facts.csv", "fact_id", "F-HW-04")
        assert f04["type"] == "LIST_OR_UNKNOWN"
        assert "never coerced to FALSE" in f04["notes"]
        f02 = _register_row("facts.csv", "fact_id", "F-HW-02")
        assert "must be supplied, not inferred" in f02["notes"]

    def test_live_implementation_matches_register(self):
        r018 = _live_rule("R-018")
        assert r018.approval_id == "APR-010"
        assert r018.effective_from == date(2016, 4, 4)
        assert r018.source_refs[0].source_id == "SRC-013"
        r096 = _live_rule("R-096")
        assert r096.approval_id == "APR-010"
        assert r096.effective_from == date(2016, 4, 4)
        assert r096.source_refs[0].source_id == "SRC-120"
        assert set(r096.applicability_conditions[0].value) == set(SCHEDULE_II_TOKENS)

    def test_chain_active_not_deferred_or_gated(self):
        for rule_id in HW_CHAIN_RULES:
            assert rule_id in MH_INCLUDED_RULE_IDS
            assert rule_id not in MH_DEFERRED_RULES
            assert rule_id not in MH_REQUIRES_CONFIRMATION_RULE_IDS


class TestChainReconstruction:
    """What each rule contributes; no hidden composition."""

    def test_r018_is_broad_generation_trigger(self):
        fields: set[str] = set()
        for cond in _live_rule("R-018").applicability_conditions:
            fields |= _leaf_fields(cond)
        assert fields == {"F-HW-01"}

    def test_r096_is_independent_characteristic_trigger(self):
        fields: set[str] = set()
        for cond in _live_rule("R-096").applicability_conditions:
            fields |= _leaf_fields(cond)
        assert fields == {"F-HW-04"}

    def test_no_shared_inputs_no_composition(self):
        """Disjoint input sets and no rule-reference fields: the engine
        represents the relationship only as two independent triggers aggregated
        by APPLIES-first priority — which the register supports (either trigger
        suffices for authorisation)."""
        assert {"F-HW-01"} & {"F-HW-04"} == set()
        for rule_id in HW_CHAIN_RULES:
            for cond in _live_rule(rule_id).applicability_conditions:
                for field in _leaf_fields(cond):
                    assert field.startswith("F-"), (rule_id, field)

    def test_either_trigger_applies_approval(self):
        assert _approval_result({"F-HW-01": True, "F-HW-04": []}) == "applies"
        assert _approval_result(
            {"F-HW-01": False, "F-HW-04": ["CLASS_A"]}
        ) == "applies"

    def test_contradiction_resolves_fail_safe(self):
        """Generation denied but lab positive: APPLIES wins (authorisation
        required; the contradiction is MPCB content business, not a negation)."""
        assert _approval_result(
            {"F-HW-01": False, "F-HW-04": ["CLASS_B"]}
        ) == "applies"

    def test_negative_lab_does_not_cancel_generation_flag(self):
        assert _approval_result(
            {"F-HW-01": True, "F-HW-04": ["NON_HAZARDOUS"]}
        ) == "applies"


class TestR018ActiveSafety:
    """Falsification attempts against the broad trigger."""

    def test_true_applies(self):
        assert evaluate_rule(_live_rule("R-018"), {"F-HW-01": True}).result == "applies"

    def test_false_does_not_apply(self):
        res = evaluate_rule(_live_rule("R-018"), {"F-HW-01": False})
        assert res.result == "does_not_apply"

    def test_unknown_fails_closed_per_et054(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-054")
        assert row["rule_id"] == "R-018"
        assert "HW_AUTH=UNKNOWN" in row["expected"]
        assert evaluate_rule(_live_rule("R-018"), {"F-HW-01": None}).result == (
            "insufficient_data"
        )
        assert evaluate_rule(_live_rule("R-018"), {}).result == "insufficient_data"

    def test_effective_window_exact(self):
        before = evaluate_rule(
            _live_rule("R-018"), {"F-HW-01": True},
            evaluation_date=date(2016, 4, 3),
        )
        assert before.result == "does_not_apply"
        assert "not in force" in before.reason
        on_date = evaluate_rule(
            _live_rule("R-018"), {"F-HW-01": True},
            evaluation_date=date(2016, 4, 4),
        )
        assert on_date.result == "applies"

    def test_t1_source_resolves_in_corpus(self):
        corpus = {s.id for s in load_regulatory_pack("IN-MH").sources}
        assert "SRC-013" in corpus

    def test_generation_without_stream_detail_still_applies(self):
        """Register design: generation triggers authorisation; stream detail
        (F-HW-02 supplied entries) is content for Form 1, not an
        applicability conjunct. The code correctly omits F-HW-02."""
        assert _approval_result({"F-HW-01": True}) == "applies"


class TestR096ActiveSafety:
    """Falsification attempts against the characteristic trigger."""

    def test_characteristic_tokens_apply(self):
        for token in sorted(SCHEDULE_II_TOKENS):
            res = evaluate_rule(_live_rule("R-096"), {"F-HW-04": [token]})
            assert res.result == "applies", token

    def test_summary_tokens_are_lab_conclusions(self):
        """HAZARDOUS / MEETS_SCHEDULE_II are only valid as lab-reported
        conclusions inside F-HW-04 (label: lab_results_for_Schedule_II_tests).
        Unlisted, missing, or UNKNOWN inputs below prove no lab-free path
        to APPLIES exists."""
        spec = get_fact_spec("IN-MH", "F-HW-04")
        assert spec.label == "lab_results_for_Schedule_II_tests"

    def test_empty_list_does_not_apply(self):
        """[] means no positive findings recorded. Supply discipline: an
        untested waste must be sent as missing/UNKNOWN (ET-129), never []."""
        res = evaluate_rule(_live_rule("R-096"), {"F-HW-04": []})
        assert res.result == "does_not_apply"

    def test_unlisted_waste_without_lab_data_per_et129(self):
        row = _register_row("edge_tests.csv", "test_id", "ET-129")
        assert row["rule_id"] == "R-096"
        assert row["expected"] == "INSUFFICIENT_DATA"
        assert evaluate_rule(_live_rule("R-096"), {}).result == "insufficient_data"
        assert evaluate_rule(_live_rule("R-096"), {"F-HW-04": None}).result == (
            "insufficient_data"
        )
        assert evaluate_rule(_live_rule("R-096"), {"F-HW-04": "UNKNOWN"}).result == (
            "insufficient_data"
        )

    def test_list_embedded_unknown_fails_closed(self):
        """Surgical fix under audit: ['UNKNOWN'] previously coerced to FALSE,
        contradicting the register's 'never coerced to FALSE'. Now
        INSUFFICIENT_DATA; established positives still stand (next test)."""
        res = evaluate_rule(_live_rule("R-096"), {"F-HW-04": ["UNKNOWN"]})
        assert res.result == "insufficient_data"
        assert res.result != "does_not_apply"

    def test_positive_with_unknown_element_still_applies(self):
        """Fail-safe direction preserved: a concluded characteristic is not
        unseated by an accompanying unknown element."""
        res = evaluate_rule(_live_rule("R-096"), {"F-HW-04": ["CLASS_A", "UNKNOWN"]})
        assert res.result == "applies"

    def test_clean_results_do_not_apply(self):
        res = evaluate_rule(
            _live_rule("R-096"), {"F-HW-04": ["NON_HAZARDOUS", "WITHIN_LIMITS"]}
        )
        assert res.result == "does_not_apply"

    def test_effective_window_exact(self):
        before = evaluate_rule(
            _live_rule("R-096"), {"F-HW-04": ["CLASS_A"]},
            evaluation_date=date(2016, 4, 3),
        )
        assert before.result == "does_not_apply"
        on_date = evaluate_rule(
            _live_rule("R-096"), {"F-HW-04": ["CLASS_A"]},
            evaluation_date=date(2016, 4, 4),
        )
        assert on_date.result == "applies"

    def test_t2_source_resolves_with_currency_caveat(self):
        corpus = {s.id for s in load_regulatory_pack("IN-MH").sources}
        assert "SRC-120" in corpus
        row = _register_row("sources.csv", "source_id", "SRC-120")
        assert row["tier"] == "T2"
        assert "Post-2016 amendments" in row["what_the_source_does_not_prove"]


class TestPerStreamMultiStream:
    """ANY semantics; no MAX/ALL/EXISTS assumed."""

    def test_any_positive_triggers(self):
        res = evaluate_rule(
            _live_rule("R-096"), {"F-HW-04": ["NON_HAZARDOUS", "CLASS_C1"]}
        )
        assert res.result == "applies"

    def test_all_clean_does_not_apply(self):
        res = evaluate_rule(
            _live_rule("R-096"), {"F-HW-04": ["NON_HAZARDOUS", "WITHIN_LIMITS"]}
        )
        assert res.result == "does_not_apply"

    def test_stream_entries_are_content_not_predicate(self):
        """F-HW-02 (per-stream schedule/entry objects, MPCB/consultant
        determined) appears in no chain predicate: content stays out of
        applicability by construction."""
        for rule_id in HW_CHAIN_RULES:
            for cond in _live_rule(rule_id).applicability_conditions:
                assert "F-HW-02" not in _leaf_fields(cond)

    def test_no_aggregation_operator_in_engine(self):
        assert [op.value for op in ApplicabilityOp] == [
            "eq", "in", "gte", "lte", "gt", "lt",
        ]

    def test_hw_streams_table_needs_occupier_facts(self):
        """hw_streams.csv triggers require occupier-declared process+waste
        facts; the table is reference, not an inference engine."""
        csv_dir = _get_csv_dir()
        with open(csv_dir / "hw_streams.csv", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 54
        assert "occupier-declared facts" in rows[0]["trigger"]


class TestApprovalLevelFailClosed:
    """summarize_by_approval priority is fail-safe for this pair."""

    def test_both_missing_is_insufficient(self):
        assert _approval_result({}) == "insufficient_data"

    def test_false_generation_with_missing_lab(self):
        """No generation → no authorisation even without lab data: the only
        DOES_NOT_APPLY-over-INSUFFICIENT_DATA masking, and it is sound."""
        res = _approval_result({"F-HW-01": False, "F-HW-04": None})
        assert res == "does_not_apply"

    def test_unknown_generation_with_empty_lab(self):
        """F-HW-01 UNKNOWN + [] lab → DOES_NOT_APPLY via R-096's recorded
        negative ([] = no positive findings recorded). Supply discipline:
        an untested waste must be sent as missing/UNKNOWN (then the verdict
        is INSUFFICIENT_DATA), never []."""
        res = _approval_result({"F-HW-01": None, "F-HW-04": []})
        assert res == "does_not_apply"
        assert _approval_result({"F-HW-01": None}) == "insufficient_data"

    def test_explicit_no_waste_is_negative(self):
        assert _approval_result(
            {"F-HW-01": False, "F-HW-04": ["NON_HAZARDOUS"]}
        ) == "does_not_apply"


class TestDependencyPropagation:
    """Unknown HW authorisation must block downstream, never satisfy."""

    def _graph(self, applicability: str, obtained: set | None = None,
                 prereq_state: str = "insufficient_data"):
        # Engine contract uses lowercase result values
        # (ApprovalResult.*.value: applies / does_not_apply / conditional /
        # insufficient_data); anything else falls into the blocking branch.
        # obtained satisfies only applies-state prereqs: unknown prereqs
        # block even when claimed obtained (fail-closed).
        mh_pack = load_regulatory_pack("IN-MH")
        return evaluate_readiness(
            mh_pack.dependencies,
            {"APR-010": applicability, "APR-008": prereq_state,
             "APR-009": prereq_state},
            obtained=obtained if obtained is not None else set(),
        )

    def test_applies_blocked_until_consent_obtained(self):
        graph = self._graph("applies")
        assert graph.readiness["APR-010"].readiness == ReadinessStatus.BLOCKED
        assert set(graph.readiness["APR-010"].blocking_prerequisites) == {
            "APR-008", "APR-009",
        }

    def test_insufficient_consent_blocks(self):
        """An unevaluated approval (own verdict INSUFFICIENT_DATA) is
        PENDING_EVALUATION — never READY, never satisfied by prereqs."""
        graph = self._graph("insufficient_data")
        assert graph.readiness["APR-010"].readiness == ReadinessStatus.PENDING_EVALUATION
        assert graph.readiness["APR-010"].readiness != ReadinessStatus.READY

    def test_obtained_consent_unblocks(self):
        graph = self._graph("applies", obtained={"APR-008", "APR-009"},
                            prereq_state="applies")
        assert graph.readiness["APR-010"].readiness == ReadinessStatus.READY

    def test_obtained_does_not_cure_unknown_prereq(self):
        """Fail-closed: even claimed-obtained consent with unknown
        applicability still blocks downstream authorisation."""
        graph = self._graph("applies", obtained={"APR-008", "APR-009"})
        assert graph.readiness["APR-010"].readiness == ReadinessStatus.BLOCKED

    def test_ready_never_without_obtained(self):
        """Fail-closed by absence (inventory pin): CTE/CTO have no active
        rules, so satisfaction comes only from the obtained set."""
        active_approvals = {r.approval_id for r in load_mh_approval_rules()}
        assert "APR-008" not in active_approvals
        assert "APR-009" not in active_approvals
        graph = self._graph("APPLIES")
        assert graph.readiness["APR-010"].readiness != ReadinessStatus.READY


class TestDocumentsStayContent:
    """DOC-001/002/003 + Forms live in the document layer, not predicates."""

    def test_apr010_document_requirements_loaded(self):
        mh_pack = load_regulatory_pack("IN-MH")
        keys = {r["requirement_key"]
                for r in mh_pack.get_requirements_for_approval("APR-010")}
        assert {"DOC-001", "DOC-002", "DOC-003"} <= keys

    def test_no_doc_field_in_predicates(self):
        for rule_id in HW_CHAIN_RULES:
            for cond in _live_rule(rule_id).applicability_conditions:
                for field in _leaf_fields(cond):
                    assert not field.startswith("DOC-"), (rule_id, field)

    def test_sla_and_portal_are_display_only(self):
        mh_pack = load_regulatory_pack("IN-MH")
        assert "SLA-004" in {s.sla_id for s in mh_pack.sla_records}
        assert mh_pack.get_portal_entry("APR-010") is not None
        assert mh_pack.approval_authorities["APR-010"] == "AUT-003"


class TestFactDiscipline:
    """No convenient facts; no GJ leakage."""

    def test_hw_fact_specs(self):
        assert get_fact_spec("IN-MH", "F-HW-01").value_type == FactValueType.BOOLEAN
        assert get_fact_spec("IN-MH", "F-HW-04").value_type == FactValueType.LIST
        assert get_fact_spec("IN-MH", "F-HW-04").unknown_allowed is True

    def test_invalid_hw_values_rejected(self):
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-HW-01", "YES")
        with pytest.raises(FactValidationError):
            validate_fact_value("IN-MH", "F-HW-04", 42)

    def test_none_always_valid(self):
        validate_fact_value("IN-MH", "F-HW-01", None)
        validate_fact_value("IN-MH", "F-HW-04", None)

    def test_gj_namespace_rejects_hw_facts(self):
        for fid, value in (("F-HW-01", True), ("F-HW-04", ["CLASS_A"])):
            with pytest.raises(FactValidationError) as exc:
                validate_fact_value("IN-GJ", fid, value)
            assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH

    def test_no_consent_chain_regression(self):
        """Parallel-work rule: R-013/R-014/R-015/R-017 untouched."""
        for rule_id in ("R-013", "R-014", "R-015", "R-017"):
            assert rule_id in MH_DEFERRED_RULES
            assert rule_id not in MH_INCLUDED_RULE_IDS


class TestJurisdictionIsolation:
    """IN-MH chain work must not leak into IN-GJ."""

    def test_gj_pack_untouched(self):
        gj_pack = load_regulatory_pack(IN_GJ)
        assert len(gj_pack.approval_rules) == 19
        gj_ids = {r.id for r in gj_pack.approval_rules}
        assert not (HW_CHAIN_RULES & gj_ids)

    def test_gj_approvals_untouched(self):
        gj_approval_ids = {r.approval_id
                           for r in load_regulatory_pack(IN_GJ).approval_rules}
        assert "APR-010" not in gj_approval_ids

    def test_mh_active_unchanged(self):
        assert len(load_mh_approval_rules()) == 26


class TestClassification:
    """R-018 A; R-096 B (bounded). Both stay active."""

    def test_r018_is_class_a(self):
        assert "R-018" in MH_INCLUDED_RULE_IDS

    def test_r096_is_class_b(self):
        assert "R-096" in MH_INCLUDED_RULE_IDS

    def test_zero_status_changes(self):
        assert len(load_mh_approval_rules()) == 26
        assert len(MH_DEFERRED_RULES) == 61
        assert len(MH_REQUIRES_CONFIRMATION_RULE_IDS) == 26
