"""Tests for the form condition evaluator."""
from __future__ import annotations

from app.forms.conditions import evaluate_condition, get_required_documents, get_visible_fields
from app.forms.models import ConditionalRule


class TestEvaluateCondition:
    def test_eq_match(self):
        rule = ConditionalRule(field="status", operator="eq", value="active")
        assert evaluate_condition(rule, {"status": "active"}) is True

    def test_eq_no_match(self):
        rule = ConditionalRule(field="status", operator="eq", value="active")
        assert evaluate_condition(rule, {"status": "inactive"}) is False

    def test_eq_missing_field(self):
        rule = ConditionalRule(field="status", operator="eq", value="active")
        assert evaluate_condition(rule, {}) is False

    def test_neq(self):
        rule = ConditionalRule(field="status", operator="neq", value="active")
        assert evaluate_condition(rule, {"status": "inactive"}) is True
        assert evaluate_condition(rule, {"status": "active"}) is False

    def test_in_match(self):
        rule = ConditionalRule(field="type", operator="in", value=["a", "b", "c"])
        assert evaluate_condition(rule, {"type": "b"}) is True

    def test_in_no_match(self):
        rule = ConditionalRule(field="type", operator="in", value=["a", "b"])
        assert evaluate_condition(rule, {"type": "z"}) is False

    def test_in_non_list_value(self):
        rule = ConditionalRule(field="type", operator="in", value="abc")
        assert evaluate_condition(rule, {"type": "a"}) is False

    def test_not_in(self):
        rule = ConditionalRule(field="type", operator="not_in", value=["a", "b"])
        assert evaluate_condition(rule, {"type": "c"}) is True
        assert evaluate_condition(rule, {"type": "a"}) is False

    def test_gt(self):
        rule = ConditionalRule(field="count", operator="gt", value=10)
        assert evaluate_condition(rule, {"count": 11}) is True
        assert evaluate_condition(rule, {"count": 10}) is False
        assert evaluate_condition(rule, {"count": 9}) is False

    def test_gt_non_numeric(self):
        rule = ConditionalRule(field="count", operator="gt", value=10)
        assert evaluate_condition(rule, {"count": "abc"}) is False

    def test_lt(self):
        rule = ConditionalRule(field="count", operator="lt", value=10)
        assert evaluate_condition(rule, {"count": 9}) is True
        assert evaluate_condition(rule, {"count": 10}) is False

    def test_contains_string(self):
        rule = ConditionalRule(field="name", operator="contains", value="test")
        assert evaluate_condition(rule, {"name": "This is a test"}) is True
        assert evaluate_condition(rule, {"name": "THIS IS A TEST"}) is True
        assert evaluate_condition(rule, {"name": "no match"}) is False

    def test_contains_array(self):
        rule = ConditionalRule(field="tags", operator="contains", value="urgent")
        assert evaluate_condition(rule, {"tags": ["urgent", "low"]}) is True
        assert evaluate_condition(rule, {"tags": ["low"]}) is False

    def test_contains_non_string_non_array(self):
        rule = ConditionalRule(field="val", operator="contains", value="x")
        assert evaluate_condition(rule, {"val": 123}) is False

    def test_exists_with_value(self):
        rule = ConditionalRule(field="name", operator="exists")
        assert evaluate_condition(rule, {"name": "hello"}) is True

    def test_exists_none(self):
        rule = ConditionalRule(field="name", operator="exists")
        assert evaluate_condition(rule, {"name": None}) is False

    def test_exists_empty_string(self):
        rule = ConditionalRule(field="name", operator="exists")
        assert evaluate_condition(rule, {"name": ""}) is False

    def test_exists_missing(self):
        rule = ConditionalRule(field="name", operator="exists")
        assert evaluate_condition(rule, {}) is False

    def test_unknown_operator_passes(self):
        rule = ConditionalRule(field="x", operator="unknown_op", value=1)
        assert evaluate_condition(rule, {"x": 1}) is True


class TestGetVisibleFields:
    def test_no_condition_always_visible(self):
        fields = [{"key": "name", "label": "Name"}]
        result = get_visible_fields(fields, {})
        assert result == ["name"]

    def test_condition_true(self):
        fields = [
            {"key": "name", "label": "Name"},
            {
                "key": "extra",
                "label": "Extra",
                "conditionalOn": {"field": "show", "operator": "eq", "value": True},
            },
        ]
        result = get_visible_fields(fields, {"show": True})
        assert "name" in result
        assert "extra" in result

    def test_condition_false(self):
        fields = [
            {"key": "name", "label": "Name"},
            {
                "key": "extra",
                "label": "Extra",
                "conditionalOn": {"field": "show", "operator": "eq", "value": True},
            },
        ]
        result = get_visible_fields(fields, {"show": False})
        assert "name" in result
        assert "extra" not in result


class TestGetRequiredDocuments:
    def test_unconditional_always_required(self):
        docs = [{"key": "id_proof", "label": "ID Proof", "required": True}]
        result = get_required_documents(docs, {})
        assert result == [{"key": "id_proof", "required": True}]

    def test_conditional_applies_when_true(self):
        docs = [
            {
                "key": "env_clearance",
                "label": "Env Clearance",
                "required": True,
                "conditionalOn": {
                    "field": "sector",
                    "operator": "eq",
                    "value": "chemicals",
                },
            }
        ]
        result = get_required_documents(docs, {"sector": "chemicals"})
        assert len(result) == 1

    def test_conditional_skipped_when_false(self):
        docs = [
            {
                "key": "env_clearance",
                "label": "Env Clearance",
                "required": True,
                "conditionalOn": {
                    "field": "sector",
                    "operator": "eq",
                    "value": "chemicals",
                },
            }
        ]
        result = get_required_documents(docs, {"sector": "textiles"})
        assert len(result) == 0
