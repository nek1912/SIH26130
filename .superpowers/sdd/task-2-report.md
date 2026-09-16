# Task 2 Report: Orchestration Service

## What I Implemented

Created `backend/app/orchestration/service.py` with two functions:

### `orchestrate_application()`
- Takes a single approval_id and all project data
- Runs applicability evaluation via `evaluate_approval_applicability()` + `summarize_by_approval()`
- Runs dependency readiness via `evaluate_readiness()`
- Computes document readiness by matching requirements to uploaded/extraction/validation data
- Checks consistency and SLA results for additional blockers
- Determines `OrchestrationStatus` using priority rules (NOT_APPLICABLE → INSUFFICIENT_DATA → BLOCKED_BY_DEPENDENCY → BLOCKED_BY_DOCUMENTS → REVIEW_REQUIRED → READY)
- Selects highest-priority next_action from blockers
- Builds human-readable explanation with full traceability

### `orchestrate_application_full()`
- Calls `orchestrate_application()` for each approval_id
- Aggregates overall status using worst-case priority across all approvals
- Finds highest-priority next_action across all approvals
- Returns `ApplicationOrchestration` with status distribution summary

## Key Design Decisions

1. **Pure function** — no database calls, no side effects, no LLM calls. All data passed as parameters.
2. **Reuses existing engines** — delegates to `evaluate_approval_applicability`, `summarize_by_approval`, `evaluate_readiness`, and `get_requirements_for_approval` without duplicating logic.
3. **Document readiness logic** — "mandatory" means requirement_level in `("required", "mandatory")`. Optional docs don't block.
4. **Status priority** — follows brief's priority order exactly.
5. **Consistency/SLA handling** — checks for `outcome == "REVIEW_REQUIRED"` and `state == "breached"` respectively, works with both Pydantic models and plain dicts.

## Files Changed

- Created: `backend/app/orchestration/service.py`

## Test Results

- **538 passed, 4 skipped, 0 failures** (existing test suite)
- Smoke test: orchestration works end-to-end for 18 approvals with chemical project facts
  - A01: blocked_by_documents (4 blockers from missing docs)
  - Overall: blocked_by_dependency (A03→A02→A04 chain)
  - 19 total blockers across 18 approvals

## Self-Review Findings

1. The `_compute_document_readiness` function uses `get_requirements_for_approval` from `app.seed.documents` — this matches the brief's intent to filter by approval_id.
2. `consistency_result` and `sla_info` accept `Any | None` and handle both Pydantic models and dicts gracefully via `getattr`/`.get()`.
3. The `_build_explanation` helper produces concise traceable explanations.
4. No circular imports — all imports are from existing modules.
