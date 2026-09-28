"""FastAPI incentive scheme endpoints — listing and project assessment."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.auth.models import UserContext
from app.incentives.engine import assess_all_schemes
from app.incentives.models import IncentiveAssessmentRequest
from app.seed.incentives import scheme_to_dict
from app.seed.pack import DEFAULT_JURISDICTION, load_regulatory_pack

router = APIRouter()


def _get_schemes() -> list[Any]:
    """Load all incentive schemes from the active regulatory pack."""
    return load_regulatory_pack(DEFAULT_JURISDICTION).incentive_schemes


@router.get("/incentives")
async def list_incentive_schemes(
    category: str | None = Query(
        default=None, description="Filter by scheme category"
    ),
    _user: UserContext = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List all available government support/incentive schemes.

    Optionally filter by category (capital_subsidy, interest_subsidy, etc.).
    """
    schemes = _get_schemes()
    result = [scheme_to_dict(s) for s in schemes if s.active]
    if category:
        result = [r for r in result if r.get("category") == category]
    return result


@router.get("/incentives/{scheme_id}")
async def get_incentive_scheme(
    scheme_id: str,
    _user: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    """Get details for a specific incentive scheme."""
    schemes = _get_schemes()
    for s in schemes:
        if s.id == scheme_id:
            return scheme_to_dict(s)
    raise HTTPException(
        status_code=404, detail=f"Scheme {scheme_id} not found"
    )


@router.post("/incentives/assess")
async def assess_incentives(
    request: IncentiveAssessmentRequest,
    _user: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    """Assess project-specific incentive relevance.

    Evaluates all (or filtered) schemes against the provided project facts.
    Returns deterministic relevance assessments with source traceability.
    """
    schemes = _get_schemes()
    result = assess_all_schemes(
        schemes=schemes,
        project_facts=request.project_facts,
        project_id="",
        scheme_ids=request.scheme_ids,
    )
    return result.model_dump()
