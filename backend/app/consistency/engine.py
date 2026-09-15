"""Deterministic cross-document consistency engine.

Compares extracted field values across documents belonging to the
same application using the workbook's Consistency_Fields rules.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.consistency.models import (
    ConsistencyFinding,
    ConsistencyOutcome,
    ConsistencyResult,
    ConsistencyRule,
)
from app.extraction.models import ExtractedField


def check_application_consistency(
    application_id: str,
    extracted_fields: list[ExtractedField],
    rules: list[ConsistencyRule],
    doc_req_map: dict[str, str],
) -> ConsistencyResult:
    """Compare extracted field values across documents for each consistency rule.

    Args:
        application_id: The application being checked.
        extracted_fields: All extracted fields for this application.
        rules: Consistency rules to evaluate.
        doc_req_map: Mapping from document_id to requirement_key (e.g. "doc-uuid" -> "D01").

    Returns:
        ConsistencyResult with per-rule findings and aggregated outcome.
    """
    # Group extracted fields by canonical field name → {req_key: value}
    fields_by_name: dict[str, dict[str, Any]] = {}
    for field in extracted_fields:
        if field.field_name not in fields_by_name:
            fields_by_name[field.field_name] = {}
        req_key = doc_req_map.get(field.document_id)
        if req_key:
            # Only keep non-empty values
            if field.field_value is not None and field.field_value != "":
                fields_by_name[field.field_name][req_key] = field.field_value

    findings: list[ConsistencyFinding] = []

    for rule in rules:
        # Collect values from the rule's document_keys
        field_values = fields_by_name.get(rule.canonical_field, {})
        observed: dict[str, Any] = {}
        for dk in rule.document_keys:
            if dk in field_values:
                observed[dk] = field_values[dk]

        # Determine outcome
        non_empty = {k: v for k, v in observed.items() if v is not None and v != ""}

        if len(non_empty) == 0:
            outcome = ConsistencyOutcome.INSUFFICIENT_DATA
            message = (
                f"No extracted values found for {rule.canonical_field} "
                f"in any of {rule.document_keys}"
            )
        elif len(non_empty) == 1:
            outcome = ConsistencyOutcome.VALID
            key = list(non_empty.keys())[0]
            message = (
                f"Only one document ({key}) has a value for "
                f"{rule.canonical_field}; nothing to compare"
            )
        else:
            values = list(non_empty.values())
            if all(v == values[0] for v in values):
                outcome = ConsistencyOutcome.VALID
                message = f"All {len(non_empty)} documents agree on {rule.canonical_field}"
            else:
                outcome = ConsistencyOutcome.REVIEW_REQUIRED
                message = (
                    f"Documents disagree on {rule.canonical_field}: "
                    + ", ".join(f"{k}={v}" for k, v in non_empty.items())
                )

        findings.append(
            ConsistencyFinding(
                rule_id=rule.id,
                canonical_field=rule.canonical_field,
                outcome=outcome,
                observed_values=observed,
                expected_relationship=f"{rule.requirement_key} across {rule.document_keys}",
                message=message,
                source_ref=f"Workbook Consistency_Fields {rule.id}",
            )
        )

    # Aggregate: worst outcome across all findings
    outcome_priority = {
        ConsistencyOutcome.VALID: 0,
        ConsistencyOutcome.INSUFFICIENT_DATA: 1,
        ConsistencyOutcome.REVIEW_REQUIRED: 2,
    }
    worst = ConsistencyOutcome.VALID
    for f in findings:
        if outcome_priority[f.outcome] > outcome_priority[worst]:
            worst = f.outcome

    return ConsistencyResult(
        application_id=application_id,
        outcome=worst,
        findings=findings,
        checked_at=datetime.utcnow(),
        rule_version="1",
    )
