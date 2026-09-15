"""Deterministic validation engine for documents.

Validates extracted fields against rules defined in the workbook Document_Register.
Returns explicit outcomes: VALID, INVALID, REVIEW_REQUIRED, or INSUFFICIENT_DATA.
Every result includes source/rule traceability.
"""
from __future__ import annotations

from typing import Any

from app.extraction.models import (
    ExtractionResult,
    ExtractionStatus,
    FieldFinding,
    ValidationOutcome,
    ValidationResult,
)

# Validation rule definitions per document domain
# Source: SIH_130_Gujarat_Chemical_Final_Verified_Dataset.xlsx → Document_Register sheet

VALIDATION_RULES: dict[str, list[dict[str, Any]]] = {
    "LAND": [
        {
            "rule_id": "LAND-001",
            "description": "Document must be a PDF (accepted format for land documents)",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "GIDC Document Requirements",
        },
        {
            "rule_id": "LAND-002",
            "description": "Document must not be empty (minimum 1 page)",
            "field_name": "page_count",
            "check": "min_value",
            "min_value": 1,
            "source_ref": "GIDC Document Requirements",
        },
    ],
    "BUILDING": [
        {
            "rule_id": "BUILD-001",
            "description": "Building plan must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "GIDC Plan Approval Requirements",
        },
        {
            "rule_id": "BUILD-002",
            "description": "Building plan must have at least 1 page",
            "field_name": "page_count",
            "check": "min_value",
            "min_value": 1,
            "source_ref": "GIDC Plan Approval Requirements",
        },
    ],
    "ENVIRONMENT": [
        {
            "rule_id": "ENV-001",
            "description": "Environmental document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "GPCB/IFP Requirements",
        },
        {
            "rule_id": "ENV-002",
            "description": "Environmental document must have content (minimum 1 page)",
            "field_name": "page_count",
            "check": "min_value",
            "min_value": 1,
            "source_ref": "GPCB/IFP Requirements",
        },
    ],
    "PROCESS": [
        {
            "rule_id": "PROC-001",
            "description": "Process document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "IFP GPCB Checklist",
        },
        {
            "rule_id": "PROC-002",
            "description": "Process document must have content",
            "field_name": "page_count",
            "check": "min_value",
            "min_value": 1,
            "source_ref": "IFP GPCB Checklist",
        },
    ],
    "WASTE": [
        {
            "rule_id": "WASTE-001",
            "description": "Waste document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "HOWM Rule 6",
        },
    ],
    "CHEMICAL": [
        {
            "rule_id": "CHEM-001",
            "description": "Chemical list must be a PDF or CSV",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf", "text/csv"],
            "source_ref": "MSIHC Guidelines",
        },
        {
            "rule_id": "CHEM-002",
            "description": "If CSV, must have at least 2 columns (chemical name + quantity)",
            "field_name": "column_count",
            "check": "conditional_min",
            "condition_field": "mime_type",
            "condition_value": "text/csv",
            "min_value": 2,
            "source_ref": "MSIHC Guidelines",
        },
    ],
    "FIRE": [
        {
            "rule_id": "FIRE-001",
            "description": "Fire safety document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "Gujarat Fire Safety Regulations 2023",
        },
    ],
    "ELECTRICAL": [
        {
            "rule_id": "ELEC-001",
            "description": "Electrical document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "CEICED/IFP Requirements",
        },
    ],
    "FACTORY": [
        {
            "rule_id": "FACT-001",
            "description": "Factory document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "ShramSetu Requirements",
        },
    ],
    "CHEMICAL STORAGE": [
        {
            "rule_id": "CSTOR-001",
            "description": "PESO document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "PESO Petroleum Rules 2002",
        },
    ],
    "WATER": [
        {
            "rule_id": "WATER-001",
            "description": "Water document must be a PDF",
            "field_name": "mime_type",
            "check": "accepted_mime",
            "accepted": ["application/pdf"],
            "source_ref": "CGWA Guidelines",
        },
    ],
}


def _check_accepted_mime(field_value: Any, rule: dict[str, Any]) -> tuple[ValidationOutcome, str]:
    """Check if MIME type is in accepted list."""
    accepted = rule.get("accepted", [])
    if field_value in accepted:
        return ValidationOutcome.VALID, f"MIME type '{field_value}' is accepted"
    return ValidationOutcome.INVALID, f"MIME type '{field_value}' not in accepted list: {accepted}"


