"""FastAPI regulatory/RAG endpoints — source search and explanation."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import (
    get_active_jurisdiction,
    get_applications_repository,
    get_consistency_repository,
    get_db_client,
    get_documents_repository,
    get_project_facts_repository,
    get_sources_repository,
    get_workflow_events_repository,
)
from app.api.orchestration import _load_baseline_inputs
from app.auth.dependencies import (
    check_application_ownership,
    get_current_user,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.db.postgres import PostgresDB
from app.regulatory.explanation import (
    answer_query,
    explain_approval,
    explain_orchestration_with_citations,
)
from app.regulatory.impact import ImpactValidationError, RehearsalInputs, rehearse_impact
from app.regulatory.impact_models import ImpactRehearseRequest
from app.regulatory.ingestion import get_seed_chunks, get_seed_source_dicts
from app.regulatory.models import ExplanationRequest
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.sources import SourcesRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.seed.pack import load_regulatory_pack

router = APIRouter()


@router.get("/sources")
async def list_sources(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _user: UserContext = Depends(get_current_user),
    repo: SourcesRepository = Depends(get_sources_repository),
) -> list[dict[str, Any]]:
    """List all regulatory sources."""
    return repo.get_all_sources(limit=limit, offset=offset)


@router.get("/sources/status")
async def source_status(
    _user: UserContext = Depends(get_current_user),
    repo: SourcesRepository = Depends(get_sources_repository),
) -> dict[str, Any]:
    """Get source ingestion status."""
    return {
        "source_count": repo.count_sources(),
        "chunk_count": repo.count_chunks(),
    }


@router.get("/sources/{source_id}")
async def get_source(
    source_id: str,
    _user: UserContext = Depends(get_current_user),
    repo: SourcesRepository = Depends(get_sources_repository),
) -> dict[str, Any]:
    """Get a source by ID with its chunks."""
    source = repo.get_by_id_text(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    chunks = repo.get_chunks_for_source(source_id)
    return {"source": source, "chunks": chunks}


@router.post("/sources/seed")
async def seed_sources(
    _user: UserContext = Depends(get_current_user),
    repo: SourcesRepository = Depends(get_sources_repository),
) -> dict[str, Any]:
    """Seed all 32 regulatory sources into the database.

    Idempotent: skips sources that already exist.
    """
    source_dicts = get_seed_source_dicts()
    chunk_dicts = get_seed_chunks()

    created_sources = 0
    for sd in source_dicts:
        existing = repo.get_by_id_text(sd["id"])
        if not existing:
            repo.create_source(sd)
            created_sources += 1

    created_chunks = 0
    for cd in chunk_dicts:
        existing_chunks = repo.get_chunks_for_source(cd["source_id"])
        if not existing_chunks:
            repo.create_chunk(cd)
            created_chunks += 1

    return {
        "sources_seeded": created_sources,
        "chunks_seeded": created_chunks,
        "total_sources": repo.count_sources(),
        "total_chunks": repo.count_chunks(),
    }


@router.post("/regulatory/explain")
async def explain_regulatory(
    request: ExplanationRequest,
    client: PostgresDB = Depends(get_db_client),
    _user: UserContext = Depends(get_current_user),
) -> dict[str, Any]:
    """Answer a regulatory query with source citations."""
    explanation = answer_query(client, request.query, limit=request.limit)
    return explanation.model_dump()


@router.get("/regulatory/approval/{approval_id}/explanation")
async def explain_approval_endpoint(
    approval_id: str,
    applicability: str = Query(default="unknown"),
    reason: str = Query(default=""),
    client: PostgresDB = Depends(get_db_client),
    _user: UserContext = Depends(get_current_user),
    jurisdiction: str = Depends(get_active_jurisdiction),
) -> dict[str, Any]:
    """Get a source-grounded explanation for an approval."""
    pack = load_regulatory_pack(jurisdiction)
    rules = pack.approval_rules
    explanation = explain_approval(
        client=client,
        approval_id=approval_id,
        approval_rules=rules,
        applicability_result=applicability,
        reason=reason,
    )
    return explanation.model_dump()


@router.get("/regulatory/orchestration/{application_id}/citations")
async def orchestration_citations(
    application_id: str,
    approval_id: str = Query(description="Specific approval to explain"),
    explanation: str = Query(default=""),
    client: PostgresDB = Depends(get_db_client),
    _user: UserContext = Depends(get_current_user),
    jurisdiction: str = Depends(get_active_jurisdiction),
) -> dict[str, Any]:
    """Enrich an orchestration result with source citations."""
    pack = load_regulatory_pack(jurisdiction)
    rules = pack.approval_rules
    result = explain_orchestration_with_citations(
        client=client,
        approval_id=approval_id,
        approval_rules=rules,
        orchestration_explanation=explanation,
    )
    return result.model_dump()


@router.post("/regulatory/changes/rehearse")
async def rehearse_regulatory_change(
    request: ImpactRehearseRequest,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    facts_repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    docs_repo: DocumentsRepository = Depends(get_documents_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    consistency_repo: ConsistencyRepository = Depends(
        get_consistency_repository
    ),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
) -> dict[str, Any]:
    """Staff-only stateless rehearsal of one regulatory change.

    Re-runs the deterministic orchestration pipeline old-vs-new against the
    selected application and returns RESULT_CHANGED / SOURCE_RELEVANT /
    NO_IMPACT. Never persists the proposed change; never writes to
    project_facts, projects, applications, documents, workflow, sources,
    or evidence stores.
    """
    try:
        application_id = UUID(str(request.application_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid application_id")
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    # Identical baseline inputs as GET orchestration (shared loader).
    # The pack resolves from the application's persisted identity.
    inputs = _load_baseline_inputs(
        application,
        application_id,
        repo,
        facts_repo,
        docs_repo,
        events_repo,
        consistency_repo,
    )
    pack = inputs["pack"]

    try:
        impact = rehearse_impact(
            request.change,
            RehearsalInputs(
                base_facts=inputs["facts"],
                approval_rules=inputs["rules"],
                approval_authorities=inputs["authorities"],
                dependencies=inputs["dependencies"],
                all_approval_ids=inputs["all_approval_ids"],
                document_requirements=inputs["doc_requirements"],
                uploaded_documents=inputs["uploaded_docs"],
                extraction_results=inputs["extraction_results"],
                validation_results=inputs["validation_results"],
                consistency_result=inputs["consistency_result"],
                sla_info=inputs["sla_info"],
                obtained_approvals=inputs["obtained"],
                evidence_gaps_by_approval=inputs["evidence_gaps_by_approval"],
                approval_compositions=pack.approval_compositions,
                known_source_ids={s.id for s in pack.sources},
                evidence_registry=list(pack.evidence_gaps),
                evidence_hints=dict(pack.evidence_hints),
            ),
        )
    except ImpactValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.detail) from exc

    return {"application_id": inputs["application_id"], **impact.model_dump()}
