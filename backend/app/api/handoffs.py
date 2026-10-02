"""Manual government handoff routes.

Truthful bookkeeping around external authority portals. No route here
contacts a government system: portal links are plain anchors, and every
status is applicant-reported unless staff-verified.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_applications_repository,
    get_consistency_repository,
    get_documents_repository,
    get_handoffs_repository,
    get_project_facts_repository,
    get_workflow_events_repository,
)
from app.api.orchestration import _load_baseline_inputs
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
    require_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.handoff.models import (
    InitiateHandoffRequest,
    RecordSubmissionRequest,
    ReportStatusRequest,
    VerifyHandoffRequest,
)
from app.handoff.service import (
    HandoffStateError,
    apply_report,
    apply_submission,
    apply_verification,
    handoff_event_metadata,
    prepare_initiation,
)
from app.orchestration.models import OrchestrationStatus
from app.orchestration.service import orchestrate_application_full
from app.repositories.applications import ApplicationsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.handoffs import HandoffsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.workflow_events import WorkflowEventsRepository

router = APIRouter()


def _handoff_or_404(
    store: HandoffsRepository, handoff_id: UUID, application_id: UUID
) -> dict:
    row = store.get_by_id(handoff_id)
    if not row or str(row.get("application_id")) != str(application_id):
        raise HTTPException(status_code=404, detail="Handoff not found")
    return row


def _write_event(
    events_repo: WorkflowEventsRepository,
    application_id: str,
    record: dict,
    action: str,
    actor: str,
) -> None:
    meta = handoff_event_metadata(record, action, actor)
    events_repo.create(
        {
            "application_id": application_id,
            "from_stage": None,
            "to_stage": record.get("status"),
            "action": action,
            "performed_by_id": actor,
            "metadata": meta,
        }
    )


def _run_orchestration(inputs: dict):
    pack = inputs.get("pack")
    return orchestrate_application_full(
        application_id=inputs["application_id"],
        project_facts=inputs["facts"],
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
        fact_provenance=inputs.get("fact_provenance"),
        approval_compositions=inputs.get(
            "approval_compositions",
            pack.approval_compositions if pack is not None else None,
        ),
    )


def _ready_approvals_view(orch, inputs: dict) -> list[dict]:
    """READY approvals enriched with catalog portal data (server-sourced)."""
    view = []
    for aid, approval in orch.approvals.items():
        if approval.status != OrchestrationStatus.READY:
            continue
        entry = inputs["pack"].get_portal_entry(aid)
        if entry is None:
            continue
        missing_docs = [
            d.requirement_key
            for d in approval.documents
            if d.blocking and d.readiness == "missing"
        ]
        view.append(
            {
                "approval_code": aid,
                "authority": entry["authority"],
                "external_system": entry["external_system"],
                "portal_url": entry["portal_url"],
                "portal_kind": entry["portal_kind"],
                "document_readiness": approval.document_readiness,
                "missing_documents": missing_docs,
            }
        )
    return view


@router.get("/applications/{application_id}/handoffs")
async def list_handoffs(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    facts_repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    docs_repo: DocumentsRepository = Depends(get_documents_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    consistency_repo: ConsistencyRepository = Depends(
        get_consistency_repository
    ),
    store: HandoffsRepository = Depends(get_handoffs_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """List handoff records plus currently-READY approvals. Read-only."""
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    rows = store.list_for_application(application_id)
    inputs = _load_baseline_inputs(
        application, application_id, repo, facts_repo, docs_repo, events_repo,
        consistency_repo,
    )
    orch = _run_orchestration(inputs)
    current = {
        aid: (o.status == OrchestrationStatus.READY)
        for aid, o in orch.approvals.items()
    }
    enriched = [
        {**row, "currently_ready": bool(current.get(row.get("approval_code"), False))}
        for row in rows
    ]
    return {"handoffs": enriched, "ready_approvals": _ready_approvals_view(orch, inputs)}


@router.post("/applications/{application_id}/handoffs/initiate")
async def initiate_handoff(
    application_id: UUID,
    request: InitiateHandoffRequest,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    facts_repo: ProjectFactsRepository = Depends(get_project_facts_repository),
    docs_repo: DocumentsRepository = Depends(get_documents_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    consistency_repo: ConsistencyRepository = Depends(
        get_consistency_repository
    ),
    store: HandoffsRepository = Depends(get_handoffs_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Applicant records intent to apply on the official portal (READY only)."""
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    inputs = _load_baseline_inputs(
        application, application_id, repo, facts_repo, docs_repo, events_repo,
        consistency_repo,
    )
    pack = inputs["pack"]
    if pack.get_portal_entry(request.approval_code) is None:
        raise HTTPException(
            status_code=422, detail=f"Unknown approval_code '{request.approval_code}'"
        )
    if store.get_active_for_approval(application_id, request.approval_code):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active handoff already exists for this approval",
        )

    orch = _run_orchestration(inputs)
    approval = orch.approvals.get(request.approval_code)
    orch_status = approval.status.value if approval else "insufficient_data"

    try:
        record = prepare_initiation(
            application_id=str(application_id),
            approval_code=request.approval_code,
            orchestration_status=orch_status,
            reported_by=str(user.user_id),
            portal_entry=pack.get_portal_entry(request.approval_code),
        )
    except HandoffStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=exc.detail
        ) from exc

    created = store.create(record)
    _write_event(
        events_repo, str(application_id), created, "handoff.initiate",
        str(user.user_id),
    )
    return {**created, "currently_ready": True}


