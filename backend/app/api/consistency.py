"""API endpoints for cross-document consistency checks."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    get_applications_repository,
    get_consistency_repository,
)
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.consistency.engine import check_application_consistency
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.seed.pack import UnknownPackError, resolve_persisted_pack

router = APIRouter()


def _get_application(
    application_id: str,
    user: UserContext,
    app_repo: ApplicationsRepository,
) -> dict:
    """Get application and verify ownership. Raises 404/403."""
    application = app_repo.get_by_id(UUID(application_id))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)
    return application


@router.post("/applications/{application_id}/consistency/check")
async def run_consistency_check(
    application_id: str,
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
    app_repo: ApplicationsRepository = Depends(get_applications_repository),
    repo: ConsistencyRepository = Depends(get_consistency_repository),
):
    """Run a cross-document consistency check for an application."""
    application = _get_application(application_id, user, app_repo)

    # Get extracted fields and document mapping
    fields_data = repo.get_extracted_fields_for_application(application_id)
    doc_map = repo.get_document_req_map(application_id)

    # Convert to ExtractedField models
    from app.extraction.models import ExtractedField

    fields = [ExtractedField(**f) for f in fields_data]

    # Run engine with the application's persisted pack rules
    try:
        pack = resolve_persisted_pack(
            application.get("jurisdiction"), application.get("pack_version")
        )
    except UnknownPackError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    rules = pack.consistency_rules
    result = check_application_consistency(application_id, fields, rules, doc_map)

    # Persist: delete previous, store new
    repo.delete_previous_results(application_id)
    now = datetime.now(UTC).isoformat()
    result_row = repo.create_result(
        application_id, result.outcome.value, now, result.rule_version
    )

    findings_data = [
        {
            "result_id": result_row["id"],
            "application_id": application_id,
            "rule_id": f.rule_id,
            "canonical_field": f.canonical_field,
            "outcome": f.outcome.value,
            "observed_values": f.observed_values,
            "expected_relationship": f.expected_relationship,
            "message": f.message,
            "source_ref": f.source_ref,
        }
        for f in result.findings
    ]
    repo.create_findings(findings_data)

    return {
        "application_id": result.application_id,
        "outcome": result.outcome.value,
        "findings": [
            {
                "rule_id": f.rule_id,
                "canonical_field": f.canonical_field,
                "outcome": f.outcome.value,
                "observed_values": f.observed_values,
                "expected_relationship": f.expected_relationship,
                "message": f.message,
                "source_ref": f.source_ref,
            }
            for f in result.findings
        ],
        "checked_at": now,
        "rule_version": result.rule_version,
    }


@router.get("/applications/{application_id}/consistency")
async def get_consistency(
    application_id: str,
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
    app_repo: ApplicationsRepository = Depends(get_applications_repository),
    repo: ConsistencyRepository = Depends(get_consistency_repository),
):
    """Get the latest consistency check result for an application."""
    _get_application(application_id, user, app_repo)

    result_row = repo.get_latest_result(application_id)
    if not result_row:
        raise HTTPException(status_code=404, detail="No consistency check found")

    findings = repo.list_findings_for_result(result_row["id"])

    return {
        "application_id": result_row["application_id"],
        "outcome": result_row["outcome"],
        "findings": [
            {
                "rule_id": f["rule_id"],
                "canonical_field": f["canonical_field"],
                "outcome": f["outcome"],
                "observed_values": f["observed_values"],
                "expected_relationship": f["expected_relationship"],
                "message": f["message"],
                "source_ref": f["source_ref"],
            }
            for f in findings
        ],
        "checked_at": result_row["checked_at"],
        "rule_version": result_row["rule_version"],
    }
