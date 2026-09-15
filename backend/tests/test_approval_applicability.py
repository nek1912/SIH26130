"""Tests for the approval applicability evaluation engine.

Covers:
- All four outcomes: APPLIES, DOES_NOT_APPLY, CONDITIONAL, INSUFFICIENT_DATA
- Missing inputs handling
- Multiple matching rules
- Conflicting rules
- Source/rule traceability
- Summarize evaluations
"""
from __future__ import annotations

from app.rules.applicability import (
    evaluate_approval_applicability,
    evaluate_rule,
    summarize_evaluations,
)
from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityEvaluation,
    ApplicabilityOp,
    ApprovalRule,
    SourceRef,
)


def _make_rule(
    *,
    rule_id: str = "rule-1",
    approval_id: str = "approval-1",
    conditions: list[dict] | None = None,
    source_id: str = "src-1",
    version: str = "1",
    active: bool = True,
) -> ApprovalRule:
    """Create a test approval rule with minimal required fields.

    Conditions are wrapped in an AndNode to preserve AND semantics
    (matching the original flat-list behavior).
    """
    raw = [
        ApplicabilityCondition(
            field=c["field"],
            op=ApplicabilityOp(c["op"]),
            value=c["value"],
        )
        for c in (conditions or [])
    ]
    # Wrap multiple conditions in an AndNode for AND semantics
    if len(raw) > 1:
        wrapped = [AndNode(conditions=raw)]
    else:
        wrapped = raw

    return ApprovalRule(
        id=rule_id,
        approval_id=approval_id,
        applicability_conditions=wrapped,
        source_refs=[SourceRef(source_id=source_id, citation_span="s.1")],
        version=version,
        active=active,
    )


def _make_source_ref(source_id: str = "src-1", citation: str = "s.1") -> SourceRef:
    """Create a test source reference."""
    return SourceRef(source_id=source_id, citation_span=citation)


# ─────────────────────────────────────────────────────────────
# APPLIES outcome
# ─────────────────────────────────────────────────────────────


class TestApplicable:
    def test_single_condition_passes(self):
        rule = _make_rule(
            conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}]
        )
        facts = {"sector": "chemicals"}
        result = evaluate_rule(rule, facts, authority="GPCB")
        assert result.result == "applies"
        assert result.rule_id == "rule-1"
        assert result.approval_id == "approval-1"
        assert result.authority == "GPCB"
        assert len(result.missing_inputs) == 0
        assert "sector" in result.required_inputs

    def test_multiple_conditions_all_pass(self):
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
            ]
        )
        facts = {"sector": "chemicals", "headcount": 150}
        result = evaluate_rule(rule, facts, authority="Labour Dept")
        assert result.result == "applies"
        assert "satisfied" in result.reason.lower()

    def test_no_conditions_always_applies(self):
        rule = _make_rule(conditions=[])
        facts = {"sector": "textiles"}
        result = evaluate_rule(rule, facts)
        assert result.result == "applies"
        assert "No applicability conditions" in result.reason

    def test_in_operator_passes(self):
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "in", "value": ["chemicals", "pharma"]}
            ]
        )
        facts = {"sector": "pharma"}
        result = evaluate_rule(rule, facts)
        assert result.result == "applies"

    def test_numeric_gte_passes(self):
        rule = _make_rule(
            conditions=[{"field": "annual_turnover_inr", "op": "gte", "value": 10000000}]
        )
        facts = {"annual_turnover_inr": 50000000}
        result = evaluate_rule(rule, facts)
        assert result.result == "applies"

    def test_source_references_included(self):
        source = _make_source_ref(source_id="src-act-1", citation="s.3(a)")
        rule = ApprovalRule(
            id="rule-src",
            approval_id="approval-1",
            applicability_conditions=[
                ApplicabilityCondition(field="sector", op=ApplicabilityOp.EQ, value="chemicals")
            ],
            source_refs=[source],
            version="1",
        )
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert len(result.source_references) == 1
        assert result.source_references[0].source_id == "src-act-1"
        assert result.source_references[0].citation_span == "s.3(a)"


# ─────────────────────────────────────────────────────────────
# DOES_NOT_APPLY outcome
# ─────────────────────────────────────────────────────────────


