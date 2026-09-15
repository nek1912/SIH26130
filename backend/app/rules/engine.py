"""Deterministic applicability evaluation engine.

Ported from compliance-grid/src/gates/evaluate-applicability.ts.

Given an EntityProfile and a list of Obligations, filters to only those
that apply. Multiple conditions on a single obligation are AND-combined.
No AI involvement — pure deterministic code.

Source: compliance-grid/src/gates/evaluate-applicability.ts (68 lines)
"""
from __future__ import annotations

from typing import Any

from app.rules.models import ApplicabilityCondition, EntityProfile, Obligation


def _lookup_field(entity: EntityProfile, field: str) -> Any:
    """Read a named field from an EntityProfile via generic lookup."""
    return entity.model_dump().get(field)


def _evaluate_condition(entity: EntityProfile, condition: ApplicabilityCondition) -> bool:
    """Evaluate a single applicability condition against an entity profile."""
    value = _lookup_field(entity, condition.field)

    match condition.op:
        case "eq":
            return value == condition.value

        case "in":
            if not isinstance(condition.value, list):
                return False
            if isinstance(value, list):
                return any(v in condition.value for v in value)
            return value in condition.value

        case "gt":
            return (
                isinstance(value, (int, float))
                and isinstance(condition.value, (int, float))
                and value > condition.value
            )

        case "gte":
            return (
                isinstance(value, (int, float))
                and isinstance(condition.value, (int, float))
                and value >= condition.value
            )

        case "lt":
            return (
                isinstance(value, (int, float))
                and isinstance(condition.value, (int, float))
                and value < condition.value
            )

        case "lte":
            return (
                isinstance(value, (int, float))
                and isinstance(condition.value, (int, float))
                and value <= condition.value
            )

    # Unknown operator — conservatively reject rather than silently assume
    return False


def evaluate_applicability(
    entity: EntityProfile,
    obligations: list[Obligation],
) -> list[Obligation]:
    """Filter obligations to only those applicable to the given entity.

    All applicability conditions on an obligation must pass (AND logic).
    Returns the subset of obligations that apply.

    This is a pure deterministic function — no DB, no AI.
    """
    return [
        o
        for o in obligations
        if all(_evaluate_condition(entity, c) for c in o.applicability_conditions)
    ]
