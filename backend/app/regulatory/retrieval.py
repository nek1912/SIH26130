"""Regulatory retrieval service — full-text search over source chunks.

Uses PostgreSQL tsvector/tsquery with ts_rank_cd for relevance
ranking directly against local PostgreSQL. No external vector
database or embedding service required.
"""
from __future__ import annotations

from typing import Any

from app.db.postgres import PostgresDB
from app.regulatory.models import Citation, RetrievedChunk, SourceChunk, SourceRecord


def _build_retrieved_chunks(
    rows: list[dict[str, Any]],
    source_map: dict[str, SourceRecord],
) -> list[RetrievedChunk]:
    """Convert database rows into RetrievedChunk objects with source info."""
    results: list[RetrievedChunk] = []
    for row in rows:
        chunk = SourceChunk(
            id=row.get("id"),
            source_id=row.get("source_id", ""),
            chunk_text=row.get("chunk_text", ""),
            chunk_index=row.get("chunk_index", 0),
            metadata=row.get("metadata", {}),
        )
        rank = float(row.get("rank", 0.0))
        source = source_map.get(chunk.source_id)
        results.append(RetrievedChunk(chunk=chunk, rank=rank, source=source))
    return results


def chunks_to_citations(retrieved: list[RetrievedChunk]) -> list[Citation]:
    """Convert retrieved chunks into citations, deduplicating by source_id.

    For each source, keeps the highest-ranked chunk as the citation excerpt.
    """
    best_by_source: dict[str, RetrievedChunk] = {}
    for r in retrieved:
        sid = r.chunk.source_id
        if sid not in best_by_source or r.rank > best_by_source[sid].rank:
            best_by_source[sid] = r

    citations: list[Citation] = []
    for r in sorted(best_by_source.values(), key=lambda x: x.rank, reverse=True):
        if r.source is None:
            continue
        citations.append(
            Citation(
                source_id=r.source.id,
                title=r.source.title,
                authority=r.source.authority,
                url=r.source.url,
                source_type=r.source.source_type,
                excerpt=r.chunk.chunk_text,
                relevance_rank=r.rank,
            )
        )
    return citations


def _ranked_search(
    db: PostgresDB, query: str, limit: int
) -> list[dict[str, Any]]:
    """Full-text search with ts_rank_cd relevance, highest first."""
    return db.fetch_all(
        "SELECT id, source_id, chunk_text, chunk_index, metadata, "
        "ts_rank_cd(tsv, plainto_tsquery('english', %s)) AS rank "
        "FROM source_chunks "
        "WHERE tsv @@ plainto_tsquery('english', %s) "
        "ORDER BY rank DESC LIMIT %s",
        (query, query, limit),
    )


