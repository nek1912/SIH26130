"""G0-R5 regulatory evidence boundary — machine-readable evidence statuses.

Distinguishes VERIFIED / PARTIAL / NOT_ESTABLISHED / CONFLICTING for
unresolved regulatory facts. Fail-closed: only VERIFIED evidence may back
applicability rules; everything else surfaces as INSUFFICIENT_DATA.

Source of truth: Gap-Closure Pass G0-R5 Final (cut-off 25.09.2026).
This module asserts no legal conclusions — it records evidence state only.
"""
from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceStatus(StrEnum):
    """Evidence sufficiency for a regulatory fact."""

    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    CONFLICTING = "CONFLICTING"


class EvidenceRecord(BaseModel):
    """One unresolved (or verified) regulatory fact with traceability."""

    evidence_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    status: EvidenceStatus
    verified_scope: str = Field(min_length=1)
    unresolved_question: str = Field(default="")
    source_reference: str = Field(min_length=1)
    effective_date: date | None = None
    notes: str = ""
    flags: list[str] = Field(default_factory=list)


class EvidenceNotVerifiedError(ValueError):
    """Raised when a non-VERIFIED record is used where VERIFIED is required."""


def is_encodable(record: EvidenceRecord) -> bool:
    """True only for VERIFIED evidence. All other states must not be encoded."""
    return record.status == EvidenceStatus.VERIFIED


def is_evidence_gap(record: EvidenceRecord) -> bool:
    """True for any non-VERIFIED record (gap that must fail closed)."""
    return record.status != EvidenceStatus.VERIFIED


def require_verified(record: EvidenceRecord) -> EvidenceRecord:
    """Fail-closed guard for rule creation. Raises unless VERIFIED."""
    if not is_encodable(record):
        raise EvidenceNotVerifiedError(
            f"Evidence {record.evidence_id} is {record.status.value}; "
            "VERIFIED required before encoding applicability rules."
        )
    return record


def gap_to_applicability_result(record: EvidenceRecord) -> str | None:
    """Map an evidence gap to an applicability result.

    Returns "insufficient_data" for PARTIAL / NOT_ESTABLISHED / CONFLICTING,
    None for VERIFIED (no gap to surface).
    """
    if is_evidence_gap(record):
        return "insufficient_data"
    return None
