"""Application assignment and work-queue logic.

Provides helpers for:
- Assigning an application to a reviewer/officer
- Building staff work-queue queries (filtered views)
- Ownership/access checks for workflow actions
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.auth.permissions import SystemRole
from app.workflow.models import ACTIVE_STATUSES, ApplicationStatus


def can_assign(user_role: SystemRole) -> bool:
    """Check if a role can assign applications to officers.

    Only MANAGER and ADMIN can assign.
    """
    return user_role in {SystemRole.MANAGER, SystemRole.ADMIN}


def can_review(user_role: SystemRole) -> bool:
    """Check if a role can review applications."""
    return user_role in {SystemRole.REVIEWER, SystemRole.MANAGER, SystemRole.ADMIN}


def can_decide(user_role: SystemRole) -> bool:
    """Check if a role can make final decisions on applications."""
    return user_role in {SystemRole.MANAGER, SystemRole.ADMIN}


def get_staff_queue_filter(
    *,
    status: list[str] | None = None,
    assigned_to: UUID | None = None,
    team_id: str | None = None,
) -> dict[str, Any]:
    """Build a filter dictionary for staff work-queue queries.

    Returns a dict suitable for use with the repository query layer.
    """
    filters: dict[str, Any] = {}
    if status:
        # Validate statuses
        valid = [s for s in status if s in {s.value for s in ApplicationStatus}]
        if valid:
            filters["status"] = valid
    if assigned_to:
        filters["assigned_officer_id"] = str(assigned_to)
    if team_id:
        filters["owning_team_id"] = team_id
    return filters


def get_active_statuses() -> list[str]:
    """Return the list of statuses where SLA applies (as strings)."""
    return [s.value for s in ACTIVE_STATUSES]


def is_terminal_status(status: ApplicationStatus) -> bool:
    """Check if a status is terminal (no further transitions expected)."""
    return status in {
        ApplicationStatus.APPROVED,
        ApplicationStatus.REFUSED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.CANCELLED,
    }


def status_display_name(status: ApplicationStatus) -> str:
    """Human-readable display name for a status."""
    names = {
        ApplicationStatus.DRAFT: "Draft",
        ApplicationStatus.SUBMITTED: "Submitted",
        ApplicationStatus.UNDER_REVIEW: "Under Review",
        ApplicationStatus.AWAITING_INSPECTION: "Awaiting Inspection",
        ApplicationStatus.AWAITING_CONSULTATION: "Awaiting Consultation",
        ApplicationStatus.AWAITING_HEARING: "Awaiting Hearing",
        ApplicationStatus.AWAITING_DOCUMENTS: "Awaiting Documents",
        ApplicationStatus.AWAITING_PAYMENT: "Awaiting Payment",
        ApplicationStatus.APPROVED: "Approved",
        ApplicationStatus.REFUSED: "Refused",
        ApplicationStatus.WITHDRAWN: "Withdrawn",
        ApplicationStatus.INCOMPLETE: "Incomplete",
        ApplicationStatus.RETURNED: "Returned for Information",
        ApplicationStatus.CANCELLED: "Cancelled",
    }
    return names.get(status, status.value)