@router.post("/applications/{application_id}/handoffs/{handoff_id}/record-submission")
async def record_submission(
    application_id: UUID,
    handoff_id: UUID,
    request: RecordSubmissionRequest,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    store: HandoffsRepository = Depends(get_handoffs_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
            Permission.APPLICATION_REVIEW,
        )
    ),
):
    """Record a manual external submission + opaque reference. No lookup."""
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)
    row = _handoff_or_404(store, handoff_id, application_id)

    try:
        updated = apply_submission(
            row,
            external_reference=request.external_reference,
            actor=str(user.user_id),
            applicant_note=request.applicant_note,
        )
    except HandoffStateError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT if exc.conflict
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=exc.detail,
        ) from exc

    saved = store.update(handoff_id, updated)
    _write_event(
        events_repo, str(application_id), saved or updated,
        "handoff.record_submission", str(user.user_id),
    )
    return saved or updated


@router.post("/applications/{application_id}/handoffs/{handoff_id}/report-status")
async def report_status(
    application_id: UUID,
    handoff_id: UUID,
    request: ReportStatusRequest,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    store: HandoffsRepository = Depends(get_handoffs_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
            Permission.APPLICATION_REVIEW,
        )
    ),
):
    """Report an external status. Always USER_REPORTED, never verified."""
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)
    row = _handoff_or_404(store, handoff_id, application_id)

    try:
        updated = apply_report(
            row,
            to_status=request.to_status.value,
            actor=str(user.user_id),
            applicant_note=request.applicant_note,
        )
    except HandoffStateError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT if exc.conflict
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=exc.detail,
        ) from exc

    saved = store.update(handoff_id, updated)
    _write_event(
        events_repo, str(application_id), saved or updated,
        "handoff.report_status", str(user.user_id),
    )
    return saved or updated


@router.post("/applications/{application_id}/handoffs/{handoff_id}/verify")
async def verify_handoff(
    application_id: UUID,
    handoff_id: UUID,
    request: VerifyHandoffRequest,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    store: HandoffsRepository = Depends(get_handoffs_repository),
    events_repo: WorkflowEventsRepository = Depends(
        get_workflow_events_repository
    ),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_REVIEW)),
):
    """Staff-only: confirm a reported external status as authoritative."""
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)
    row = _handoff_or_404(store, handoff_id, application_id)

    try:
        updated = apply_verification(
            row,
            verified_status=request.verified_status.value,
            verifier=str(user.user_id),
        )
    except HandoffStateError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT if exc.conflict
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=exc.detail,
        ) from exc

    saved = store.update(handoff_id, updated)
    _write_event(
        events_repo, str(application_id), saved or updated,
        "handoff.verify", str(user.user_id),
    )
    return saved or updated
