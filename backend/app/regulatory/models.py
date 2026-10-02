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
    """A source citation for an explanation.

    Core fields (source_id/title/authority/url/source_type/excerpt/
    relevance_rank) are the stable contract. Jurisdiction-aware
    metadata below is additive and optional: missing stored metadata
    is exposed as None (unavailable) rather than invented.
    """
    source_id: str
    title: str
    authority: str
    url: str
    source_type: str
    excerpt: str
    relevance_rank: float
    # Additive T5 citation metadata (all optional for back-compat).
    jurisdiction: str | None = None
    checked_date: str | None = None
    trust_tier: str | None = None
    # Provision/section locator from the rule's SourceRef citation_span.
    provision: str | None = None


class ExplanationRequest(BaseModel):
    """Request for a regulatory explanation."""
    query: str
    approval_id: str | None = None
    application_id: str | None = None
    limit: int = Field(default=5, ge=1, le=20)
    # Optional jurisdiction selector for RAG retrieval (T5). None preserves
    # the server default (IN-GJ behavior unchanged). When set, retrieval
    # is strictly jurisdiction-filtered with no cross-jurisdiction fallback.
    jurisdiction: str | None = None


class RegulatoryExplanation(BaseModel):
    """A source-grounded regulatory explanation with citations."""
    answer: str
    citations: list[Citation]
    evidence_state: EvidenceState
    query: str
    approval_id: str | None = None
    application_id: str | None = None
