"""Regulatory data models — source records, chunks, citations, and explanations."""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceState(StrEnum):
    """Evidence sufficiency state for explanations."""
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    PARTIAL = "partial"


class SourceRecord(BaseModel):
    """A verified regulatory source from the Gujarat dataset."""
    id: str
    title: str
    authority: str
    source_type: str
    url: str
    jurisdiction: str = "IN-GJ"
    source_class: str = "Official"
    notes: str = ""
    checked_date: str = ""
    trust_tier: str = "govt-portal"
    content_hash: str = ""


class SourceChunk(BaseModel):
    """A searchable text chunk from a regulatory source."""
    id: str | None = None
    source_id: str
    chunk_text: str
    chunk_index: int = 0
    metadata: dict = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    """A chunk returned from search with relevance ranking."""
    chunk: SourceChunk
    rank: float
    source: SourceRecord | None = None


class Citation(BaseModel):
    """A source citation for an explanation."""
    source_id: str
    title: str
    authority: str
    url: str
    source_type: str
    excerpt: str
    relevance_rank: float


class ExplanationRequest(BaseModel):
    """Request for a regulatory explanation."""
    query: str
    approval_id: str | None = None
    application_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)


class RegulatoryExplanation(BaseModel):
    """A source-grounded regulatory explanation with citations."""
    answer: str
    citations: list[Citation]
    evidence_state: EvidenceState
    query: str
    approval_id: str | None = None
    application_id: str | None = None