def search_chunks(
    client: Any,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search source chunks using PostgreSQL full-text search.

    Args:
        client: PostgresDB database handle
        query: Search query string
        limit: Maximum results

    Returns:
        List of chunk rows with rank
    """
    if not query.strip():
        return []
    assert isinstance(client, PostgresDB), "search_chunks requires PostgresDB"
    return _ranked_search(client, query, limit)


def search_chunks_with_rank(
    client: Any,
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search source chunks with explicit rank scoring.

    Uses plainto_tsquery + ts_rank_cd directly (the previous Supabase
    RPC path has no local equivalent and is not needed).
    """
    if not query.strip():
        return []
    assert isinstance(client, PostgresDB), "search requires PostgresDB"
    return _ranked_search(client, query, limit)


def get_source_by_id(client: Any, source_id: str) -> dict[str, Any] | None:
    """Fetch a single source record by ID."""
    assert isinstance(client, PostgresDB)
    return client.fetch_one("SELECT * FROM sources WHERE id = %s", (source_id,))


def get_chunks_for_source(client: Any, source_id: str) -> list[dict[str, Any]]:
    """Fetch all chunks for a given source."""
    assert isinstance(client, PostgresDB)
    return client.fetch_all(
        "SELECT id, source_id, chunk_text, chunk_index, metadata "
        "FROM source_chunks WHERE source_id = %s ORDER BY chunk_index",
        (source_id,),
    )


def get_citations_for_source_ids(
    client: Any,
    source_ids: list[str],
) -> list[Citation]:
    """Retrieve citations for a list of source IDs."""
    if not source_ids:
        return []
    assert isinstance(client, PostgresDB)

    placeholders = ", ".join(["%s"] * len(source_ids))
    source_rows = client.fetch_all(
        f"SELECT * FROM sources WHERE id IN ({placeholders})",
        tuple(source_ids),
    )
    source_map = {s["id"]: SourceRecord(**s) for s in source_rows}

    citations: list[Citation] = []
    for sid in source_ids:
        source = source_map.get(sid)
        if source is None:
            continue
        # Get the primary chunk (index 0) for the excerpt
        chunks = get_chunks_for_source(client, sid)
        primary_chunk = next((c for c in chunks if c.get("chunk_index") == 0), None)
        excerpt = primary_chunk["chunk_text"] if primary_chunk else source.title
        citations.append(
            Citation(
                source_id=source.id,
                title=source.title,
                authority=source.authority,
                url=source.url,
                source_type=source.source_type,
                excerpt=excerpt,
                relevance_rank=1.0,
                jurisdiction=source.jurisdiction or None,
                checked_date=source.checked_date or None,
                trust_tier=source.trust_tier or None,
            )
        )
    return citations


def get_all_sources(
    client: Any,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Fetch all regulatory sources with pagination."""
    assert isinstance(client, PostgresDB)
    return client.fetch_all(
        "SELECT * FROM sources ORDER BY id LIMIT %s OFFSET %s", (limit, offset)
    )


# ─────────────────────────────────────────────────────────────
# T5: pack-backed deterministic retrieval (no DB, no embeddings).
#
# Maharashtra regulatory evidence lives in the in-memory
# RegulatoryPack (verified/stored SourceRecords). The DB tables only
# carry Gujarat rows. These helpers resolve rule/approval evidence
# strictly within one pack's jurisdiction: no cross-jurisdiction
# fallback, missing sources stay missing, and ranking is a simple
# deterministic token overlap (inspectable, no LLM/vector layer).
# ─────────────────────────────────────────────────────────────

def pack_source_to_citation(
    source: SourceRecord,
    excerpt: str | None = None,
    rank: float = 1.0,
    provision: str | None = None,
) -> Citation:
    """Build a Citation from a pack SourceRecord (additive metadata kept)."""
    return Citation(
        source_id=source.id,
        title=source.title,
        authority=source.authority,
        url=source.url,
        source_type=source.source_type,
        excerpt=excerpt if excerpt is not None else source.title,
        relevance_rank=float(rank),
        jurisdiction=source.jurisdiction,
        checked_date=source.checked_date or None,
        trust_tier=source.trust_tier or None,
        provision=provision,
    )


def get_pack_source_by_id(
    sources: list[SourceRecord],
    source_id: str,
) -> SourceRecord | None:
    """Exact source lookup within one pack. None when missing (no fallback)."""
    for s in sources:
        if s.id == source_id:
            return s
    return None


def get_pack_citations_for_source_ids(
    sources: list[SourceRecord],
    source_ids: list[str],
    provisions: dict[str, str] | None = None,
) -> list[Citation]:
    """Citations for source IDs strictly within the given pack sources.

    Unknown IDs are skipped (explicit missing, never substituted with
    another jurisdiction's source). Order follows source_ids.
    """
    by_id = {s.id: s for s in sources}
    out: list[Citation] = []
    for sid in source_ids:
        source = by_id.get(sid)
        if source is None:
            continue
        provision = (provisions or {}).get(sid)
        out.append(pack_source_to_citation(source, rank=1.0, provision=provision))
    return out


def get_rule_source_ids(
    approval_rules: list[Any],
    rule_id: str,
) -> list[str]:
    """Source IDs referenced by one rule (empty when the rule is unknown)."""
    for rule in approval_rules:
        if getattr(rule, "id", None) == rule_id:
            return [ref.source_id for ref in (rule.source_refs or []) if ref.source_id]
    return []


def get_approval_source_ids(
    approval_rules: list[Any],
    approval_id: str,
) -> list[str]:
    """Deduplicated source IDs for an approval (order-preserving)."""
    ids: list[str] = []
    for rule in approval_rules:
        if getattr(rule, "approval_id", None) == approval_id:
            for ref in rule.source_refs or []:
                if ref.source_id and ref.source_id not in ids:
                    ids.append(ref.source_id)
    return ids


def get_approval_provisions(
    approval_rules: list[Any],
    approval_id: str,
) -> dict[str, str]:
    """First-seen citation_span per source for an approval (provision display)."""
    out: dict[str, str] = {}
    for rule in approval_rules:
        if getattr(rule, "approval_id", None) == approval_id:
            for ref in rule.source_refs or []:
                if ref.source_id and ref.source_id not in out:
                    out[ref.source_id] = ref.citation_span
    return out


def get_approval_citations(
    sources: list[SourceRecord],
    approval_rules: list[Any],
    approval_id: str,
) -> list[Citation]:
    """Only sources actually associated with an approval (pack-scoped)."""
    ids = get_approval_source_ids(approval_rules, approval_id)
    provisions = get_approval_provisions(approval_rules, approval_id)
    return get_pack_citations_for_source_ids(sources, ids, provisions)


def _tokenize(text: str) -> set[str]:
    import re as _re

    return set(_re.findall(r"[a-z0-9]+", text.lower()))


def search_pack_sources(
    sources: list[SourceRecord],
    query: str,
    limit: int = 5,
) -> list[Citation]:
    """Deterministic ranked text search over pack sources (no DB).

    Score = token overlap between the query and
    (title + authority + source_type + notes). Ties break by source_id
    for determinism. Jurisdiction filtering is by construction: callers
    pass exactly one pack's sources, so GJ rows can never appear for an
    MH query and vice versa.
    """
    if not query.strip() or limit <= 0:
        return []
    qtokens = _tokenize(query)
    if not qtokens:
        return []
    scored: list[tuple[int, SourceRecord]] = []
    for s in sources:
        hay = f"{s.title} {s.authority} {s.source_type} {s.notes}"
        overlap = len(qtokens & _tokenize(hay))
        if overlap > 0:
            scored.append((overlap, s))
    scored.sort(key=lambda t: (-t[0], t[1].id))
    out: list[Citation] = []
    for overlap, s in scored[:limit]:
        # Deterministic rank in (0, 1]: overlap density, no ML.
        rank = overlap / max(len(qtokens), 1)
        out.append(pack_source_to_citation(s, excerpt=s.title, rank=rank))
    return out


def filter_rules_by_effective_date(
    approval_rules: list[Any],
    evaluation_date: Any | None,
) -> list[Any]:
    """Respect rule effective windows when an evaluation date is supplied.

    None evaluation_date preserves existing behavior (all rules).
    Rules outside [effective_from, effective_to] are excluded from
    evidence lookup (their sources must not cite for that date).
    """
    if evaluation_date is None:
        return list(approval_rules)
    try:
        from datetime import date as _date

        if isinstance(evaluation_date, str):
            evaluation_date = _date.fromisoformat(evaluation_date)
    except (ValueError, TypeError):
        return list(approval_rules)
    out: list[Any] = []
    for r in approval_rules:
        eff_from = getattr(r, "effective_from", None)
        eff_to = getattr(r, "effective_to", None)
        if eff_from is not None and evaluation_date < eff_from:
            continue
        if eff_to is not None and evaluation_date > eff_to:
            continue
        out.append(r)
    return out


def search_chunks_for_jurisdiction(
    client: Any,
    query: str,
    limit: int = 5,
    jurisdiction: str | None = None,
) -> list[dict[str, Any]]:
    """Jurisdiction-filtered full-text search over DB chunks (additive).

    None jurisdiction preserves the legacy unfiltered behavior (GJ path
    unchanged). When set, only chunks whose source carries that
    jurisdiction are returned (JOIN sources). No fallback across
    jurisdictions.
    """
    if not query.strip():
        return []
    assert isinstance(client, PostgresDB), "search requires PostgresDB"
    if jurisdiction is None:
        return _ranked_search(client, query, limit)
    return client.fetch_all(
        "SELECT sc.id, sc.source_id, sc.chunk_text, sc.chunk_index, "
        "sc.metadata, "
        "ts_rank_cd(sc.tsv, plainto_tsquery('english', %s)) AS rank "
        "FROM source_chunks sc JOIN sources s ON s.id = sc.source_id "
        "WHERE s.jurisdiction = %s "
        "AND sc.tsv @@ plainto_tsquery('english', %s) "
        "ORDER BY rank DESC LIMIT %s",
        (query, jurisdiction, query, limit),
    )
