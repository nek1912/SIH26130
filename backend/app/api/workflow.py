"""Workflow API endpoints.

Handles application state transitions:
- Submit (draft → submitted)
- Advance (review stage progression)
- Request info / respond
- Assign to officer
- Approve / refuse
- Withdraw / cancel
- Get workflow events for an application
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_applications_repository, get_workflow_events_repository
from app.auth.dependencies import (
    require_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.applications import ApplicationsRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.workflow.assignments import can_assign
from app.workflow.engine import execute_transition
from app.workflow.models import ApplicationStatus

router = APIRouter()


def _get_application_or_404(
    repo: ApplicationsRepository, application_id: UUID
) -> dict:
    """Fetch an application or raise 404."""
    app = repo.get_by_id(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Submit a draft application — DRAFT → SUBMITTED."""
    application = _get_application_or_404(repo, application_id)

    current_status = ApplicationStatus(application.get("status", "draft"))
    if current_status != ApplicationStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Application is in status '{current_status}', only 'draft' can be submitted",
        )

    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="submit",
        user_id=user.user_id,
        user_role=user.role,
        events_repository=events_repo,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error,
        )

    # Persist the transition
    repo.update(application_id, {
        "status": result.new_status,
        "current_stage": result.stage_key,
    })

    return {
        "application_id": str(application_id),
        "previous_status": result.previous_status,
        "new_status": result.new_status,
        "current_stage": result.stage_key,
        "workflow_event": result.workflow_event,
    }


@router.post("/applications/{application_id}/advance")
async def advance_application(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_REVIEW)),
):
    """Advance to the next review stage."""
    application = _get_application_or_404(repo, application_id)

    current_status = ApplicationStatus(application.get("status", "draft"))
    current_stage = application.get("current_stage")

    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="advance",
        user_id=user.user_id,
        user_role=user.role,
        current_stage=current_stage,
        events_repository=events_repo,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error,
        )

    repo.update(application_id, {
        "status": result.new_status,
        "current_stage": result.stage_key,
    })

    return {
        "application_id": str(application_id),
        "previous_status": result.previous_status,
        "new_status": result.new_status,
        "current_stage": result.stage_key,
        "workflow_event": result.workflow_event,
    }


@router.post("/applications/{application_id}/request-info")
async def request_information(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_REVIEW)),
):
    """Request additional information — UNDER_REVIEW → RETURNED."""
    application = _get_application_or_404(repo, application_id)

    current_status = ApplicationStatus(application.get("status", "draft"))
    current_stage = application.get("current_stage")

    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="request_info",
        user_id=user.user_id,
        user_role=user.role,
        current_stage=current_stage,
        events_repository=events_repo,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error,
        )

    repo.update(application_id, {
        "status": result.new_status,
        "current_stage": result.stage_key,
    })

    return {
        "application_id": str(application_id),
        "previous_status": result.previous_status,
        "new_status": result.new_status,
        "current_stage": result.stage_key,
        "workflow_event": result.workflow_event,
    }


@router.post("/applications/{application_id}/respond")
async def respond_to_query(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Respond to a query — RETURNED/INCOMPLETE → UNDER_REVIEW."""
    application = _get_application_or_404(repo, application_id)

    current_status = ApplicationStatus(application.get("status", "draft"))
    current_stage = application.get("current_stage")

    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="respond",
        user_id=user.user_id,
        user_role=user.role,
        current_stage=current_stage,
        events_repository=events_repo,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error,
        )

    repo.update(application_id, {
        "status": result.new_status,
        "current_stage": result.stage_key,
    })

    return {
        "application_id": str(application_id),
        "previous_status": result.previous_status,
        "new_status": result.new_status,
        "current_stage": result.stage_key,
        "workflow_event": result.workflow_event,
    }


@router.post("/applications/{application_id}/assign")
async def assign_application(
    application_id: UUID,
    officer_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_ASSIGN)),
):
    """Assign an application to a reviewer/officer."""
    _get_application_or_404(repo, application_id)

    if not can_assign(user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can assign applications",
        )

    repo.update(application_id, {
        "assigned_officer_id": str(officer_id),
    })

    return {
        "application_id": str(application_id),
        "assigned_officer_id": str(officer_id),
    }


@router.post("/applications/{application_id}/approve")
async def approve_application(
    application_id: UUID,
    reason: str = "",
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_DECIDE)),
):
    """Approve an application — UNDER_REVIEW → APPROVED."""
    application = _get_application_or_404(repo, application_id)

    current_status = ApplicationStatus(application.get("status", "draft"))
    current_stage = application.get("current_stage")

    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="approve",
        user_id=user.user_id,
        user_role=user.role,
        current_stage=current_stage,
        metadata={"reason": reason} if reason else None,
        events_repository=events_repo,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error,
        )

    repo.update(application_id, {
        "status": result.new_status,
        "current_stage": result.stage_key,
        "decision_outcome": "approved",
        "decision_reason": reason or None,
    })

    return {
        "application_id": str(application_id),
        "previous_status": result.previous_status,
        "new_status": result.new_status,
        "workflow_event": result.workflow_event,
    }


@router.post("/applications/{application_id}/refuse")
async def refuse_application(
    application_id: UUID,
    reason: str = "",
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_DECIDE)),
):
    """Refuse an application — UNDER_REVIEW → REFUSED."""
    application = _get_application_or_404(repo, application_id)

    current_status = ApplicationStatus(application.get("status", "draft"))
    current_stage = application.get("current_stage")

    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="refuse",
        user_id=user.user_id,
        user_role=user.role,
        current_stage=current_stage,
        metadata={"reason": reason} if reason else None,
        events_repository=events_repo,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error,
        )

    repo.update(application_id, {
        "status": result.new_status,
        "current_stage": result.stage_key,
        "decision_outcome": "refused",
        "decision_reason": reason or None,
    })

    return {
        "application_id": str(application_id),
        "previous_status": result.previous_status,
        "new_status": result.new_status,
        "workflow_event": result.workflow_event,
    }


@router.post("/applications/{application_id}/withdraw")
async def withdraw_application(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Withdraw an application (applicant only)."""
    application = _get_application_or_404(repo, application_id)

    current_status = ApplicationStatus(application.get("status", "draft"))
    current_stage = application.get("current_stage")

    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="withdraw",
        user_id=user.user_id,
        user_role=user.role,
        current_stage=current_stage,
        events_repository=events_repo,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error,
        )

    repo.update(application_id, {
        "status": result.new_status,
        "current_stage": result.stage_key,
    })

    return {
        "application_id": str(application_id),
        "previous_status": result.previous_status,
        "new_status": result.new_status,
        "workflow_event": result.workflow_event,
    }
