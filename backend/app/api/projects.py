"""Project endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_project_facts_repository, get_project_repository
from app.auth.dependencies import (
    check_project_ownership,
    require_any_permission,
    require_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository

router = APIRouter()


@router.post("/projects")
async def create_project(
    name: str,
    description: str | None = None,
    applicant_id: UUID = None,
    repo: ProjectRepository = Depends(get_project_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Create a new project."""
    data = {"name": name, "description": description}
    # Use the authenticated user's ID as the applicant unless explicitly provided
    # (and the caller has elevated privileges).
    if applicant_id and user.role in {
        Permission.APPLICATION_VIEW_ALL,
        Permission.APPLICATION_ASSIGN,
    }:
        data["applicant_id"] = str(applicant_id)
    else:
        data["applicant_id"] = str(user.user_id)
    return repo.create(data)


@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    repo: ProjectRepository = Depends(get_project_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get a project by ID."""
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    check_project_ownership(user, project)
    return project


@router.get("/projects/{project_id}/facts")
async def get_project_facts(
    project_id: UUID,
    repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get facts for a project."""
    facts = repo.get_by_project(project_id)
    if not facts:
        raise HTTPException(status_code=404, detail="Project facts not found")
    return facts


@router.post("/projects/{project_id}/facts")
async def upsert_project_facts(
    project_id: UUID,
    entity_type: str,
    sector: str,
    jurisdictions: list[str] = [],
    headcount: int = 0,
    annual_turnover_inr: float = 0,
    repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Create or update project facts."""
    data = {
        "entity_type": entity_type,
        "sector": sector,
        "jurisdictions": jurisdictions,
        "headcount": headcount,
        "annual_turnover_inr": annual_turnover_inr,
    }
    return repo.upsert(project_id, data)
