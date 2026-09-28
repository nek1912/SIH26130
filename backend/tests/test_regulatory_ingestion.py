"""Tests for regulatory seed data and ingestion."""
from __future__ import annotations

from app.regulatory.ingestion import (
    build_all_chunks,
    build_source_chunks,
    get_seed_chunks,
    get_seed_source_dicts,
    get_seed_sources,
)
from app.regulatory.models import SourceRecord
from app.seed.sources import load_regulatory_sources, source_to_chunks, source_to_dict


class TestSourceModels:
    """Test SourceRecord model creation."""

    def test_source_record_creation(self):
        """SourceRecord can be created with required fields."""
        source = SourceRecord(
            id="S01",
            title="Test Source",
            authority="Test Authority",
            source_type="portal",
            url="https://example.com",
        )
        assert source.id == "S01"
        assert source.jurisdiction == "IN-GJ"
        assert source.source_class == "Official"

    def test_source_record_defaults(self):
        """SourceRecord has sensible defaults."""
        source = SourceRecord(
            id="S99",
            title="Test",
            authority="Auth",
            source_type="type",
            url="https://example.com",
        )
        assert source.trust_tier == "govt-portal"
        assert source.notes == ""


class TestSeedSources:
    """Test the seed data loader."""

    def test_load_all_sources(self):
        """Load all verified Gujarat regulatory sources."""
        sources = load_regulatory_sources()
        assert len(sources) == 32

    def test_source_ids_unique(self):
        """All source IDs are unique."""
        sources = load_regulatory_sources()
        ids = [s.id for s in sources]
        assert len(ids) == len(set(ids))

    def test_source_ids_sequential(self):
        """Source IDs follow S01-S33 pattern (S32 removed as duplicate)."""
        sources = load_regulatory_sources()
        ids = sorted(s.id for s in sources)
        assert ids[0] == "S01"
        assert ids[-1] == "S33"

    def test_all_sources_official(self):
        """All sources are classified as Official."""
        sources = load_regulatory_sources()
        for s in sources:
            assert s.source_class == "Official"

    def test_all_sources_gujarat_jurisdiction(self):
        """All sources have Gujarat jurisdiction."""
        sources = load_regulatory_sources()
        for s in sources:
            assert s.jurisdiction == "IN-GJ"

    def test_all_sources_have_urls(self):
        """All sources have valid URLs."""
        sources = load_regulatory_sources()
        for s in sources:
            assert s.url.startswith("https://")

    def test_all_sources_have_authority(self):
        """All sources have an authority."""
        sources = load_regulatory_sources()
        for s in sources:
            assert s.authority
            assert len(s.authority) > 3

    def test_all_sources_have_title(self):
        """All sources have a title."""
        sources = load_regulatory_sources()
        for s in sources:
            assert s.title
            assert len(s.title) > 3

    def test_known_source_ids(self):
        """Key source IDs used by approval rules exist."""
        sources = load_regulatory_sources()
        ids = {s.id for s in sources}
        # These are referenced by seed/approvals.py
        for key_id in ["S01", "S03", "S04", "S05", "S07", "S09", "S11", "S12",
                        "S14", "S16", "S17", "S18", "S19", "S30", "S31"]:
            assert key_id in ids, f"Key source {key_id} missing"


class TestSourceConversion:
    """Test source-to-dict and chunk generation."""

    def test_source_to_dict(self):
        """SourceRecord converts to database dict."""
        source = load_regulatory_sources()[0]
        d = source_to_dict(source)
        assert d["id"] == source.id
        assert d["title"] == source.title
        assert d["authority"] == source.authority
        assert d["url"] == source.url
        assert d["trust_tier"] == "govt-portal"

    def test_source_to_chunks(self):
        """Source generates at least 2 chunks."""
        source = load_regulatory_sources()[0]
        chunks = source_to_chunks(source)
        assert len(chunks) >= 2
        # First chunk is identity
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["source_id"] == source.id
        assert source.title in chunks[0]["chunk_text"]

    def test_chunks_have_metadata(self):
        """Chunks include metadata."""
        source = load_regulatory_sources()[0]
        chunks = source_to_chunks(source)
        for chunk in chunks:
            assert "role" in chunk["metadata"]

    def test_notes_chunk_created(self):
        """Sources with notes get a notes chunk."""
        source = load_regulatory_sources()[0]
        chunks = source_to_chunks(source)
        # S01 has notes, so should have at least 2 chunks
        assert len(chunks) >= 2

    def test_all_sources_have_chunks(self):
        """Every source generates at least 2 chunks."""
        sources = load_regulatory_sources()
        for source in sources:
            chunks = source_to_chunks(source)
            assert len(chunks) >= 2, f"{source.id} has {len(chunks)} chunks"


class TestIngestion:
    """Test the ingestion service."""

    def test_get_seed_sources(self):
        """get_seed_sources returns 32 sources."""
        sources = get_seed_sources()
        assert len(sources) == 32

    def test_get_seed_source_dicts(self):
        """get_seed_source_dicts returns 32 dicts."""
        dicts = get_seed_source_dicts()
        assert len(dicts) == 32
        assert all(isinstance(d, dict) for d in dicts)

    def test_get_seed_chunks(self):
        """get_seed_chunks returns chunks for all sources."""
        chunks = get_seed_chunks()
        # 32 sources, each with 2-3 chunks
        assert len(chunks) >= 66  # at least 2 per source
        assert all(isinstance(c, dict) for c in chunks)

    def test_seed_chunks_reference_valid_sources(self):
        """All chunks reference source IDs that exist in the seed data."""
        sources = get_seed_sources()
        source_ids = {s.id for s in sources}
        chunks = get_seed_chunks()
        for chunk in chunks:
            assert chunk["source_id"] in source_ids

    def test_build_all_chunks(self):
        """build_all_chunks processes all sources."""
        sources = get_seed_sources()
        chunks = build_all_chunks(sources)
        assert len(chunks) >= 66

    def test_build_source_chunks(self):
        """build_source_chunks works for a single source."""
        source = get_seed_sources()[0]
        chunks = build_source_chunks(source)
        assert len(chunks) >= 2
