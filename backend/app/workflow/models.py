"""Workflow models — application status and stage type mappings.

Ported from Digital-Permit-Platform/src/lib/workflow/engine.ts
and Digital-Permit-Platform/src/types/module.ts.

Source: Digital-Permit-Platform/src/lib/workflow/engine.ts (323 lines)
"""
from __future__ import annotations

from enum import StrEnum


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    AWAITING_INSPECTION = "awaiting_inspection"
    AWAITING_CONSULTATION = "awaiting_consultation"
    AWAITING_HEARING = "awaiting_hearing"
    AWAITING_DOCUMENTS = "awaiting_documents"
    AWAITING_PAYMENT = "awaiting_payment"
    APPROVED = "approved"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"
    INCOMPLETE = "incomplete"
    RETURNED = "returned"
    CANCELLED = "cancelled"


# Map workflow stage types to application status.
# From Digital-Permit-Platform/src/lib/workflow/engine.ts lines 14-23.
STAGE_TYPE_TO_STATUS: dict[str, ApplicationStatus] = {
    "validation": ApplicationStatus.UNDER_REVIEW,
    "review": ApplicationStatus.UNDER_REVIEW,
    "inspection": ApplicationStatus.AWAITING_INSPECTION,
    "consultation": ApplicationStatus.AWAITING_CONSULTATION,
    "hearing": ApplicationStatus.AWAITING_HEARING,
    "training": ApplicationStatus.UNDER_REVIEW,
    "decision": ApplicationStatus.UNDER_REVIEW,
    "custom": ApplicationStatus.UNDER_REVIEW,
}

# Statuses where an application is actively being processed (SLA applies).
# From Digital-Permit-Platform/src/lib/sla.ts lines 31-41.
ACTIVE_STATUSES: list[ApplicationStatus] = [
    ApplicationStatus.SUBMITTED,
    ApplicationStatus.UNDER_REVIEW,
    ApplicationStatus.AWAITING_INSPECTION,
    ApplicationStatus.AWAITING_CONSULTATION,
    ApplicationStatus.AWAITING_HEARING,
    ApplicationStatus.AWAITING_DOCUMENTS,
    ApplicationStatus.AWAITING_PAYMENT,
    ApplicationStatus.RETURNED,
    ApplicationStatus.INCOMPLETE,
]
