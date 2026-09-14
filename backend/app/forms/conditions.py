"""Conditional logic evaluator for dynamic forms.

Ported from Digital-Permit-Platform/src/lib/conditions.ts.

Evaluates conditional rules against form answers. Supports 8 operators.
Two higher-order functions use this evaluator to determine which form
fields and document requirements should be visible/required.

Source: Digital-Permit-Platform/src/lib/conditions.ts (93 lines)
"""
from __future__ import annotations

from typing import Any

from app.forms.models import ConditionalRule


def evaluate_condition(
    rule: ConditionalRule,
    answers: dict[str, Any],
) -> bool:
    """Evaluate a conditional rule against form answers.

    Supports operators: eq, neq, in, not_in, gt, lt, contains, exists.
    Unknown operators return True (pass-through).
    """
    field_value = answers.get(rule.field)

    match rule.operator:
        case "eq":
            return field_value == rule.value

        case "neq":
            return field_value != rule.value

        case "in":
            if isinstance(rule.value, list):
                return field_value in rule.value
            return False

        case "not_in":
            if isinstance(rule.value, list):
                return field_value not in rule.value
            return True

        case "gt":
            return (
                isinstance(field_value, (int, float))
                and isinstance(rule.value, (int, float))
                and field_value > rule.value
            )

        case "lt":
            return (
                isinstance(field_value, (int, float))
                and isinstance(rule.value, (int, float))
                and field_value < rule.value
            )

        case "contains":
            if isinstance(field_value, str) and isinstance(rule.value, str):
                return field_value.lower().__contains__(rule.value.lower())
            if isinstance(field_value, list):
                return rule.value in field_value
            return False

        case "exists":
            return field_value is not None and field_value != ""

    return True


def get_visible_fields(
    fields: list[dict[str, Any]],
    answers: dict[str, Any],
) -> list[str]:
    """Determine which fields are visible given current answers.

    Fields with no conditionalOn are always visible.
    Fields whose conditionalOn evaluates to True are visible.
    """
    visible: list[str] = []
    for field in fields:
        cond = field.get("conditionalOn")
        if cond is None:
            visible.append(field["key"])
        else:
            rule = ConditionalRule.from_dict(cond)
            if evaluate_condition(rule, answers):
                visible.append(field["key"])
    return visible


def get_required_documents(
    requirements: list[dict[str, Any]],
    answers: dict[str, Any],
) -> list[dict[str, Any]]:
    """Determine which document requirements apply given current answers.

    Requirements with no conditionalOn always apply.
    Requirements whose conditionalOn evaluates to True apply.
    """
    result: list[dict[str, Any]] = []
    for req in requirements:
        cond = req.get("conditionalOn")
        if cond is None:
            result.append({"key": req["key"], "required": req["required"]})
        else:
            rule = ConditionalRule.from_dict(cond)
            if evaluate_condition(rule, answers):
                result.append({"key": req["key"], "required": req["required"]})
    return result
