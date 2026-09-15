"""Cross-document consistency models.

Defines rules and results for comparing extracted field values
across documents belonging to the same application.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ConsistencyOutcome(StrEnum):
    """Outcome of a cross-document consistency check."""
    VALID = "VALID"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ConsistencyRule(BaseModel):
    """A single cross-document consistency rule from the workbook."""
    id: str = Field(..., description="Rule ID (e.g. C01)")
    canonical_field: str = Field(..., description="Canonical field name to compare")
    affected_systems: str = Field(..., description="Affected approval systems (informational)")
    evidence_field: str = Field(..., description="Evidence field description (informational)")
    requirement_key: str = Field(..., description="Comparison type (MUST_MATCH)")
    document_keys: list[str] = Field(..., description="Document requirement keys to compare")


class ConsistencyFinding(BaseModel):
    """A single field-level consistency finding."""
    rule_id: str = Field(..., description="Consistency rule ID")
    canonical_field: str = Field(..., description="Canonical field name")
    outcome: ConsistencyOutcome = Field(..., description="Consistency outcome")
    observed_values: dict[str, Any] = Field(
        default_factory=dict,
        description="Observed values keyed by document requirement key",
    )
    expected_relationship: str = Field(
        ..., description="Expected relationship (e.g. MUST_MATCH across [D01, D02])"
    )
    message: str = Field("", description="Human-readable finding message")
    source_ref: str = Field("", description="Source reference")


class ConsistencyResult(BaseModel):
    """Full consistency check result for an application."""
    application_id: str = Field(..., description="Application ID")
    outcome: ConsistencyOutcome = Field(
        ..., description="Overall outcome (worst-case across findings)"
    )
    findings: list[ConsistencyFinding] = Field(
        default_factory=list, description="Field-level findings"
    )
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the check"
    )
    rule_version: str = Field("1", description="Version of consistency rules used")
