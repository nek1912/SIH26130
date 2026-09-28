"""Approvals and obligations endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_approvals_repository, get_obligations_repository
from app.auth.dependencies import get_current_user, require_permission
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.approvals import ApprovalsRepository
from app.repositories.obligations import ObligationsRepository
from app.rules.applicability import (
    evaluate_approval_applicability,
    summarize_evaluations,
)
from app.rules.engine import evaluate_applicability
from app.rules.models import (
    AndNode,
    ApprovalEvaluationRequest,
    ApprovalEvaluationResponse,
    ApprovalRule,
    EntityProfile,
    Obligation,
    SourceRef,
)

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


@router.post("/approvals/seed")
async def seed_approvals(
    _user: UserContext = Depends(get_current_user),
    repo: ApprovalsRepository = Depends(get_approvals_repository),
) -> dict[str, int]:
    """Seed the canonical A01–A18 approval catalog.

    Idempotent: skips codes that already exist with matching name and
    authority. A same-code row with a different name/authority fails
    loudly (409) instead of being re-identified — human mapping is
    required (see docs/approval-identity-verification.md).
    """
    from app.seed.approval_catalog import load_approval_catalog

    created = 0
    skipped = 0
    for record in load_approval_catalog():
        existing = repo.get_by_code(record["code"])
        if not existing:
            repo.create(record)
            created += 1
            continue
        if (
            existing.get("name") != record["name"]
            or existing.get("authority") != record["authority"]
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Approval code {record['code']} already exists with a "
                    "different name/authority; human mapping required "
                    "(see docs/approval-identity-verification.md)."
                ),
            )
        skipped += 1

    return {
        "approvals_seeded": created,
        "approvals_skipped": skipped,
        "total_catalog": len(load_approval_catalog()),
    }


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


@router.post("/approvals/evaluate", response_model=ApprovalEvaluationResponse)
async def evaluate_approvals(
    request: ApprovalEvaluationRequest,
    repo: ApprovalsRepository = Depends(get_approvals_repository),
    user: UserContext = Depends(require_permission(Permission.MODULE_VIEW)),
):
    """Evaluate approval applicability for a project.

    Accepts arbitrary project facts and returns detailed evaluation results
    for each approval rule. Results include:
    - applies/does_not_apply/conditional/insufficient_data
    - reason with triggered facts
    - required/missing inputs
    - authority and source references

    Rules are data-driven — new approvals can be added without changing
    engine code.
    """
    # Get all active approvals
    approvals = repo.get_active()
    approval_authorities = {str(a["id"]): a.get("authority", "") for a in approvals}

    # Get all approval rules
    all_rules: list[ApprovalRule] = []
    for approval in approvals:
        approval_id = str(approval["id"])
        rules_data = repo.get_rules_for_approval(UUID(approval_id))
        for rule_data in rules_data:
            # Parse source_refs from JSONB
            source_refs_raw = rule_data.get("source_refs", [])
            source_refs = [SourceRef(**sr) for sr in source_refs_raw]

            # Parse condition trees from JSONB — supports both flat
            # conditions (backward-compatible) and nested AND/OR/NOT trees.
            # Flat lists are wrapped in an AndNode to preserve AND semantics.
            raw_conditions = rule_data.get("applicability_conditions", [])
            if len(raw_conditions) > 1:
                # Multiple flat conditions → implicit AND
                conditions = [AndNode(conditions=raw_conditions)]
            else:
                conditions = raw_conditions

            all_rules.append(
                ApprovalRule(
                    id=str(rule_data["id"]),
                    approval_id=approval_id,
                    obligation_id=rule_data.get("obligation_id"),
                    applicability_conditions=conditions,
                    source_refs=source_refs,
                    version=rule_data.get("version", "1"),
                    active=rule_data.get("active", True),
                )
            )

    # Filter to specific approvals if requested
    approval_ids = request.approval_ids

    # Evaluate
    evaluations = evaluate_approval_applicability(
        rules=all_rules,
        project_facts=request.project_facts,
        approval_authorities=approval_authorities,
        approval_ids=approval_ids,
    )

    summary = summarize_evaluations(evaluations)

    return ApprovalEvaluationResponse(evaluations=evaluations, summary=summary)
