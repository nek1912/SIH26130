"""Orchestration endpoint — readiness/blocking status for an application."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    get_applications_repository,
    get_documents_repository,
    get_project_facts_repository,
)
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.orchestration.service import orchestrate_application_full
from app.repositories.applications import ApplicationsRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.dependencies import load_approval_dependencies
from app.seed.documents import load_document_requirements

router = APIRouter()


@router.get("/applications/{application_id}/orchestration")
async def get_application_orchestration(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    facts_repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    docs_repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get orchestration readiness status for an application.

    Returns per-approval readiness, blockers, next action, and overall status.
    """
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    project_id = application.get("project_id")

    # Load project facts
    facts = {}
    if project_id:
        facts_record = facts_repo.get_by_project(project_id)
        if facts_record:
            exclude_keys = ("id", "project_id", "created_at", "updated_at")
            facts = {k: v for k, v in facts_record.items() if k not in exclude_keys}

    # Load documents
    uploaded_docs = docs_repo.list_documents_for_application(str(application_id))
    doc_requirements = load_document_requirements()

    # Load seed data
    rules = load_approval_rules()
    authorities = load_approval_authorities()
    dependencies = load_approval_dependencies()

    # No approvals "obtained" for a single-application view
    obtained: set[str] = set()

    # Determine all approval IDs to evaluate
    all_approval_ids = [f"A{i:02d}" for i in range(1, 19)]

    # Run orchestration
    result = orchestrate_application_full(
        application_id=str(application_id),
        project_facts=facts,
        approval_rules=rules,
        approval_authorities=authorities,
        dependencies=dependencies,
        all_approval_ids=all_approval_ids,
        document_requirements=doc_requirements,
        uploaded_documents=uploaded_docs,
        extraction_results=[],
        validation_results=[],
        consistency_result=None,
        sla_info=None,
        obtained_approvals=obtained,
    )

    return result.model_dump()
