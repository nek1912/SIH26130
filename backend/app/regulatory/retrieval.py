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