def _check_min_value(field_value: Any, rule: dict[str, Any]) -> tuple[ValidationOutcome, str]:
    """Check if numeric field meets minimum value."""
    min_value = rule.get("min_value", 0)
    try:
        if field_value is None:
            return ValidationOutcome.INSUFFICIENT_DATA, "Field value is missing"
        if int(field_value) >= min_value:
            return ValidationOutcome.VALID, f"Value {field_value} meets minimum {min_value}"
        return ValidationOutcome.INVALID, f"Value {field_value} below minimum {min_value}"
    except (TypeError, ValueError):
        return ValidationOutcome.REVIEW_REQUIRED, f"Cannot parse value as integer: {field_value}"


def _check_conditional_min(
    field_value: Any,
    rule: dict[str, Any],
    all_fields: dict[str, Any],
) -> tuple[ValidationOutcome, str]:
    """Check minimum value only if condition is met."""
    condition_field = rule.get("condition_field")
    condition_value = rule.get("condition_value")

    if condition_field and all_fields.get(condition_field) != condition_value:
        return ValidationOutcome.VALID, "Rule does not apply (condition not met)"

    return _check_min_value(field_value, rule)


CHECK_FUNCTIONS = {
    "accepted_mime": _check_accepted_mime,
    "min_value": _check_min_value,
    "conditional_min": _check_conditional_min,
}


def validate_document(
    extraction_result: ExtractionResult,
    requirement_key: str,
    domain: str,
    mime_type: str,
    accepted_mime_types: list[str] | None = None,
) -> ValidationResult:
    """Validate extracted fields against deterministic rules.

    Args:
        extraction_result: Result from document extraction
        requirement_key: Document requirement key (e.g., D01)
        domain: Document domain (e.g., LAND, ENVIRONMENT)
        mime_type: Declared MIME type of the document
        accepted_mime_types: List of accepted MIME types from requirement

    Returns:
        ValidationResult with explicit outcome and field-level findings
    """
    findings: list[FieldFinding] = []

    # Build field map from extraction results
    field_map: dict[str, Any] = {}
    for field in extraction_result.fields:
        field_map[field.field_name] = field.field_value

    # Add mime_type to field map for validation
    field_map["mime_type"] = mime_type

    # Get rules for this domain
    rules = VALIDATION_RULES.get(domain, [])

    for rule in rules:
        field_name = rule["field_name"]
        field_value = field_map.get(field_name)
        check_type = rule["check"]

        check_func = CHECK_FUNCTIONS.get(check_type)
        if not check_func:
            continue

        if check_type == "conditional_min":
            outcome, message = check_func(field_value, rule, field_map)
        else:
            outcome, message = check_func(field_value, rule)

        findings.append(FieldFinding(
            field_name=field_name,
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            outcome=outcome,
            expected=rule.get("accepted") or rule.get("min_value"),
            actual=field_value,
            message=message,
            source_ref=rule.get("source_ref", ""),
        ))

    # Check accepted MIME types from requirement if provided
    if accepted_mime_types:
        mime_valid = mime_type in accepted_mime_types
        if not mime_valid:
            # Check wildcard matches
            for accepted in accepted_mime_types:
                if accepted.endswith("/*") and mime_type.startswith(accepted[:-2]):
                    mime_valid = True
                    break

        if not mime_valid:
            findings.append(FieldFinding(
                field_name="mime_type",
                rule_id="REQ-MIME-001",
                rule_description=f"Document must be one of: {accepted_mime_types}",
                outcome=ValidationOutcome.INVALID,
                expected=accepted_mime_types,
                actual=mime_type,
                message=f"MIME type '{mime_type}' not accepted for this requirement",
                source_ref="Document Requirement Specification",
            ))

    # Determine overall outcome
    if extraction_result.status == ExtractionStatus.UNSUPPORTED:
        overall_outcome = ValidationOutcome.REVIEW_REQUIRED
    elif extraction_result.status == ExtractionStatus.FAILED:
        overall_outcome = ValidationOutcome.REVIEW_REQUIRED
    elif any(f.outcome == ValidationOutcome.INVALID for f in findings):
        overall_outcome = ValidationOutcome.INVALID
    elif any(f.outcome == ValidationOutcome.REVIEW_REQUIRED for f in findings):
        overall_outcome = ValidationOutcome.REVIEW_REQUIRED
    elif any(f.outcome == ValidationOutcome.INSUFFICIENT_DATA for f in findings):
        overall_outcome = ValidationOutcome.INSUFFICIENT_DATA
    else:
        overall_outcome = ValidationOutcome.VALID

    # Collect source references
    source_refs = list({f.source_ref for f in findings if f.source_ref})

    return ValidationResult(
        document_id=extraction_result.document_id,
        application_id=extraction_result.application_id,
        requirement_key=requirement_key,
        outcome=overall_outcome,
        findings=findings,
        rule_version="1",
        source_refs=source_refs,
    )
