"""Orchestration data models — types for per-approval readiness assessments."""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class OrchestrationStatus(StrEnum):
    READY = "ready"
    BLOCKED_BY_DEPENDENCY = "blocked_by_dependency"
    BLOCKED_BY_DOCUMENTS = "blocked_by_documents"
    REVIEW_REQUIRED = "review_required"
    INSUFFICIENT_DATA = "insufficient_data"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"


class BlockerType(StrEnum):
    DEPENDENCY = "dependency"
    DOCUMENT_MISSING = "document_missing"
    DOCUMENT_INVALID = "document_invalid"
    DOCUMENT_REVIEW_REQUIRED = "document_review_required"
    EXTRACTION_FAILED = "extraction_failed"
    CONSISTENCY_REVIEW = "consistency_review"
    INSUFFICIENT_DATA = "insufficient_data"
    SLA_BREACHED = "sla_breached"


class BlockerDetail(BaseModel):
    blocker_type: BlockerType
    description: str
    affected_approval_id: str | None
    affected_document_key: str | None
    source_ref: str
    evidence: str
    action_required: str


class DocumentReadinessSummary(BaseModel):
    requirement_key: str
    document_name: str
    readiness: str
    extraction_status: str | None
    validation_outcome: str | None
    blocking: bool
    reason: str


class ApprovalOrchestration(BaseModel):
    approval_id: str
    status: OrchestrationStatus
    applicability_result: str
    dependency_readiness: str
    document_readiness: str
    consistency_outcome: str | None
    sla_state: str | None
    blockers: list[BlockerDetail]
    documents: list[DocumentReadinessSummary]
    explanation: str
    next_action: str


class NextAction(BaseModel):
    action_type: str
    description: str
    affected_approval_id: str | None
    affected_document_key: str | None
    link_section: str


class ApplicationOrchestration(BaseModel):
    application_id: str
    overall_status: OrchestrationStatus
    approvals: dict[str, ApprovalOrchestration]
    total_blockers: int
    next_action: NextAction | None
    stage_number: int | None
    explanation: str
