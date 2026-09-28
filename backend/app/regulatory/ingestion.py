"""Regulatory ingestion service — seed sources and build search index.

This module handles the one-time ingestion of verified Gujarat regulatory
sources into the database. It creates source records and searchable text
chunks without any LLM or embedding dependencies.
"""
from __future__ import annotations

from typing import Any

from app.regulatory.models import SourceRecord
from app.seed.sources import load_regulatory_sources, source_to_chunks, source_to_dict


def build_source_chunks(source: SourceRecord) -> list[dict[str, Any]]:
    """Build chunk records for a single source."""
    return source_to_chunks(source)


def build_all_chunks(sources: list[SourceRecord]) -> list[dict[str, Any]]:
    """Build chunk records for all sources."""
    all_chunks: list[dict[str, Any]] = []
    for source in sources:
        all_chunks.extend(build_source_chunks(source))
    return all_chunks


def get_seed_sources() -> list[SourceRecord]:
    """Return the 32 verified Gujarat regulatory sources."""
    return load_regulatory_sources()


def get_seed_source_dicts() -> list[dict[str, Any]]:
    """Return sources as database-ready dicts."""
    return [source_to_dict(s) for s in load_regulatory_sources()]


def get_seed_chunks() -> list[dict[str, Any]]:
    """Return all chunks as database-ready dicts."""
    return build_all_chunks(load_regulatory_sources())