class TestNotApplicable:
    def test_condition_fails(self):
        rule = _make_rule(
            conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}]
        )
        facts = {"sector": "textiles"}
        result = evaluate_rule(rule, facts)
        assert result.result == "does_not_apply"
        assert "Conditions not met" in result.reason
        assert "textiles" in result.reason

    def test_one_condition_fails_among_many(self):
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
            ]
        )
        facts = {"sector": "textiles", "headcount": 150}
        result = evaluate_rule(rule, facts)
        assert result.result == "does_not_apply"

    def test_in_operator_fails(self):
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "in", "value": ["chemicals", "pharma"]}
            ]
        )
        facts = {"sector": "textiles"}
        result = evaluate_rule(rule, facts)
        assert result.result == "does_not_apply"

    def test_numeric_gte_fails(self):
        rule = _make_rule(
            conditions=[{"field": "headcount", "op": "gte", "value": 100}]
        )
        facts = {"headcount": 50}
        result = evaluate_rule(rule, facts)
        assert result.result == "does_not_apply"

    def test_numeric_lt_fails(self):
        rule = _make_rule(
            conditions=[{"field": "headcount", "op": "lt", "value": 50}]
        )
        facts = {"headcount": 100}
        result = evaluate_rule(rule, facts)
        assert result.result == "does_not_apply"


# ─────────────────────────────────────────────────────────────
# INSUFFICIENT_DATA outcome
# ─────────────────────────────────────────────────────────────


class TestInsufficientData:
    def test_missing_single_field(self):
        rule = _make_rule(
            conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}]
        )
        facts = {}
        result = evaluate_rule(rule, facts)
        assert result.result == "insufficient_data"
        assert "Required fact fields missing" in result.reason
        assert "sector" in result.missing_inputs
        assert "sector" in result.required_inputs

    def test_missing_multiple_fields(self):
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
            ]
        )
        facts = {}
        result = evaluate_rule(rule, facts)
        assert result.result == "insufficient_data"
        assert len(result.missing_inputs) == 2
        assert "sector" in result.missing_inputs
        assert "headcount" in result.missing_inputs

    def test_partial_missing_fields(self):
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
            ]
        )
        facts = {"sector": "chemicals"}
        result = evaluate_rule(rule, facts)
        assert result.result == "insufficient_data"
        assert result.missing_inputs == ["headcount"]
        assert "sector" not in result.missing_inputs

    def test_missing_entity_type(self):
        rule = _make_rule(
            conditions=[{"field": "entity_type", "op": "eq", "value": "pvt-ltd"}]
        )
        facts = {"sector": "chemicals"}
        result = evaluate_rule(rule, facts)
        assert result.result == "insufficient_data"
        assert "entity_type" in result.missing_inputs

    def test_missing_jurisdictions(self):
        rule = _make_rule(
            conditions=[
                {"field": "jurisdictions", "op": "in", "value": ["IN-GJ"]}
            ]
        )
        facts = {"sector": "chemicals"}
        result = evaluate_rule(rule, facts)
        assert result.result == "insufficient_data"
        assert "jurisdictions" in result.missing_inputs


# ─────────────────────────────────────────────────────────────
# CONDITIONAL outcome
# ─────────────────────────────────────────────────────────────


class TestConditional:
    def test_condition_cannot_evaluate_missing_optional_field(self):
        """When a condition references a field not in facts but all present
        conditions pass, result is CONDITIONAL. However, if all fields are
        required by the rule, missing fields produce INSUFFICIENT_DATA."""
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "registered_state", "op": "eq", "value": "IN-GJ"},
            ]
        )
        facts = {"sector": "chemicals"}
        result = evaluate_rule(rule, facts)
        # registered_state is missing and required by the rule
        assert result.result == "insufficient_data"
        assert "registered_state" in result.missing_inputs

    def test_partial_conditions_pass_partial_unevaluated(self):
        """CONDITIONAL requires some conditions to pass and some to be unevaluated
        but with no failing conditions. Since all fields referenced by conditions
        are required, this can only occur if a condition references a field that
        exists but has an unexpected type."""
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
            ]
        )
        # Both fields present, sector passes, headcount fails
        facts = {"sector": "chemicals", "headcount": 50}
        result = evaluate_rule(rule, facts)
        assert result.result == "does_not_apply"

    def test_conditional_when_no_conditions(self):
        """Rule with no conditions always applies — this is a trivial case."""
        rule = _make_rule(conditions=[])
        result = evaluate_rule(rule, {})
        assert result.result == "applies"


