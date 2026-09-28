# Phase 7 — Official-Source RAG & Regulatory Explanation

## Current State
- 558 backend tests passing, 4 skipped, ruff clean
- Frontend TypeScript clean, Vite build successful
- 32 verified Gujarat regulatory sources in workbook (S01-S32), all "Official"
- `sources` table exists in schema (no data, no vector columns)
- `instruments` table exists in schema (no data)
- `SourcesRepository` exists (minimal CRUD only)
- `SourcesRepository` wired in `deps.py` but unused by any endpoint
- No pgvector, no embedding infrastructure, no LLM integration anywhere
- No `regulatory/` module exists

## Approach
- **No pgvector, no embeddings, no external LLM** (none authorized yet)
- Use **PostgreSQL `tsvector` + GIN indexes** for full-text search (native, zero dependencies)
- Seed all 32 sources from the workbook into the database
- Build a deterministic citation + explanation layer (template-based, no LLM)
- Source-grounded answers always cite the retrieved official source(s)
- RAG never overrides or calculates applicability — it only explains existing deterministic results

## Architecture

```
Deterministic rules decide → RAG retrieves → Templates explain → Human decides
```

RAG flow:
1. Ingest: Parse workbook sources → create source records + text chunks
2. Index: `tsvector` column on chunks, GIN index for fast search
3. Retrieve: `plainto_tsquery` + `ts_rank_cd` for relevance ranking
4. Cite: Every result carries source_id, title, authority, URL, chunk text, rank
5. Explain: Template-based explanation engine (no LLM) using retrieved evidence

## Deliverables

### 1. Database Migration (005_rag_sources.sql)
- Alter `sources` table: add `title`, `authority`, `source_type`, `source_class`, `notes` columns
- Create `source_chunks` table: id, source_id, chunk_text, chunk_index, metadata, tsv (tsvector)
- GIN index on `source_chunks.tsv` for full-text search
- `sources` table GIN index on title/domain for fast lookup

### 2. Seed Data (seed/sources.py)
- Extract all 32 sources (S01-S32) from workbook as `SourceRecord` objects
- Map workbook fields: source_id, source_title, authority, type, url, checked, source_class, notes
- Pre-built chunks per source (authority + title + notes as searchable content)

### 3. Backend Models (regulatory/models.py)
- `SourceRecord` — full source metadata
- `SourceChunk` — text chunk with source linkage
- `RetrievedChunk` — chunk with search rank
- `Citation` — source_id, title, authority, url, chunk_text, rank
- `RegulatoryExplanation` — answer + citations + evidence_state
- `ExplanationRequest` — query text, optional approval_id, optional application_id

### 4. Ingestion Service (regulatory/ingestion.py)
- `ingest_sources()` — seed all 32 sources to database
- `chunk_source()` — split source content into searchable chunks
- `build_tsvector()` — generate tsvector text from source metadata

### 5. Retrieval Service (regulatory/retrieval.py)
- `search_chunks(query, limit)` — full-text search with ts_rank_cd
- `get_source_by_id(source_id)` — fetch source record
- `get_chunks_for_source(source_id)` — all chunks for a source
- `get_citations_for_approval(approval_id)` — retrieve all cited sources for an approval rule

### 6. Explanation Service (regulatory/explanation.py)
- `explain_approval(approval_id)` — deterministic explanation from rule + sources
- `explain_rule(rule_id)` — explain a specific rule with source evidence
- `answer_query(query)` — RAG-based query answering with citations
- `explain_orchestration_result(approval_id, orchestration)` — enrich existing explanation with citations
- All explanations include `evidence_state`: `sufficient`, `insufficient`, `partial`
- When sources don't contain enough evidence → explicit `INSUFFICIENT_EVIDENCE` state

### 7. Repository Enhancement (repositories/sources.py)
- `get_source_by_id(source_id)` — single source
- `search_chunks(query, limit)` — full-text search
- `get_chunks_for_source(source_id)` — chunks by source
- `create_source(data)` / `create_chunk(data)` — for ingestion

### 8. API Endpoints (api/regulatory.py)
- `GET /sources` — list all regulatory sources
- `GET /sources/{id}` — get source details + chunks
- `POST /regulatory/explain` — RAG query answering
- `GET /regulatory/approval/{id}/explanation` — explanation for a specific approval
- `GET /regulatory/orchestration/{application_id}/citations` — enrich orchestration with source citations
- All endpoints auth-protected (VIEW_OWN/VIEW_TEAM/VIEW_ALL)

### 9. Frontend
- `types/api.ts` — add Source, SourceChunk, Citation, RegulatoryExplanation types
- `lib/api.ts` — add `regulatory` API section
- `pages/applicant/ApplicationDetailPage.tsx` — add RegulatoryAssistant panel
- `pages/staff/ApplicationDetailPage.tsx` — add RegulatoryAssistant panel (staff view)
- Minimal panel: explanation query, displayed citations with source links

### 10. Tests
- Ingestion: source creation, chunking, tsvector generation
- Retrieval: full-text search, ranking, empty results
- Explanation: approval explanation, query answering, insufficient evidence
- Citation: source metadata preserved, citations correct
- RAG boundary: cannot alter applicability, cannot override rules
- API: endpoint validation, auth, ownership
- All 558+ existing tests continue passing

## Files to Create/Modify

### New files
- `supabase/migrations/005_rag_sources.sql`
- `backend/app/regulatory/__init__.py`
- `backend/app/regulatory/models.py`
- `backend/app/regulatory/ingestion.py`
- `backend/app/regulatory/retrieval.py`
- `backend/app/regulatory/explanation.py`
- `backend/app/api/regulatory.py`
- `backend/app/seed/sources.py`
- `backend/tests/test_regulatory_ingestion.py`
- `backend/tests/test_regulatory_retrieval.py`
- `backend/tests/test_regulatory_explanation.py`
- `backend/tests/test_regulatory_api.py`
- `frontend/src/pages/shared/RegulatoryAssistant.tsx`

### Modified files
- `backend/app/repositories/sources.py` — add search/chunk methods
- `backend/app/api/deps.py` — add regulatory service dependencies
- `backend/app/main.py` — register regulatory router
- `frontend/src/types/api.ts` — add RAG types
- `frontend/src/lib/api.ts` — add regulatory API methods
- `frontend/src/pages/applicant/ApplicationDetailPage.tsx` — add panel
- `frontend/src/pages/staff/ApplicationDetailPage.tsx` — add panel
- `ARCHITECTURE.md` — update Phase 7 status
- `PRD.md` — update Phase 7 status
- `RULES.md` — update backend structure
- `AGENTS.md` — update status

## Verification
1. `cd backend && python -m pytest tests/ -v` — all pass
2. `cd backend && python -m ruff check app/ tests/` — clean
3. `cd frontend && npx tsc --noEmit` — clean
4. `cd frontend && npx vite build` — success
5. Manual: source seeding, search, explanation endpoints
