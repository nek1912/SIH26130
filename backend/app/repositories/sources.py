"""Sources repository — CRUD + full-text search for regulatory sources."""
from __future__ import annotations

from typing import Any

from app.repositories.base import BaseRepository


class SourcesRepository(BaseRepository):
    """Repository for regulatory sources and chunks."""

    def __init__(self, client):
        super().__init__(client, "sources")

    def get_by_jurisdiction(self, jurisdiction: str) -> list[dict[str, Any]]:
        """Get sources by jurisdiction."""
        return self.client.fetch_all(
            "SELECT * FROM sources WHERE jurisdiction = %s", (jurisdiction,)
        )

    def get_by_id_text(self, source_id: str) -> dict[str, Any] | None:
        """Get a source by its text ID (e.g. 'S01')."""
        return self.client.fetch_one(
            "SELECT * FROM sources WHERE id = %s", (source_id,)
        )

    def get_all_sources(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get all sources with pagination."""
        return self.client.fetch_all(
            "SELECT * FROM sources ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset),
        )

    def create_source(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a source record."""
        return self.client.insert_one(self.table_name, data)

    def create_sources_batch(self, records: list[dict[str, Any]]) -> int:
        """Create multiple source records. Returns count created."""
        if not records:
            return 0
        return len(self.client.insert_many(self.table_name, records))

    def search_chunks(
        self, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Search source_chunks using PostgreSQL full-text search."""
        if not query.strip():
            return []
        return self.client.fetch_all(
            "SELECT id, source_id, chunk_text, chunk_index, metadata, "
            "ts_rank_cd(tsv, plainto_tsquery('english', %s)) AS rank "
            "FROM source_chunks "
            "WHERE tsv @@ plainto_tsquery('english', %s) "
            "ORDER BY rank DESC LIMIT %s",
            (query, query, limit),
        )

    def get_chunks_for_source(self, source_id: str) -> list[dict[str, Any]]:
        """Get all chunks for a source."""
        return self.client.fetch_all(
            "SELECT id, source_id, chunk_text, chunk_index, metadata "
            "FROM source_chunks WHERE source_id = %s ORDER BY chunk_index",
            (source_id,),
        )

    def create_chunk(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a source chunk."""
        return self.client.insert_one("source_chunks", data)

    def create_chunks_batch(self, records: list[dict[str, Any]]) -> int:
        """Create multiple chunks. Returns count created."""
        if not records:
            return 0
        return len(self.client.insert_many("source_chunks", records))

    def count_sources(self) -> int:
        """Count total sources."""
        return self.client.count(self.table_name)

    def count_chunks(self) -> int:
        """Count total chunks."""
        return self.client.count("source_chunks")
