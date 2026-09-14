"""Applications endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_applications_repository
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
    require_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.applications import ApplicationsRepository

router = APIRouter()


@router.get("/applications")
async def list_applications(
    status: str | None = Query(None, description="Filter by status"),
    assigned_to: UUID | None = Query(None, description="Filter by assigned officer"),
    applicant_id: UUID | None = Query(None, description="Filter by applicant (staff only)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    repo: ApplicationsRepository = Depends(get_applications_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """List all applications with optional filters (staff only).

    Supports filtering by status, assigned officer, and applicant.
    Returns paginated results with total count.
    """
    from app.workflow.models import ApplicationStatus

    parsed_status = None
    if status:
        try:
            ApplicationStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status: '{status}'. Valid: {[s.value for s in ApplicationStatus]}",
            )
        parsed_status = [status]

    # Applicants can only see their own applications
    effective_applicant_id = None
    if user.role.value == "applicant":
        effective_applicant_id = str(user.user_id)
    elif applicant_id:
        effective_applicant_id = str(applicant_id)

    items, total = repo.list_all_with_filters(
        status=parsed_status,
        assigned_to=str(assigned_to) if assigned_to else None,
        applicant_id=effective_applicant_id,
        page=page,
        page_size=page_size,
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/applications")
async def create_application(
    project_id: UUID,
    approval_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Create a new application."""
    data = {
        "project_id": str(project_id),
        "approval_id": str(approval_id),
        "status": "draft",
        "applicant_id": str(user.user_id),
    }
    return repo.create_with_reference(data)


@router.get("/applications/{application_id}")
async def get_application(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get an application by ID."""
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)
    return application


@router.get("/projects/{project_id}/applications")
async def list_project_applications(
    project_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """List all applications for a project."""
    return repo.get_by_project(project_id)