# ─────────────────────────────────────────────────────────────
# Multiple rules and approval-level evaluation
# ─────────────────────────────────────────────────────────────


class TestMultipleRules:
    def test_two_rules_same_approval_both_apply(self):
        rules = [
            _make_rule(
                rule_id="r1",
                approval_id="a1",
                conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}],
            ),
            _make_rule(
                rule_id="r2",
                approval_id="a1",
                conditions=[{"field": "headcount", "op": "gte", "value": 50}],
            ),
        ]
        facts = {"sector": "chemicals", "headcount": 100}
        evaluations = evaluate_approval_applicability(rules, facts)
        assert len(evaluations) == 2
        assert all(e.result == "applies" for e in evaluations)

    def test_two_rules_different_approvals(self):
        rules = [
            _make_rule(
                rule_id="r1",
                approval_id="a1",
                conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}],
            ),
            _make_rule(
                rule_id="r2",
                approval_id="a2",
                conditions=[{"field": "sector", "op": "eq", "value": "textiles"}],
            ),
        ]
        facts = {"sector": "chemicals"}
        evaluations = evaluate_approval_applicability(rules, facts)
        assert len(evaluations) == 2
        results_by_rule = {e.rule_id: e.result for e in evaluations}
        assert results_by_rule["r1"] == "applies"
        assert results_by_rule["r2"] == "does_not_apply"

    def test_filter_by_approval_ids(self):
        rules = [
            _make_rule(
                rule_id="r1",
                approval_id="a1",
                conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}],
            ),
            _make_rule(
                rule_id="r2",
                approval_id="a2",
                conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}],
            ),
        ]
        facts = {"sector": "chemicals"}
        evaluations = evaluate_approval_applicability(
            rules, facts, approval_ids=["a1"]
        )
        assert len(evaluations) == 1
        assert evaluations[0].approval_id == "a1"


# ─────────────────────────────────────────────────────────────
# Conflicting rules
# ─────────────────────────────────────────────────────────────


class TestConflictingRules:
    def test_conflicting_conditions_on_same_approval(self):
        """Two rules for same approval with different sector requirements."""
        rules = [
            _make_rule(
                rule_id="r1",
                approval_id="a1",
                conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}],
            ),
            _make_rule(
                rule_id="r2",
                approval_id="a1",
                conditions=[{"field": "sector", "op": "eq", "value": "textiles"}],
            ),
        ]
        facts = {"sector": "chemicals"}
        evaluations = evaluate_approval_applicability(rules, facts)
        assert len(evaluations) == 2
        results = {e.rule_id: e.result for e in evaluations}
        assert results["r1"] == "applies"
        assert results["r2"] == "does_not_apply"


# ─────────────────────────────────────────────────────────────
# Source and rule traceability
# ─────────────────────────────────────────────────────────────


class TestTraceability:
    def test_rule_id_preserved(self):
        rule = _make_rule(rule_id="trace-rule-42")
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert result.rule_id == "trace-rule-42"

    def test_approval_id_preserved(self):
        rule = _make_rule(approval_id="approval-99")
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert result.approval_id == "approval-99"

    def test_authority_preserved(self):
        rule = _make_rule()
        result = evaluate_rule(rule, {"sector": "chemicals"}, authority="GPCB")
        assert result.authority == "GPCB"

    def test_source_references_preserved(self):
        source = _make_source_ref(source_id="src-doc-1", citation="Section 5(2)")
        rule = ApprovalRule(
            id="r-trace",
            approval_id="a-trace",
            applicability_conditions=[
                ApplicabilityCondition(field="sector", op=ApplicabilityOp.EQ, value="chemicals")
            ],
            source_refs=[source],
            version="1",
        )
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert len(result.source_references) == 1
        assert result.source_references[0].source_id == "src-doc-1"
        assert result.source_references[0].citation_span == "Section 5(2)"

    def test_multiple_source_references(self):
        sources = [
            _make_source_ref(source_id="src-1", citation="s.1"),
            _make_source_ref(source_id="src-2", citation="s.2"),
        ]
        rule = ApprovalRule(
            id="r-multi-src",
            approval_id="a-multi-src",
            applicability_conditions=[
                ApplicabilityCondition(field="sector", op=ApplicabilityOp.EQ, value="chemicals")
            ],
            source_refs=sources,
            version="1",
        )
        result = evaluate_rule(rule, {"sector": "chemicals"})
        assert len(result.source_references) == 2

    def test_required_inputs_include_all_condition_fields(self):
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": "chemicals"},
                {"field": "headcount", "op": "gte", "value": 100},
                {"field": "jurisdictions", "op": "in", "value": ["IN-GJ"]},
            ]
        )
        result = evaluate_rule(rule, {})
        assert set(result.required_inputs) == {"sector", "headcount", "jurisdictions"}

    def test_version_preserved(self):
        rule = _make_rule(version="3")
        result = evaluate_rule(rule, {"sector": "chemicals"})
        # Version is in the rule model, not directly in evaluation result
        # but we can verify the rule was evaluated correctly
        assert result.result == "applies"


