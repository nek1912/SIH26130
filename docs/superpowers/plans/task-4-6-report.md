# Task 4-6 Report: Database Migration, Repository, and API Endpoints

**Date:** 2026-09-15  
**Status:** Complete

## What Was Implemented

### Task 4: Database Migration
- Created `supabase/migrations/004_consistency.sql`
  - `consistency_outcome` enum type (VALID, REVIEW_REQUIRED, INSUFFICIENT_DATA)
  - `consistency_results` table with application_id FK, outcome, checked_at, rule_version
  - `consistency_findings` table with result_id FK, rule_id, canonical_field, observed_values JSONB
  - Indexes on application_id and result_id

### Task 5: Consistency Repository
- Created `backend/app/repositories/consistency.py`
  - `ConsistencyRepository` extends `BaseRepository`
  - `create_result()` — insert consistency result row
  - `create_findings()` — bulk insert findings
  - `get_latest_result()` — most recent result by checked_at DESC
  - `list_findings_for_result()` — all findings for a result
  - `delete_findings_for_result()` — cascade delete findings
  - `delete_previous_results()` — clean re-run support
  - `get_extracted_fields_for_application()` — reads from extracted_fields table
  - `get_document_req_map()` — builds document_id → requirement_key mapping

### Task 6: API Endpoints
- Created `backend/app/api/consistency.py`
  - `POST /applications/{app_id}/consistency/check` — runs engine, persists results
  - `GET /applications/{app_id}/consistency` — returns latest result + findings
  - Auth: `require_any_permission` (VIEW_OWN, VIEW_TEAM, VIEW_ALL) + ownership check
- Updated `backend/app/main.py` — added consistency router

### Tests
- Created `backend/tests/test_consistency_api.py`
  - 5 repository tests (mocked Supabase client)
  - 2 API tests (FastAPI TestClient with mocked deps)

## Test Results

- **527 passed**, 4 skipped (pre-existing Supabase-dependent tests), 22 warnings (pre-existing JWT key warnings)
- **Lint:** All checks passed (ruff)

## Files Changed

| File | Action |
|------|--------|
| `supabase/migrations/004_consistency.sql` | Created |
| `backend/app/repositories/consistency.py` | Created |
| `backend/app/api/consistency.py` | Created |
| `backend/app/main.py` | Modified (added router import + include) |
| `backend/tests/test_consistency_api.py` | Created |

## Concerns

- The API tests mock the Supabase client with `side_effect` to return different mock chains per table name. This works but is fragile if table access patterns change.
- The `_get_application` helper in the API follows the same pattern as `extraction.py`'s `_get_app_withOwnership` — consistent but creates a new ApplicationsRepository on each call.
- The `delete_previous_results()` method does N+1 queries (one per existing result to delete findings). For MVP with typically one result per app, this is acceptable.
