"""Regulatory explanation service — template-based source-grounded explanations.

This module generates deterministic, source-cited explanations for approval
rules and regulatory queries. No LLM is used; all explanations are built
from rule metadata + retrieved source evidence.

Core principle:
  Deterministic rules decide → RAG retrieves → Templates explain → Human decides
"""
from __future__ import annotations

from typing import Any

from app.regulatory.models import (
    Citation,
    EvidenceState,
    RegulatoryExplanation,
)
from app.regulatory.retrieval import (
    get_citations_for_source_ids,
    search_chunks_with_rank,
)
from app.rules.models import ApprovalRule, SourceRef


def _source_refs_to_ids(source_refs: list[SourceRef]) -> list[str]:
    """Extract source IDs from SourceRef objects."""
    return [ref.source_id for ref in source_refs if ref.source_id]


def _extract_source_ids_from_rules(
    approval_rules: list[ApprovalRule],
    approval_id: str,
) -> list[str]:
    """Extract all source IDs referenced by rules for a given approval."""
    ids: list[str] = []
    for rule in approval_rules:
        if rule.approval_id == approval_id:
            ids.extend(_source_refs_to_ids(rule.source_refs))
    return list(dict.fromkeys(ids))  # deduplicate, preserve order


def _build_applicability_explanation(
    approval_id: str,
    applicability_result: str,
    reason: str,
    source_refs: list[SourceRef],
    citations: list[Citation],
) -> tuple[str, EvidenceState]:
    """Build a deterministic explanation for why an approval applies/doesn't."""
    citation_summary = ""
    if citations:
        cited_names = [f"{c.title} ({c.authority})" for c in citations[:3]]
        citation_summary = f" Source(s): {'; '.join(cited_names)}."

    if applicability_result in ("does_not_apply", "DOES_NOT_APPLY"):
        answer = (
            f"Approval {approval_id} does not apply to this project. "
            f"{reason}"
            f"{citation_summary}"
        )
        evidence = EvidenceState.SUFFICIENT
    elif applicability_result in ("conditional", "CONDITIONAL"):
        answer = (
            f"Approval {approval_id} conditionally applies. "
            f"{reason}"
            f"{citation_summary}"
        )
        evidence = EvidenceState.PARTIAL
    elif applicability_result in ("insufficient_data", "INSUFFICIENT_DATA"):
        answer = (
            f"Cannot determine applicability for {approval_id}: "
            f"insufficient project data. {reason}"
        )
        evidence = EvidenceState.INSUFFICIENT
    else:
        answer = (
            f"Approval {approval_id} applies to this project. "
            f"{reason}"
            f"{citation_summary}"
        )
        evidence = EvidenceState.SUFFICIENT if citations else EvidenceState.PARTIAL

    return answer, evidence


def explain_approval(
    client: Any,
    approval_id: str,
    approval_rules: list[ApprovalRule],
    applicability_result: str = "unknown",
    reason: str = "",
) -> RegulatoryExplanation:
    """Generate a source-grounded explanation for an approval's applicability.

    This does NOT recalculate applicability — it uses the existing
    deterministic result and retrieves source evidence to explain it.
    """
    # 1. Extract source IDs from the approval's rules
    source_ids = _extract_source_ids_from_rules(approval_rules, approval_id)

    # 2. Retrieve citations from database
    citations = get_citations_for_source_ids(client, source_ids) if source_ids else []

    # 3. Build explanation from the deterministic result
    answer, evidence = _build_applicability_explanation(
        approval_id, applicability_result, reason,
        [ref for rule in approval_rules if rule.approval_id == approval_id
         for ref in rule.source_refs],
        citations,
    )

    return RegulatoryExplanation(
        answer=answer,
        citations=citations,
        evidence_state=evidence,
        query=f"applicability:{approval_id}",
        approval_id=approval_id,
    )