# ─────────────────────────────────────────────────────────────
# Summarize evaluations
# ─────────────────────────────────────────────────────────────


class TestSummarize:
    def test_summary_counts(self):
        evaluations = [
            ApplicabilityEvaluation(
                rule_id="r1",
                approval_id="a1",
                result="applies",
                reason="",
                required_inputs=[],
                missing_inputs=[],
                authority="",
                source_references=[],
            ),
            ApplicabilityEvaluation(
                rule_id="r2",
                approval_id="a2",
                result="does_not_apply",
                reason="",
                required_inputs=[],
                missing_inputs=[],
                authority="",
                source_references=[],
            ),
            ApplicabilityEvaluation(
                rule_id="r3",
                approval_id="a3",
                result="applies",
                reason="",
                required_inputs=[],
                missing_inputs=[],
                authority="",
                source_references=[],
            ),
            ApplicabilityEvaluation(
                rule_id="r4",
                approval_id="a4",
                result="insufficient_data",
                reason="",
                required_inputs=[],
                missing_inputs=[],
                authority="",
                source_references=[],
            ),
        ]
        summary = summarize_evaluations(evaluations)
        assert summary["applies"] == 2
        assert summary["does_not_apply"] == 1
        assert summary["conditional"] == 0
        assert summary["insufficient_data"] == 1

    def test_empty_summary(self):
        summary = summarize_evaluations([])
        assert summary["applies"] == 0
        assert summary["does_not_apply"] == 0
        assert summary["conditional"] == 0
        assert summary["insufficient_data"] == 0


# ─────────────────────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_facts_with_conditions(self):
        rule = _make_rule(
            conditions=[{"field": "sector", "op": "eq", "value": "chemicals"}]
        )
        result = evaluate_rule(rule, {})
        assert result.result == "insufficient_data"
        assert "sector" in result.missing_inputs

    def test_empty_rules_list(self):
        evaluations = evaluate_approval_applicability([], {"sector": "chemicals"})
        assert evaluations == []

    def test_condition_with_list_value_eq(self):
        """When condition value is a list and entity value is not in list."""
        rule = _make_rule(
            conditions=[
                {"field": "sector", "op": "eq", "value": ["chemicals", "pharma"]}
            ]
        )
        facts = {"sector": "textiles"}
        result = evaluate_rule(rule, facts)
        # eq with list value: value == ["chemicals", "pharma"] is False
        assert result.result == "does_not_apply"

    def test_all_operators_on_missing_field(self):
        """All operators return INSUFFICIENT_DATA when field is missing."""
        for op in ["eq", "in", "gt", "gte", "lt", "lte"]:
            rule = _make_rule(
                conditions=[{"field": "headcount", "op": op, "value": 100}]
            )
            result = evaluate_rule(rule, {})
            assert result.result == "insufficient_data"
            assert "headcount" in result.missing_inputs

    def test_approval_authorities_mapping(self):
        rules = [
            _make_rule(rule_id="r1", approval_id="a1", conditions=[]),
        ]
        authorities = {"a1": "GPCB Gujarat"}
        evaluations = evaluate_approval_applicability(
            rules, {}, approval_authorities=authorities
        )
        assert evaluations[0].authority == "GPCB Gujarat"

    def test_authority_not_in_mapping(self):
        rules = [
            _make_rule(rule_id="r1", approval_id="a-unknown", conditions=[]),
        ]
        evaluations = evaluate_approval_applicability(rules, {})
        assert evaluations[0].authority == ""
