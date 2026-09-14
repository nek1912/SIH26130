"""Semantic validation of applicability conditions.

Ported from compliance-grid/src/gates/validate-applicability.ts.

Checks that each condition uses allowed field names, that numeric operators
are only used on compatible fields, and that the value matches the expected
type. Failures route candidates to review rather than auto-committing.

Source: compliance-grid/src/gates/validate-applicability.ts (128 lines)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.rules.models import ApplicabilityCondition, EntityType

# ─────────────────────────────────────────────────────────────
# Allowed field names for applicability conditions
# ─────────────────────────────────────────────────────────────

ALLOWED_FIELDS = {
    "sector",
    "entity_type",
    "jurisdictions",
    "headcount",
    "annual_turnover_inr",
    "incorporation_date",
    "registered_state",
}

NUMERIC_OPS = {"gt", "gte", "lt", "lte"}

# Fields that support numeric comparison ops. incorporation_date is
# represented as an ISO string but is ordered, so numeric ops apply.
NUMERIC_OP_COMPATIBLE_FIELDS = {"headcount", "annual_turnover_inr", "incorporation_date"}

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_JURISDICTION_RE = re.compile(r"^IN(-[A-Z]{2})?$")


@dataclass
class ValidationIssue:
    index: int
    field: str
    op: str
    reason: str


@dataclass
class ValidationResult:
    ok: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)


def _check_value(field_name: str, op: str, value: object) -> str | None:
    """Validate the value type for a given field and operator."""
    match field_name:
        case "entity_type":
            if op == "in":
                if not isinstance(value, list) or not all(
                    v in EntityType.__members__.values() if isinstance(v, str) else False
                    for v in value
                ):
                    return "value must match the EntityType enum"
            else:
                if not isinstance(value, str) or value not in {
                    e.value for e in EntityType
                }:
                    return "value must match the EntityType enum"
            return None

        case "jurisdictions" | "registered_state":
            if op == "in":
                if not isinstance(value, list) or not all(
                    isinstance(v, str) and _JURISDICTION_RE.match(v) for v in value
                ):
                    return "value must match the Jurisdiction shape (IN or IN-XX)"
            else:
                if not isinstance(value, str) or not _JURISDICTION_RE.match(value):
                    return "value must match the Jurisdiction shape (IN or IN-XX)"
            return None

        case "sector":
            if op == "in":
                if not isinstance(value, list) or not all(
                    isinstance(v, str) and len(v) > 0 for v in value
                ):
                    return "value must be a non-empty string"
            else:
                if not isinstance(value, str) or len(value) == 0:
                    return "value must be a non-empty string"
            return None

        case "headcount" | "annual_turnover_inr":
            if op == "in":
                if not isinstance(value, list) or not all(
                    isinstance(v, (int, float)) for v in value
                ):
                    return "value must be a number"
            else:
                if not isinstance(value, (int, float)):
                    return "value must be a number"
            return None

        case "incorporation_date":
            if op == "in":
                if not isinstance(value, list) or not all(
                    isinstance(v, str) and _ISO_DATE_RE.match(v) for v in value
                ):
                    return "value must be an ISO date string (YYYY-MM-DD)"
            else:
                if not isinstance(value, str) or not _ISO_DATE_RE.match(value):
                    return "value must be an ISO date string (YYYY-MM-DD)"
            return None

    return None


def validate_applicability_conditions(
    conditions: list[ApplicabilityCondition],
) -> ValidationResult:
    """Validate a list of applicability conditions semantically.

    Checks:
    1. Field name is in the allowed set
    2. Numeric ops (gt, gte, lt, lte) are only used on numeric/date fields
    3. Value type matches the field's expected type
    """
    issues: list[ValidationIssue] = []

    for i, c in enumerate(conditions):
        if c.field not in ALLOWED_FIELDS:
            issues.append(
                ValidationIssue(
                    index=i,
                    field=c.field,
                    op=c.op.value,
                    reason=(
                        f'unknown field "{c.field}"; '
                        f'allowed: {", ".join(sorted(ALLOWED_FIELDS))}'
                    ),
                )
            )
            continue

        if c.op.value in NUMERIC_OPS and c.field not in NUMERIC_OP_COMPATIBLE_FIELDS:
            issues.append(
                ValidationIssue(
                    index=i,
                    field=c.field,
                    op=c.op.value,
                    reason=(
                        f'op "{c.op.value}" requires a numeric or date field; '
                        f'"{c.field}" is not'
                    ),
                )
            )
            continue

        value_issue = _check_value(c.field, c.op.value, c.value)
        if value_issue:
            issues.append(
                ValidationIssue(index=i, field=c.field, op=c.op.value, reason=value_issue)
            )

    return ValidationResult(ok=len(issues) == 0, issues=issues)