def answer_query(
    client: Any,
    query: str,
    limit: int = 5,
) -> RegulatoryExplanation:
    """Answer a free-text regulatory query using RAG.

    Retrieves relevant source chunks and builds a cited response.
    If no sources contain sufficient evidence, returns INSUFFICIENT_EVIDENCE.
    """
    if not query.strip():
        return RegulatoryExplanation(
            answer="Please provide a regulatory question.",
            citations=[],
            evidence_state=EvidenceState.INSUFFICIENT,
            query=query,
        )

    # 1. Search for relevant chunks
    rows = search_chunks_with_rank(client, query, limit=limit)

    if not rows:
        return RegulatoryExplanation(
            answer=(
                "No relevant regulatory sources found for this query. "
                "The available Gujarat regulatory dataset may not cover this topic. "
                "Please consult the official sources directly."
            ),
            citations=[],
            evidence_state=EvidenceState.INSUFFICIENT,
            query=query,
        )

    # 2. Build citations from search results
    source_ids = list({r.get("source_id") for r in rows if r.get("source_id")})

    # Fetch source records for context
    source_citations = get_citations_for_source_ids(client, source_ids)

    # Build chunk-level citations
    citations: list[Citation] = []
    for row in rows:
        source = next(
            (sc for sc in source_citations if sc.source_id == row.get("source_id")),
            None,
        )
        if source:
            citations.append(
                Citation(
                    source_id=source.source_id,
                    title=source.title,
                    authority=source.authority,
                    url=source.url,
                    source_type=source.source_type,
                    excerpt=row.get("chunk_text", ""),
                    relevance_rank=float(row.get("rank", 0.0)) if row.get("rank") else 0.5,
                )
            )

    # 3. Deduplicate by source_id, keep best excerpt
    best_by_source: dict[str, Citation] = {}
    for c in citations:
        sid = c.source_id
        if sid not in best_by_source or c.relevance_rank > best_by_source[sid].relevance_rank:
            best_by_source[sid] = c
    deduped = sorted(best_by_source.values(), key=lambda x: x.relevance_rank, reverse=True)

    # 4. Build answer
    if not deduped:
        return RegulatoryExplanation(
            answer="No relevant sources identified for this query.",
            citations=[],
            evidence_state=EvidenceState.INSUFFICIENT,
            query=query,
        )

    source_names = [f"{c.title} ({c.authority})" for c in deduped[:3]]
    answer = (
        f"Based on the Gujarat regulatory dataset, the following source(s) are relevant: "
        f"{'; '.join(source_names)}. "
        f"Please refer to the cited sources for the authoritative regulatory text."
    )

    evidence = EvidenceState.SUFFICIENT if len(deduped) >= 1 else EvidenceState.PARTIAL

    return RegulatoryExplanation(
        answer=answer,
        citations=deduped,
        evidence_state=evidence,
        query=query,
    )


def explain_orchestration_with_citations(
    client: Any,
    approval_id: str,
    approval_rules: list[ApprovalRule],
    orchestration_explanation: str,
) -> RegulatoryExplanation:
    """Enrich an existing orchestration explanation with source citations.

    This takes the deterministic orchestration result and adds regulatory
    source evidence. It does NOT override or modify the orchestration logic.
    """
    source_ids = _extract_source_ids_from_rules(approval_rules, approval_id)
    citations = get_citations_for_source_ids(client, source_ids) if source_ids else []

    if citations:
        cited_names = [f"{c.title}" for c in citations[:3]]
        answer = (
            f"{orchestration_explanation}\n\n"
            f"Regulatory basis: {'; '.join(cited_names)}."
        )
        evidence = EvidenceState.SUFFICIENT
    else:
        answer = (
            f"{orchestration_explanation}\n\n"
            f"No regulatory sources found in the dataset for approval {approval_id}."
        )
        evidence = EvidenceState.INSUFFICIENT

    return RegulatoryExplanation(
        answer=answer,
        citations=citations,
        evidence_state=evidence,
        query=f"orchestration:{approval_id}",
        approval_id=approval_id,
    )
