"""Tests for regulatory retrieval service."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.regulatory.models import RetrievedChunk, SourceChunk, SourceRecord
from app.regulatory.retrieval import (
    _build_retrieved_chunks,
    chunks_to_citations,
    get_all_sources,
    get_chunks_for_source,
    get_citations_for_source_ids,
    get_source_by_id,
    search_chunks,
)


class TestBuildRetrievedChunks:
    """Test _build_retrieved_chunks helper."""

    def test_empty_rows(self):
        """Empty rows returns empty list."""
        result = _build_retrieved_chunks([], {})
        assert result == []

    def test_single_row(self):
        """Single row creates RetrievedChunk."""
        rows = [{
            "id": "chunk-1",
            "source_id": "S01",
            "chunk_text": "Test chunk",
            "chunk_index": 0,
            "metadata": {},
        }]
        source_map = {
            "S01": SourceRecord(
                id="S01", title="Test", authority="Auth",
                source_type="portal", url="https://example.com",
            )
        }
        result = _build_retrieved_chunks(rows, source_map)
        assert len(result) == 1
        assert result[0].chunk.source_id == "S01"
        assert result[0].source is not None
        assert result[0].source.title == "Test"

    def test_missing_source(self):
        """Row with unknown source_id has None source."""
        rows = [{
            "id": "chunk-1",
            "source_id": "S99",
            "chunk_text": "Test",
            "chunk_index": 0,
            "metadata": {},
        }]
        result = _build_retrieved_chunks(rows, {})
        assert len(result) == 1
        assert result[0].source is None


class TestChunksToCitations:
    """Test chunks_to_citations deduplication."""

    def test_empty_chunks(self):
        """Empty list returns empty citations."""
        result = chunks_to_citations([])
        assert result == []

    def test_deduplicates_by_source(self):
        """Multiple chunks from same source produce one citation."""
        source = SourceRecord(
            id="S01", title="Test", authority="Auth",
            source_type="portal", url="https://example.com",
        )
        retrieved = [
            RetrievedChunk(
                chunk=SourceChunk(source_id="S01", chunk_text="chunk 1"),
                rank=0.8,
                source=source,
            ),
            RetrievedChunk(
                chunk=SourceChunk(source_id="S01", chunk_text="chunk 2"),
                rank=0.6,
                source=source,
            ),
        ]
        result = chunks_to_citations(retrieved)
        assert len(result) == 1
        # Best chunk (rank 0.8) is used
        assert result[0].excerpt == "chunk 1"

    def test_different_sources(self):
        """Chunks from different sources produce separate citations."""
        sources = {
            "S01": SourceRecord(
                id="S01", title="Source 1", authority="Auth1",
                source_type="portal", url="https://example1.com",
            ),
            "S02": SourceRecord(
                id="S02", title="Source 2", authority="Auth2",
                source_type="portal", url="https://example2.com",
            ),
        }
        retrieved = [
            RetrievedChunk(
                chunk=SourceChunk(source_id="S01", chunk_text="chunk 1"),
                rank=0.9,
                source=sources["S01"],
            ),
            RetrievedChunk(
                chunk=SourceChunk(source_id="S02", chunk_text="chunk 2"),
                rank=0.7,
                source=sources["S02"],
            ),
        ]
        result = chunks_to_citations(retrieved)
        assert len(result) == 2

    def test_sorted_by_rank(self):
        """Citations are sorted by rank descending."""
        source = SourceRecord(
            id="S01", title="Test", authority="Auth",
            source_type="portal", url="https://example.com",
        )
        retrieved = [
            RetrievedChunk(
                chunk=SourceChunk(source_id="S01", chunk_text="low"),
                rank=0.3,
                source=source,
            ),
            RetrievedChunk(
                chunk=SourceChunk(source_id="S02", chunk_text="high"),
                rank=0.9,
                source=SourceRecord(
                    id="S02", title="High", authority="Auth",
                    source_type="portal", url="https://example.com",
                ),
            ),
        ]
        result = chunks_to_citations(retrieved)
        assert result[0].relevance_rank >= result[1].relevance_rank


class TestSearchChunks:
    """Test search_chunks with mocked PostgresDB."""

    def _db(self, rows):
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = rows
        return db

    def test_empty_query(self):
        """Empty query returns empty list."""
        result = search_chunks(self._db([]), "")
        assert result == []

    def test_whitespace_query(self):
        """Whitespace-only query returns empty list."""
        result = search_chunks(self._db([]), "   ")
        assert result == []

    def test_ranked_search(self):
        """Search uses PostgreSQL full-text search with ranking."""
        db = self._db([{"id": "1", "chunk_text": "test", "rank": 0.5}])

        result = search_chunks(db, "fire safety")
        assert len(result) == 1
        sql = db.fetch_all.call_args[0][0]
        assert "ts_rank_cd" in sql
        assert "plainto_tsquery" in sql

    def test_ranked_search_with_rank_fn(self):
        """search_chunks_with_rank returns ranked rows."""
        from app.db.postgres import PostgresDB
        from app.regulatory.retrieval import search_chunks_with_rank

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = [{"id": "1", "rank": 0.9}]
        result = search_chunks_with_rank(db, "fire")
        assert len(result) == 1


class TestGetSourceById:
    """Test get_source_by_id with mocked handle."""

    def test_existing_source(self):
        """Returns source dict for existing ID."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_one.return_value = {"id": "S01", "title": "Test"}
        result = get_source_by_id(db, "S01")
        assert result["id"] == "S01"

    def test_nonexistent_source(self):
        """Returns None for nonexistent ID."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_one.return_value = None
        result = get_source_by_id(db, "S99")
        assert result is None


class TestGetChunksForSource:
    """Test get_chunks_for_source with mocked handle."""

    def test_returns_chunks(self):
        """Returns chunks for a source."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = [
            {"chunk_text": "chunk 1", "chunk_index": 0},
            {"chunk_text": "chunk 2", "chunk_index": 1},
        ]
        result = get_chunks_for_source(db, "S01")
        assert len(result) == 2

    def test_empty_chunks(self):
        """Returns empty list for source with no chunks."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = []
        result = get_chunks_for_source(db, "S99")
        assert result == []


class TestGetCitationsForSourceIds:
    """Test get_citations_for_source_ids."""

    def test_empty_ids(self):
        """Empty IDs returns empty citations."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        result = get_citations_for_source_ids(db, [])
        assert result == []

    def test_builds_citations(self):
        """Builds citations from source IDs."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.side_effect = [
            [{"id": "S01", "title": "Source 1", "authority": "Auth1",
              "source_type": "portal", "url": "https://example.com",
              "jurisdiction": "IN-GJ", "source_class": "Official",
              "notes": "", "checked_date": "2026-09-15", "trust_tier": "govt-portal",
              "content_hash": "hash1"}],
            [{"chunk_text": "Primary chunk text", "chunk_index": 0}],
        ]

        result = get_citations_for_source_ids(db, ["S01"])
        assert len(result) == 1
        assert result[0].source_id == "S01"
        assert result[0].title == "Source 1"


class TestGetAllSources:
    """Test get_all_sources."""

    def test_returns_list(self):
        """Returns a list of sources."""
        from app.db.postgres import PostgresDB

        db = MagicMock(spec=PostgresDB)
        db.fetch_all.return_value = [{"id": "S01"}, {"id": "S02"}]
        result = get_all_sources(db)
        assert len(result) == 2
