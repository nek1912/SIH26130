"""Applications endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import (
    get_applications_repository,
    get_documents_repository,
    get_project_repository,
    get_workflow_events_repository,
)
from app.auth.dependencies import (
    check_application_ownership,
    check_project_ownership,
    require_any_permission,
    require_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.applications import ApplicationsRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.seed.pack import DEFAULT_PACK_VERSIONS
from app.workflow.sla import compute_application_sla

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
    approval_code: str = Query(..., description="Approval code like A01, A02"),
    repo: ApplicationsRepository = Depends(get_applications_repository),
    doc_repo: DocumentsRepository = Depends(get_documents_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Create a new application.

    Regulatory identity (jurisdiction + pack_version) is inherited
    from the parent project — never from the approval code, the
    request, or the global default. The approval code must exist in
    the inherited pack, else 422. No A↔APR translation is performed.
    """
    from app.seed.pack import UnknownPackError, resolve_persisted_pack

    project = project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    check_project_ownership(user, project)

    try:
        pack = resolve_persisted_pack(
            project.get("jurisdiction"), project.get("pack_version")
        )
    except UnknownPackError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    known_codes = {rule.approval_id for rule in pack.approval_rules}
    if approval_code not in known_codes:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown approval_code '{approval_code}' for jurisdiction "
                f"'{pack.jurisdiction}'"
            ),
        )

    data = {
        "project_id": str(project_id),
        "approval_id": str(approval_id),
        "approval_code": approval_code,
        "status": "draft",
        "applicant_id": str(user.user_id),
        "jurisdiction": pack.jurisdiction,
        "pack_version": DEFAULT_PACK_VERSIONS[pack.jurisdiction],
    }
    application = repo.create_with_reference(data)

    # Seed document requirements from the inherited regulatory pack
    doc_reqs = pack.get_requirements_for_approval(approval_code)
    if doc_reqs:
        requirement_records = []
        for req in doc_reqs:
            requirement_records.append({
                "application_id": application["id"],
                "requirement_key": req["requirement_key"],
                "document_name": req["document_name"],
                "approval_id": approval_code,
                "domain": req["domain"],
                "requirement_level": req["requirement_level"],
                "readiness": "pending",
                "accepted_mime_types": req.get("accepted_mime_types"),
                "max_size_mb": req.get("max_size_mb"),
                "source_basis": req.get("source_basis"),
                "source_url": req.get("source_url"),
                "document_role": req.get("document_role"),
            })
        doc_repo.create_requirements_bulk(requirement_records)

    return application


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


@router.get("/applications/{application_id}/sla")
async def get_application_sla(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get SLA status for an application.

    Returns SLA info (stage, due date, remaining days, state) or null
    if no SLA applies (inactive status or no SLA target on stage).
    """
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    # Load workflow events
    events = events_repo.list_for_application(str(application_id))

    # Load approval stages
    approval_id = application.get("approval_id")
    stages = repo.get_approval_stages(approval_id) if approval_id else []

    # Compute SLA
    sla = compute_application_sla(
        status=application.get("status"),
        current_stage=application.get("current_stage"),
        submitted_at=application.get("submitted_at"),
        created_at=application.get("created_at"),
        workflow_events=events,
        stages=stages or [],
    )

    if sla is None:
        return None

    return {
        "stage_key": sla.stage_key,
        "stage_label": sla.stage_label,
        "sla_business_days": sla.sla_business_days,
        "entered_at": sla.entered_at.isoformat(),
        "due_date": sla.due_date.isoformat(),
        "used_business_days": sla.used_business_days,
        "remaining_business_days": sla.remaining_business_days,
        "overdue_business_days": sla.overdue_business_days,
        "state": sla.state,
    }
