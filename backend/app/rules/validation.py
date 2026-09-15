"""Semantic validation of applicability condition trees.

Ported from compliance-grid/src/gates/validate-applicability.ts.

Checks that each leaf condition uses allowed field names, that numeric operators
are only used on compatible fields, and that the value matches the expected
type. Walks the recursive condition tree (AND/OR/NOT nodes).

Source: compliance-grid/src/gates/validate-applicability.ts (128 lines)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ConditionNode,
    EntityType,
    NotNode,
    OrNode,
)

# ─────────────────────────────────────────────────────────────
# Allowed field names for applicability conditions
# ─────────────────────────────────────────────────────────────

ALLOWED_FIELDS = {
    # Entity fields
    "sector",
    "entity_type",
    "jurisdictions",
    "headcount",
    "annual_turnover_inr",
    "incorporation_date",
    "registered_state",
    # Domain-specific fields from Scenario_Profile
    "plot_area_sqm",
    "builtup_area_sqm",
    "industry_type",
    "new_project",
    "production_capacity",
    "hazardous_chemicals_handled",
    "hazardous_waste_generated",
    "water_source",
    "fresh_water_requirement",
    "process_water",
    "domestic_water",
    "effluent_generation",
    "ETP_capacity",
    "power_demand",
    "connection_type",
    "DG_capacity",
    "workers_total",
    "workers_powered_factory",
    "hazardous_process",
    "building_height",
    "fire_safety_certificate_candidate",
    "lift_present",
    "boiler_present",
    "groundwater_use",
    "tree_felling",
    "forest_or_protected_area_overlap",
    "critical_pollution_area_status",
    "coastal_regulation_zone_status",
    "legal_entity",
    "notified_industrial_area",
    "electricity_license_area",
    "petroleum_or_licensed_storage",
    "estate",
    "district",
    "taluka",
    "state",
    "village",
    "pin_code",
}

NUMERIC_OPS = {"gt", "gte", "lt", "lte"}

# Fields that support numeric comparison ops. incorporation_date is
# represented as an ISO string but is ordered, so numeric ops apply.
NUMERIC_OP_COMPATIBLE_FIELDS = {
    "headcount",
    "annual_turnover_inr",
    "incorporation_date",
    "plot_area_sqm",
    "builtup_area_sqm",
    "production_capacity",
    "fresh_water_requirement",
    "process_water",
    "domestic_water",
    "effluent_generation",
    "ETP_capacity",
    "power_demand",
    "DG_capacity",
    "workers_total",
    "workers_powered_factory",
    "building_height",
}

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_JURISDICTION_RE = re.compile(r"^IN(-[A-Z]{2})?$")


@dataclass
class ValidationIssue:
    path: str  # dot-separated path to the failing node (e.g. "and.0.field")
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

        case (
            "plot_area_sqm" | "builtup_area_sqm" | "production_capacity"
            | "fresh_water_requirement" | "process_water" | "domestic_water"
            | "effluent_generation" | "ETP_capacity" | "power_demand"
            | "DG_capacity" | "workers_total" | "workers_powered_factory"
            | "building_height"
        ):
            if op == "in":
                if not isinstance(value, list) or not all(
                    isinstance(v, (int, float)) for v in value
                ):
                    return "value must be a number"
            else:
                if not isinstance(value, (int, float)):
                    return "value must be a number"
            return None

        case (
            "new_project" | "hazardous_chemicals_handled"
            | "hazardous_waste_generated" | "fire_safety_certificate_candidate"
            | "lift_present" | "boiler_present" | "groundwater_use"
            | "tree_felling"
        ):
            if op == "in":
                if not isinstance(value, list) or not all(
                    isinstance(v, bool) for v in value
                ):
                    return "value must be a boolean"
            else:
                if not isinstance(value, bool):
                    return "value must be a boolean"
            return None

        case (
            "industry_type" | "connection_type" | "water_source"
            | "discharge_mode" | "legal_entity" | "estate" | "district"
            | "taluka" | "state" | "village"
            | "petroleum_or_licensed_storage"
            | "forest_or_protected_area_overlap"
            | "critical_pollution_area_status"
            | "coastal_regulation_zone_status"
            | "notified_industrial_area"
            | "electricity_license_area"
        ):
            if op == "in":
                if not isinstance(value, list) or not all(
                    isinstance(v, str) and len(v) > 0 for v in value
                ):
                    return "value must be a non-empty string"
            else:
                if not isinstance(value, str) or len(value) == 0:
                    return "value must be a non-empty string"
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


def _validate_node(node: ConditionNode, path: str, issues: list[ValidationIssue]) -> None:
    """Recursively validate a condition node."""
    if isinstance(node, ApplicabilityCondition):
        if node.field not in ALLOWED_FIELDS:
            issues.append(
                ValidationIssue(
                    path=path,
                    field=node.field,
                    op=node.op.value,
                    reason=(
                        f'unknown field "{node.field}"; '
                        f'allowed: {", ".join(sorted(ALLOWED_FIELDS))}'
                    ),
                )
            )
            return

        if node.op.value in NUMERIC_OPS and node.field not in NUMERIC_OP_COMPATIBLE_FIELDS:
            issues.append(
                ValidationIssue(
                    path=path,
                    field=node.field,
                    op=node.op.value,
                    reason=(
                        f'op "{node.op.value}" requires a numeric or date field; '
                        f'"{node.field}" is not'
                    ),
                )
            )
            return

        value_issue = _check_value(node.field, node.op.value, node.value)
        if value_issue:
            issues.append(
                ValidationIssue(path=path, field=node.field, op=node.op.value, reason=value_issue)
            )

    elif isinstance(node, AndNode):
        for i, child in enumerate(node.conditions):
            _validate_node(child, f"{path}.and.{i}", issues)

    elif isinstance(node, OrNode):
        for i, child in enumerate(node.conditions):
            _validate_node(child, f"{path}.or.{i}", issues)

    elif isinstance(node, NotNode):
        _validate_node(node.condition, f"{path}.not", issues)


def validate_applicability_conditions(
    conditions: list[ConditionNode],
) -> ValidationResult:
    """Validate a list of condition trees semantically.

    Walks the recursive tree and checks each leaf:
    1. Field name is in the allowed set
    2. Numeric ops (gt, gte, lt, lte) are only used on numeric/date fields
    3. Value type matches the field's expected type
    """
    issues: list[ValidationIssue] = []

    for i, node in enumerate(conditions):
        _validate_node(node, f"[{i}]", issues)

    return ValidationResult(ok=len(issues) == 0, issues=issues)
