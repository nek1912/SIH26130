"""Manual government handoff models (Pydantic v2).

A handoff record tracks an applicant's MANUAL progress on an external
authority portal. It never implies machine submission to, or a response
from, any government system.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class HandoffStatus(StrEnum):
    HANDED_OFF = "handed_off"
    SUBMITTED_EXTERNALLY = "submitted_externally"
    UNDER_EXTERNAL_REVIEW = "under_external_review"
    APPROVED_EXTERNAL = "approved_external"
    REJECTED_EXTERNAL = "rejected_external"
    RETURNED_FOR_CORRECTION = "returned_for_correction"


class Verification(StrEnum):
    USER_REPORTED = "user_reported"
    STAFF_VERIFIED = "staff_verified"


# Persisted statuses counted as "active" for the single-active-handoff rule.
ACTIVE_STATUSES = frozenset(
    {
        HandoffStatus.HANDED_OFF,
        HandoffStatus.SUBMITTED_EXTERNALLY,
        HandoffStatus.UNDER_EXTERNAL_REVIEW,
        HandoffStatus.RETURNED_FOR_CORRECTION,
    }
)


class HandoffRecord(BaseModel):
    application_id: str
    approval_code: str
    authority: str
    external_system: str
    portal_url: str
    portal_kind: str = "portal"
    status: HandoffStatus
    external_reference: str | None = None
    submitted_at: str | None = None
    last_external_update_at: str | None = None
    applicant_note: str | None = None
    reported_by: str | None = None
    verification: Verification = Verification.USER_REPORTED
    verified_by: str | None = None
    verified_at: str | None = None


class InitiateHandoffRequest(BaseModel):
    approval_code: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class RecordSubmissionRequest(BaseModel):
    external_reference: str = Field(min_length=1)
    applicant_note: str | None = None

    model_config = {"extra": "forbid"}


class ReportStatusRequest(BaseModel):
    to_status: HandoffStatus
    applicant_note: str | None = None

    model_config = {"extra": "forbid"}


class VerifyHandoffRequest(BaseModel):
    verified_status: HandoffStatus

    model_config = {"extra": "forbid"}
