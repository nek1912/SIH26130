Task 2: Implement Orchestration Service

**Files:**
- Create: `backend/app/orchestration/service.py`

**Interfaces:**
- Consumes: `evaluate_approval_applicability()` from `app.rules.applicability`, `evaluate_readiness()` from `app.rules.dependency_engine`, `load_approval_rules()`/`load_approval_authorities()` from `app.seed.approvals`, `load_approval_dependencies()` from `app.seed.dependencies`, document requirements from `app.seed.documents`, existing models from `app.orchestration.models`
- Produces: `orchestrate_application()` returning `ApprovalOrchestration`, `orchestrate_application_full()` returning `ApplicationOrchestration`

## Implementation

Create `backend/app/orchestration/service.py` with two functions:

### `orchestrate_application()`

Signature:
```python
def orchestrate_application(
    application_id: str,
    approval_id: str,
    project_facts: dict[str, Any],
    approval_rules: list[ApprovalRule],
    approval_authorities: dict[str, str],
    dependencies: list[ApprovalDependency],
    document_requirements: list[dict[str, Any]],
    uploaded_documents: list[dict[str, Any]],
    extraction_results: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
    consistency_result: Any | None,
    sla_info: Any | None,
    obtained_approvals: set[str],
) -> ApprovalOrchestration:
```

Logic:
1. Run applicability: `evaluate_approval_applicability(approval_rules, project_facts, approval_authorities, [approval_id])`
2. Get the evaluation result for this approval_id (use `summarize_by_approval`)
3. Run dependency readiness: `evaluate_readiness(dependencies, applicability_results_map, obtained=obtained_approvals)`
4. Get readiness for this approval from the dependency graph
5. Compute document readiness:
   - Filter document_requirements to those matching this approval_id (via "approval_ids" field in req dicts)
   - For each requirement, check if there's a matching uploaded document
   - Readiness is: "all_valid" if all mandatory docs have valid extraction+validation, "missing" if any mandatory doc not uploaded, "invalid" if any doc has INVALID validation, "review_required" if any REVIEW_REQUIRED, "no_requirements" if empty list
   - Each document gets a DocumentReadinessSummary with blocking=True for mandatory missing/invalid docs
6. Check consistency: if consistency_result has outcome "REVIEW_REQUIRED" → add a consistency_review blocker
7. Check SLA: if sla_info has state "breached" → add a sla_breached blocker
8. Determine OrchestrationStatus using priority:
   - NOT_APPLICABLE (applicability is "does_not_apply")
   - INSUFFICIENT_DATA (applicability is "insufficient_data" or "conditional")
   - BLOCKED_BY_DEPENDENCY (dependency readiness is BLOCKED)
   - BLOCKED_BY_DOCUMENTS (mandatory docs missing or invalid)
   - REVIEW_REQUIRED (consistency or doc review needed, but no hard blockers)
   - READY (all clear)
   - COMPLETE (application status is approved/refused/withdrawn/cancelled — but this function doesn't know status, so leave it to the caller)
9. Build blockers list with full traceability
10. Determine next_action: first missing mandatory doc → "upload_document", first invalid doc → "validate_document", etc.
11. Build explanation string

### `orchestrate_application_full()`

Signature:
```python
def orchestrate_application_full(
    application_id: str,
    project_facts: dict[str, Any],
    approval_rules: list[ApprovalRule],
    approval_authorities: dict[str, str],
    dependencies: list[ApprovalDependency],
    all_approval_ids: list[str],
    document_requirements: list[dict[str, Any]],
    uploaded_documents: list[dict[str, Any]],
    extraction_results: list[dict[str, Any]],
    validation_results: list[dict[str, Any]],
    consistency_result: Any | None,
    sla_info: Any | None,
    obtained_approvals: set[str],
) -> ApplicationOrchestration:
```

Logic:
1. For each approval_id in all_approval_ids, call `orchestrate_application()`
2. Compute overall_status = worst case across all approvals (priority: BLOCKED_BY_DEPENDENCY > BLOCKED_BY_DOCUMENTS > INSUFFICIENT_DATA > REVIEW_REQUIRED > READY > NOT_APPLICABLE)
3. Find the single highest-priority next_action across all approvals
4. Count total blockers
5. Return ApplicationOrchestration

## Priority order for worst-case status:
1. BLOCKED_BY_DEPENDENCY (highest)
2. BLOCKED_BY_DOCUMENTS
3. INSUFFICIENT_DATA
4. REVIEW_REQUIRED
5. READY
6. NOT_APPLICABLE (lowest)

## Key constraints:
- This is a PURE FUNCTION — no database calls, no side effects
- All data is passed in as parameters
- Deterministic — same inputs always produce same outputs
- No LLM calls
- Reuse existing engines, do not duplicate their logic
- Follow existing code style: `from __future__ import annotations`, type hints, Pydantic models
