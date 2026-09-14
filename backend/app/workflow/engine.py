"""Workflow transition engine.

Manages application state transitions with:
- Valid transition rules (which status → which status)
- Role/permission enforcement per transition
- Optimistic concurrency protection
- Audit event creation
- Workflow event creation

This is the core domain logic for the application lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.audit.service import AuditEntry, AuditRecord, create_audit_record
from app.auth.permissions import Permission, SystemRole
from app.workflow.models import ApplicationStatus
from app.workflow.stages import StageType, WorkflowDefinition

# ---------------------------------------------------------------------------
# Transition rules
# ---------------------------------------------------------------------------

# Maps (from_status, action) → (to_status, required_role_or_permission).
# Actions: "submit", "advance", "assign", "request_info", "respond",
#          "approve", "refuse", "withdraw", "return", "cancel"
#
# If the value is None, any authenticated user can perform the action
# (the route handler still checks ownership or higher permissions).
# If the value is a Permission, the caller must hold that permission.

TRANSITION_RULES: dict[
    tuple[ApplicationStatus, str],
    tuple[ApplicationStatus, Permission | None],
] = {
    # --- Applicant actions ---
    (ApplicationStatus.DRAFT, "submit"): (
        ApplicationStatus.SUBMITTED,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.SUBMITTED, "withdraw"): (
        ApplicationStatus.WITHDRAWN,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.UNDER_REVIEW, "withdraw"): (
        ApplicationStatus.WITHDRAWN,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.AWAITING_INSPECTION, "withdraw"): (
        ApplicationStatus.WITHDRAWN,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.AWAITING_CONSULTATION, "withdraw"): (
        ApplicationStatus.WITHDRAWN,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.AWAITING_HEARING, "withdraw"): (
        ApplicationStatus.WITHDRAWN,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.RETURNED, "respond"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.INCOMPLETE, "respond"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_CREATE,
    ),
    # --- Reviewer/Manager actions ---
    (ApplicationStatus.SUBMITTED, "advance"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_REVIEW,
    ),
    (ApplicationStatus.UNDER_REVIEW, "advance"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_REVIEW,
    ),
    (ApplicationStatus.UNDER_REVIEW, "request_info"): (
        ApplicationStatus.RETURNED,
        Permission.APPLICATION_REVIEW,
    ),
    (ApplicationStatus.UNDER_REVIEW, "assign"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_ASSIGN,
    ),
    # --- Inspection ---
    (ApplicationStatus.AWAITING_INSPECTION, "advance"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_REVIEW,
    ),
    # --- Consultation ---
    (ApplicationStatus.AWAITING_CONSULTATION, "advance"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_REVIEW,
    ),
    # --- Hearing ---
    (ApplicationStatus.AWAITING_HEARING, "advance"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_REVIEW,
    ),
    # --- Decision ---
    (ApplicationStatus.UNDER_REVIEW, "approve"): (
        ApplicationStatus.APPROVED,
        Permission.APPLICATION_DECIDE,
    ),
    (ApplicationStatus.UNDER_REVIEW, "refuse"): (
        ApplicationStatus.REFUSED,
        Permission.APPLICATION_DECIDE,
    ),
    # --- Admin actions ---
    (ApplicationStatus.DRAFT, "cancel"): (
        ApplicationStatus.CANCELLED,
        Permission.APPLICATION_DELETE,
    ),
    (ApplicationStatus.SUBMITTED, "cancel"): (
        ApplicationStatus.CANCELLED,
        Permission.APPLICATION_DELETE,
    ),
    # --- Reserved statuses (documents/payment) ---
    (ApplicationStatus.AWAITING_DOCUMENTS, "respond"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.AWAITING_DOCUMENTS, "withdraw"): (
        ApplicationStatus.WITHDRAWN,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.AWAITING_PAYMENT, "respond"): (
        ApplicationStatus.UNDER_REVIEW,
        Permission.APPLICATION_CREATE,
    ),
    (ApplicationStatus.AWAITING_PAYMENT, "withdraw"): (
        ApplicationStatus.WITHDRAWN,
        Permission.APPLICATION_CREATE,
    ),
}

# Actions that set the application to a specific stage type
ACTION_TO_STAGE_TYPE: dict[str, StageType] = {
    "advance": StageType.REVIEW,
    "request_info": StageType.REVIEW,
    "approve": StageType.DECISION,
    "refuse": StageType.DECISION,
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class TransitionResult:
    """Result of a workflow transition attempt."""

    success: bool
    previous_status: ApplicationStatus | None = None
    new_status: ApplicationStatus | None = None
    stage_key: str | None = None
    workflow_event: dict[str, Any] | None = None
    audit_record: AuditRecord | None = None
    error: str | None = None


@dataclass
class WorkflowEvent:
    """An immutable record of a workflow state change."""

    id: UUID
    application_id: UUID
    from_stage: str | None
    to_stage: str
    action: str
    performed_by: UUID | None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------


def can_transition(
    current_status: ApplicationStatus,
    action: str,
    user_role: SystemRole,
) -> tuple[bool, ApplicationStatus | None, str | None]:
    """Check whether a transition is allowed.

    Returns (allowed, target_status, error_message).
    """
    rule = TRANSITION_RULES.get((current_status, action))
    if rule is None:
        return False, None, f"Action '{action}' not allowed from status '{current_status}'"

    target_status, required_permission = rule

    if required_permission is not None:
        from app.auth.permissions import has_permission

        if not has_permission(user_role, required_permission):
            return (
                False,
                None,
                f"Permission '{required_permission.value}' required for '{action}'",
            )

    return True, target_status, None


def execute_transition(
    *,
    application_id: UUID,
    current_status: ApplicationStatus,
    action: str,
    user_id: UUID,
    user_role: SystemRole,
    current_stage: str | None = None,
    workflow_def: WorkflowDefinition | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TransitionResult:
    """Execute a workflow transition atomically.

    This function is stateless — it does NOT read or write the database.
    The caller (API route) is responsible for:
    1. Reading the current application state
    2. Calling this function
    3. Writing the result back to the database
    4. Handling concurrency (optimistic locking via conditional update)

    The function validates the transition, creates workflow events and
    audit records, and returns the result for the caller to persist.
    """
    # Validate transition
    allowed, target_status, error = can_transition(current_status, action, user_role)
    if not allowed:
        return TransitionResult(success=False, error=error)

    # Determine the target stage
    to_stage = current_stage
    if workflow_def is not None and action in ACTION_TO_STAGE_TYPE:
        # For advance/request_info, find the next stage of the appropriate type
        if current_stage:
            next_stage = workflow_def.get_next_stage(current_stage)
            if next_stage:
                to_stage = next_stage.key
            else:
                # At the last stage — for approve/refuse, stay in current stage
                to_stage = current_stage
        else:
            first = workflow_def.get_first_stage()
            if first:
                to_stage = first.key

    # If action is submit, go to the first stage
    if action == "submit" and workflow_def is not None:
        first = workflow_def.get_first_stage()
        if first:
            to_stage = first.key

    to_stage = to_stage or "unknown"

    # Create workflow event
    event = WorkflowEvent(
        id=uuid4(),
        application_id=application_id,
        from_stage=current_stage,
        to_stage=to_stage,
        action=action,
        performed_by=user_id,
        metadata=metadata or {},
        created_at=datetime.now(),
    )

    # Create audit record
    audit_entry = AuditEntry(
        action=f"workflow.{action}",
        entity_type="Application",
        entity_id=str(application_id),
        user_id=str(user_id),
        application_id=str(application_id),
        previous_values={"status": current_status, "stage": current_stage},
        new_values={"status": target_status, "stage": to_stage},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    audit_record = create_audit_record(audit_entry)

    return TransitionResult(
        success=True,
        previous_status=current_status,
        new_status=target_status,
        stage_key=to_stage,
        workflow_event={
            "id": str(event.id),
            "application_id": str(event.application_id),
            "from_stage": event.from_stage,
            "to_stage": event.to_stage,
            "action": event.action,
            "performed_by": str(event.performed_by) if event.performed_by else None,
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat(),
        },
        audit_record=audit_record,
    )
