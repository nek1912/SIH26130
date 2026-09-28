-- ═══════════════════════════════════════════════════════════════
-- SIH 26130 — Phase 7: Official-Source RAG
-- Adds source metadata, text chunks, and full-text search
-- for regulatory explanation with source citations.
-- ═══════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- Extend SOURCES table with metadata columns from workbook
-- ─────────────────────────────────────────────────────────────

alter table sources
  add column if not exists title       text not null default '',
  add column if not exists authority   text not null default '',
  add column if not exists source_type text not null default '',
  add column if not exists source_class text not null default 'Official',
  add column if not exists notes       text not null default '',
  add column if not exists checked_date text not null default '';

-- ─────────────────────────────────────────────────────────────
-- SOURCE CHUNKS — searchable text segments from sources.
-- Each chunk is a piece of source content (title + authority
-- notes + description) indexed for full-text search.
-- ─────────────────────────────────────────────────────────────

create table if not exists source_chunks (
  id            uuid primary key default gen_random_uuid(),
  source_id     text not null references sources(id) on delete cascade,
  chunk_text    text not null,
  chunk_index   integer not null default 0,
  metadata      jsonb not null default '{}',
  tsv           tsvector generated always as (
    setweight(to_tsvector('english', coalesce(chunk_text, '')), 'A')
  ) stored,
  created_at    timestamptz not null default now()
);

create index idx_source_chunks_source on source_chunks(source_id);
create index idx_source_chunks_tsv on source_chunks using gin(tsv);

-- ─────────────────────────────────────────────────────────────
-- GIN index on sources for fast text search on title/authority
-- ─────────────────────────────────────────────────────────────

create index if not exists idx_sources_title on sources using gin(to_tsvector('english', title));
create index if not exists idx_sources_authority on sources using gin(to_tsvector('english', authority));
