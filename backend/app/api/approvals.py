"""Approvals and obligations endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_approvals_repository, get_obligations_repository
from app.auth.dependencies import require_permission
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.approvals import ApprovalsRepository
from app.repositories.obligations import ObligationsRepository
from app.rules.engine import evaluate_applicability
from app.rules.models import EntityProfile, Obligation

router = APIRouter()


@router.get("/approvals")
async def list_approvals(
    repo: ApprovalsRepository = Depends(get_approvals_repository),
    user: UserContext = Depends(require_permission(Permission.MODULE_VIEW)),
):
    """List all active approvals."""
    return repo.get_active()


@router.get("/approvals/{approval_id}")
async def get_approval(
    approval_id: UUID,
    repo: ApprovalsRepository = Depends(get_approvals_repository),
    user: UserContext = Depends(require_permission(Permission.MODULE_VIEW)),
):
    """Get an approval with its rules."""
    approval = repo.get_with_rules(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.get("/obligations")
async def list_obligations(
    repo: ObligationsRepository = Depends(get_obligations_repository),
    user: UserContext = Depends(require_permission(Permission.MODULE_VIEW)),
):
    """List all obligations."""
    return repo.get_all_active()


@router.post("/obligations/applicable")
async def get_applicable_obligations(
    entity_type: str,
    sector: str,
    jurisdictions: list[str] = [],
    headcount: int = 0,
    annual_turnover_inr: float = 0,
    repo: ObligationsRepository = Depends(get_obligations_repository),
    user: UserContext = Depends(require_permission(Permission.MODULE_VIEW)),
):
    """Get obligations applicable to an entity profile."""
    profile = EntityProfile(
        entity_type=entity_type,
        sector=sector,
        jurisdictions=jurisdictions,
        headcount=headcount,
        annual_turnover_inr=annual_turnover_inr,
    )
    obligations = repo.get_all_active()
    obligation_models = [Obligation(**o) for o in obligations]
    results = evaluate_applicability(obligation_models, profile)
    return [r.model_dump() for r in results]
