"""Project endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.api.deps import (
    get_active_jurisdiction,
    get_project_facts_repository,
    get_project_repository,
)
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
    jurisdiction: str = Depends(get_active_jurisdiction),
    requested_jurisdiction: str | None = Query(
        default=None,
        description=(
            "Explicit regulatory jurisdiction for the new project "
            "(e.g. 'IN-MH' for the Maharashtra demo). Must be a known pack; "
            "when omitted the server default applies. Never changes the default."
        ),
    ),
):
    """Create a new project.

    Regulatory identity is server-derived: an explicit
    ``requested_jurisdiction`` (strictly validated against known packs)
    wins, otherwise the active default applies. Clients can never set
    pack_version directly and the global default is never modified.
    """
    from app.seed.pack import DEFAULT_PACK_VERSIONS

    effective_jurisdiction = requested_jurisdiction or jurisdiction
    if effective_jurisdiction not in DEFAULT_PACK_VERSIONS:
        raise HTTPException(
            status_code=422, detail=f"Unknown jurisdiction {effective_jurisdiction!r}"
        )
    data = {
        "name": name,
        "description": description,
        "jurisdiction": effective_jurisdiction,
        "pack_version": DEFAULT_PACK_VERSIONS[effective_jurisdiction],
    }
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


@router.get("/projects/{project_id}/approval-codes")
async def list_project_approval_codes(
    project_id: UUID,
    project_repo: ProjectRepository = Depends(get_project_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """List assessable approval codes for a project.

    Read-only projection of the project's persisted regulatory pack
    (authorities included). The UI uses this to offer per-code assessment
    without hardcoding pack contents. No regulatory evaluation happens here.
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

    codes = sorted({rule.approval_id for rule in pack.approval_rules})
    return {
        "jurisdiction": pack.jurisdiction,
        "pack_version": project.get("pack_version"),
        "approvals": [
            {
                "approval_code": code,
                "authority": pack.approval_authorities.get(code, ""),
            }
            for code in codes
        ],
    }


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
    facts_json: dict[str, Any] | None = Body(default=None),
    repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Create or update project facts.

    Extended ``facts_json`` keys are validated against the persisted
    project's jurisdiction vocabulary (MH registry for IN-MH; legacy
    permissive behavior for IN-GJ). ``jurisdictions[]`` remains
    applicant entity data and never selects the vocabulary.
    """
    from app.rules.facts import (
        GJ_JURISDICTION,
        MH_JURISDICTION,
        FactValidationError,
        validate_fact_value,
    )
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

    data = {
        "entity_type": entity_type,
        "sector": sector,
        "jurisdictions": jurisdictions,
        "headcount": headcount,
        "annual_turnover_inr": annual_turnover_inr,
    }
    if facts_json is not None:
        if pack.jurisdiction == MH_JURISDICTION:
            for field_name, value in facts_json.items():
                try:
                    validate_fact_value(MH_JURISDICTION, field_name, value)
                except FactValidationError as exc:
                    raise HTTPException(
                        status_code=422, detail=str(exc)
                    ) from exc
        elif pack.jurisdiction != GJ_JURISDICTION:  # pragma: no cover
            raise HTTPException(
                status_code=422,
                detail=f"Unknown jurisdiction {pack.jurisdiction!r}",
            )
        # IN-GJ keeps legacy permissive behavior (typed params only
        # were ever validated; facts_json historically open).
        data["facts_json"] = facts_json
    return repo.upsert(project_id, data)
