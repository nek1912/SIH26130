# Task 4: Persist workflow events on transitions

## What I implemented

1. **Modified `backend/app/workflow/engine.py`**: Added optional `events_repository` parameter to `execute_transition()`. When provided, the workflow event is persisted to the database via `events_repository.create()` with fields matching the DB schema (`application_id`, `from_stage`, `to_stage`, `action`, `performed_by_id`, `metadata`, `created_at`).

2. **Modified `backend/app/api/workflow.py`**: Injected `WorkflowEventsRepository` into all 7 transition endpoints (submit, advance, request_info, respond, approve, refuse, withdraw) via FastAPI dependency injection. Each endpoint now passes `events_repository=events_repo` to `execute_transition()`.

3. **Created `backend/tests/test_workflow_events_persistence.py`**: 3 tests covering event persistence behavior:
   - Event is persisted when `events_repository` is provided
   - No DB call when `events_repository` is not provided (backward compatible)
   - Persisted event includes all required fields with correct DB column names

## What I tested and test results

- **New tests**: 3/3 passed (`test_workflow_events_persistence.py`)
- **Existing workflow engine tests**: 68/68 passed (no regressions)
- **Full backend test suite**: 533 passed, 4 skipped, 0 failed
- **Lint**: All ruff checks passed

## Files changed

- `backend/app/workflow/engine.py` — Added `events_repository` parameter + persistence logic
- `backend/app/api/workflow.py` — Injected repository into all 7 transition endpoints
- `backend/tests/test_workflow_events_persistence.py` — New test file (3 tests)

## Design decisions

- Used DB column names (`from_stage`, `to_stage`, `performed_by_id`) not the task brief's `from_status`/`to_status`/`performed_by`
- Made `events_repository` optional (default `None`) for backward compatibility — existing callers don't break
- Persistence happens inside the engine after event creation but before returning, keeping it atomic with the in-memory event
- Used `Any | None` type hint for the repository parameter to avoid import coupling (repository interface is duck-typed)

## Commit

`1c263a9` — feat: persist workflow events on transitions via optional repository parameter
