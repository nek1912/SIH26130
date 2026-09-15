"""Extraction and validation models for documents.

Defines structured fields extracted from uploaded documents and
deterministic validation results with traceability.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExtractionStatus(StrEnum):
    """Status of document extraction."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


class ValidationOutcome(StrEnum):
    """Outcome of deterministic validation."""
    VALID = "VALID"
    INVALID = "INVALID"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class FieldFinding(BaseModel):
    """A single field-level validation finding."""
    field_name: str = Field(..., description="Name of the extracted field")
    rule_id: str = Field(..., description="ID of the validation rule that produced this finding")
    rule_description: str = Field(..., description="Human-readable description of the rule")
    outcome: ValidationOutcome = Field(..., description="Validation outcome for this field")
    expected: Any = Field(None, description="Expected value or pattern")
    actual: Any = Field(None, description="Actual extracted value")
    message: str = Field("", description="Human-readable finding message")
    source_ref: str = Field("", description="Reference to regulatory source if applicable")


class ExtractedField(BaseModel):
    """A structured field extracted from a document."""
    id: str | None = Field(None, description="Database ID")
    document_id: str = Field(..., description="ID of the source document")
    application_id: str = Field(..., description="ID of the application")
    field_name: str = Field(..., description="Name of the extracted field")
    field_value: Any = Field(None, description="Extracted value")
    field_type: str = Field("string", description="Data type of the field")
    extraction_method: str = Field("", description="Method used to extract the field")
    confidence: float = Field(1.0, ge=0, le=1, description="Extraction confidence")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional extraction metadata"
    )


class ExtractionResult(BaseModel):
    """Result of extracting fields from a document."""
    document_id: str = Field(..., description="ID of the processed document")
    application_id: str = Field(..., description="ID of the application")
    status: ExtractionStatus = Field(..., description="Extraction status")
    fields: list[ExtractedField] = Field(default_factory=list, description="Extracted fields")
    errors: list[str] = Field(default_factory=list, description="Extraction errors")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="File metadata (size, pages, etc.)"
    )
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result of validating extracted fields against rules."""
    document_id: str = Field(..., description="ID of the validated document")
    application_id: str = Field(..., description="ID of the application")
    requirement_key: str = Field(..., description="Document requirement key (e.g., D01)")
    outcome: ValidationOutcome = Field(..., description="Overall validation outcome")
    findings: list[FieldFinding] = Field(default_factory=list, description="Field-level findings")
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    rule_version: str = Field("1", description="Version of validation rules used")
    source_refs: list[str] = Field(
        default_factory=list, description="Regulatory sources referenced"
    )


class DocumentExtractionSummary(BaseModel):
    """Summary of extraction and validation for a document requirement."""
    requirement_key: str
    document_name: str
    extraction_status: ExtractionStatus | None = None
    validation_outcome: ValidationOutcome | None = None
    field_count: int = 0
    finding_count: int = 0
    errors: list[str] = Field(default_factory=list)
