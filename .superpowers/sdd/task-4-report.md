# Task 4: Create Orchestration API Endpoint — Report

## Status: DONE

## Summary
Created `GET /applications/{id}/orchestration` endpoint that loads application data from the database and calls the orchestration service to return per-approval readiness status.

## Files Created/Modified
- **Created:** `backend/app/api/orchestration.py` — Orchestration endpoint
- **Modified:** `backend/app/main.py` — Registered orchestration router
- **Created:** `backend/tests/test_orchestration_api.py` — 3 API tests

## Implementation Details
- Follows the SLA endpoint pattern from `applications.py:163-216`
- Uses `require_any_permission` with VIEW_OWN, VIEW_TEAM, VIEW_ALL
- Uses `check_application_ownership` for authorization
- Loads project facts from `ProjectFactsRepository`
- Loads uploaded documents from `DocumentsRepository.list_documents_for_application()`
- Loads seed data (approval rules, authorities, dependencies, document requirements)
- Calls `orchestrate_application_full()` with all required parameters
- Returns `result.model_dump()` for the response

## Test Results
- 3/3 orchestration API tests passed
- 558/558 total tests passed (4 skipped)
- Ruff: All checks passed for new files

## Deviation from Brief
The brief referenced `docs_repo.list_for_application()` but the actual method is `list_documents_for_application()`. Used the correct method name from the DocumentsRepository.

## Commit
- `eaaa85f` — `feat(orchestration): add GET /applications/{id}/orchestration endpoint`

## Concerns
None. The endpoint follows established patterns and integrates cleanly with existing infrastructure.
