# Phase 6 — Orchestration / Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core end-to-end approval orchestration layer combining applicability + dependency + documents + extraction + validation + consistency + SLA into a single per-approval readiness assessment with explainable blockers and next action.

**Architecture:** A deterministic orchestration service combines outputs from existing engines into per-approval readiness. A new API endpoint exposes this, and a concise frontend "Readiness / Next Action" card shows blockers, required actions, and affected approvals.

**Tech Stack:** FastAPI + Python, React + TypeScript + Vite + Tailwind CSS, existing engines (applicability, dependency, workflow, documents, extraction, consistency, SLA).

## Global Constraints

- Never allow AI to determine an approval outcome. Human/statutory authority decides.
- Dependency edges from verified seeded data only. Document requirements from existing seed.
- Consistency findings are warnings, not automatic rejection. SLA uses existing engine.
- No new external dependencies. All existing tests must continue to pass.

## Baseline

- Backend: 538 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean, vite build success

## File Structure

### New files
- `backend/app/orchestration/__init__.py`
- `backend/app/orchestration/models.py`
- `backend/app/orchestration/service.py`
- `backend/app/api/orchestration.py`
- `backend/tests/test_orchestration_service.py`
- `backend/tests/test_orchestration_api.py`

### Modified files
- `backend/app/main.py` — add orchestration router
- `frontend/src/types/api.ts` — add orchestration types
- `frontend/src/lib/api.ts` — add `api.orchestration.get()`
- `frontend/src/pages/staff/ApplicationDetailPage.tsx` — add ReadinessCard
- `frontend/src/pages/applicant/ApplicationDetailPage.tsx` — add ReadinessCard

---

### Task 1: Create Orchestration Data Models

**Files:**
- Create: `backend/app/orchestration/__init__.py`
- Create: `backend/app/orchestration/models.py`

**Interfaces:**
- Produces: `OrchestrationStatus`, `BlockerType`, `BlockerDetail`, `DocumentReadinessSummary`, `ApprovalOrchestration`, `NextAction`, `ApplicationOrchestration`

- [ ] **Step 1: Create module init**

```python
"""Approval orchestration — combines all engines into readiness assessments."""
```

- [ ] **Step 2: Create orchestration models with OrchestrationStatus enum, BlockerDetail, ApprovalOrchestration, NextAction, ApplicationOrchestration**

OrchestrationStatus values: READY, BLOCKED_BY_DEPENDENCY, BLOCKED_BY_DOCUMENTS, REVIEW_REQUIRED, INSUFFICIENT_DATA, COMPLETE, NOT_APPLICABLE.

BlockerType values: dependency, document_missing, document_invalid, document_review_required, extraction_failed, consistency_review, insufficient_data, sla_breached.

ApprovalOrchestration includes: approval_id, status, applicability_result, dependency_readiness, document_readiness, consistency_outcome, sla_state, blockers list, documents list, explanation, next_action.

ApplicationOrchestration includes: application_id, overall_status, approvals dict, total_blockers, next_action, stage_number, explanation.

- [ ] **Step 3: Verify imports**

Run: `cd backend && python -c "from app.orchestration.models import OrchestrationStatus, ApplicationOrchestration; print('OK')"`

- [ ] **Step 4: Commit**

---

### Task 2: Implement Orchestration Service

**Files:**
- Create: `backend/app/orchestration/service.py`

**Interfaces:**
- Consumes: `evaluate_approval_applicability()`, `evaluate_readiness()`, seed data (approval rules, dependencies, authorities, document requirements)
- Produces: `orchestrate_application()` returning `ApprovalOrchestration`, `orchestrate_application_full()` returning `ApplicationOrchestration`

- [ ] **Step 1: Implement `orchestrate_application()`**

The function takes: application_id, approval_id, project_facts, approval_rules, approval_authorities, dependencies, document_requirements, uploaded_documents, extraction_results, validation_results, consistency_result, sla_info, obtained_approvals.

Logic:
1. Evaluate applicability via existing `evaluate_approval_applicability()`
2. Evaluate dependency readiness via existing `evaluate_readiness()`
3. Compute document readiness (check each requirement: pending=missing, valid=ok, invalid=blocker, review_required=review signal)
4. Check consistency outcome (REVIEW_REQUIRED is a warning, not blocker)
5. Check SLA state (breached = signal)
6. Combine into OrchestrationStatus using priority: NOT_APPLICABLE > INSUFFICIENT_DATA > BLOCKED_BY_DEPENDENCY > BLOCKED_BY_DOCUMENTS > REVIEW_REQUIRED > READY
7. Build blockers list with full traceability
8. Determine next action

- [ ] **Step 2: Implement `orchestrate_application_full()`**

Evaluates ALL approvals for a given application, producing ApplicationOrchestration with per-approval results, overall status (worst-case), and the single highest-priority next action.

- [ ] **Step 3: Commit**

---

### Task 3: Write Orchestration Service Tests

**Files:**
- Create: `backend/tests/test_orchestration_service.py`

- [ ] **Step 1: Write tests for all orchestration states**

Test cases:
1. READY when applies + no deps + all docs valid
2. BLOCKED_BY_DEPENDENCY when prerequisite not obtained
3. INSUFFICIENT_DATA when project facts missing
4. BLOCKED_BY_DOCUMENTS when mandatory docs not uploaded
5. REVIEW_REQUIRED when consistency has findings
6. NOT_APPLICABLE when applicability says does_not_apply
7. COMPLETE when workflow status is approved
8. SLA_BREACHED signal when SLA state is breached
9. Document readiness summary correctness
10. Next action computation (upload_document before extract before submit)
11. Multi-approval orchestration with mixed states
12. Dependency chain (A04→A02→A03) produces correct stages
13. Empty inputs handled gracefully

- [ ] **Step 2: Run tests**

Run: `cd backend && python -m pytest tests/test_orchestration_service.py -v`

- [ ] **Step 3: Commit**

---

### Task 4: Create Orchestration API Endpoint

**Files:**
- Create: `backend/app/api/orchestration.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Implement `GET /applications/{id}/orchestration` endpoint**

The endpoint:
1. Loads application from DB (via existing application repository)
2. Loads project facts (via existing project_facts repository)
3. Calls `orchestrate_application_full()` with all inputs
4. Returns `ApplicationOrchestration` response

Auth: requires `application:view_own` OR `view_team` OR `view_all` permission.
Ownership: applicant must own the project; staff bypasses.

- [ ] **Step 2: Register router in main.py**

Add `from app.api import orchestration` to imports and `app.include_router(orchestration.router, tags=["orchestration"])`.

- [ ] **Step 3: Write API tests**

Tests:
1. Endpoint returns 200 with valid application ID
2. Endpoint returns 401 without auth token
3. Endpoint returns 403 for unauthorized applicant
4. Response shape matches ApplicationOrchestration schema
5. Orchestration includes per-approval results

- [ ] **Step 4: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`

- [ ] **Step 5: Run ruff**

Run: `cd backend && python -m ruff check app/ tests/`

- [ ] **Step 6: Commit**

---

### Task 5: Add Frontend Orchestration Types and API

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add TypeScript types**

Add to `api.ts`:
```typescript
export type OrchestrationStatus =
  | 'READY'
  | 'BLOCKED_BY_DEPENDENCY'
  | 'BLOCKED_BY_DOCUMENTS'
  | 'REVIEW_REQUIRED'
  | 'INSUFFICIENT_DATA'
  | 'COMPLETE'
  | 'NOT_APPLICABLE'

export interface BlockerDetail {
  blocker_type: string
  description: string
  affected_approval_id: string | null
  affected_document_key: string | null
  source_ref: string
  evidence: string
  action_required: string
}

export interface DocumentReadinessSummary {
  requirement_key: string
  document_name: string
  readiness: string
  extraction_status: string | null
  validation_outcome: string | null
  blocking: boolean
  reason: string
}

export interface ApprovalOrchestration {
  approval_id: string
  status: OrchestrationStatus
  applicability_result: string
  dependency_readiness: string
  document_readiness: string
  consistency_outcome: string | null
  sla_state: string | null
  blockers: BlockerDetail[]
  documents: DocumentReadinessSummary[]
  explanation: string
  next_action: string
}

export interface NextAction {
  action_type: string
  description: string
  affected_approval_id: string | null
  affected_document_key: string | null
  link_section: string
}

export interface ApplicationOrchestration {
  application_id: string
  overall_status: OrchestrationStatus
  approvals: Record<string, ApprovalOrchestration>
  total_blockers: number
  next_action: NextAction | null
  stage_number: number | null
  explanation: string
}
```

- [ ] **Step 2: Add API client method**

Add to `api` object in `api.ts`:
```typescript
orchestration: {
  get: (appId: string) =>
    request<ApplicationOrchestration>(`/applications/${appId}/orchestration`),
},
```

- [ ] **Step 3: Verify tsc**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 4: Commit**

---

### Task 6: Add ReadinessCard to Staff Application Detail

**Files:**
- Modify: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

- [ ] **Step 1: Add orchestration state and data fetching**

Add state: `const [orchestration, setOrchestration] = useState<ApplicationOrchestration | null>(null)`
Add useEffect to fetch orchestration on load.

- [ ] **Step 2: Add ReadinessCard component**

The card shows:
- Overall status badge (color-coded: READY=green, BLOCKED=red, REVIEW_REQUIRED=yellow, INSUFFICIENT_DATA=gray)
- Next action description with link to relevant section
- Blocker list with type, description, affected approval/document, action required
- Per-approval breakdown showing status, applicability, dependency, document readiness
- Stage number from dependency graph

- [ ] **Step 3: Place ReadinessCard after SLA card in the layout**

- [ ] **Step 4: Verify tsc and build**

Run: `cd frontend && npx tsc --noEmit && npx vite build`

- [ ] **Step 5: Commit**

---

### Task 7: Add ReadinessCard to Applicant Application Detail

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`

- [ ] **Step 1: Add orchestration state and data fetching** (same pattern as staff page)

- [ ] **Step 2: Add ReadinessCard** (simplified for applicant — show status, next action, blockers; hide internal dependency details)

- [ ] **Step 3: Place ReadinessCard after SLA card**

- [ ] **Step 4: Verify tsc and build**

- [ ] **Step 5: Commit**

---

### Task 8: Run Full Verification

- [ ] **Step 1: Backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass (existing 538 + new orchestration tests)

- [ ] **Step 2: Backend lint**

Run: `cd backend && python -m ruff check app/ tests/`
Expected: Clean

- [ ] **Step 3: Frontend checks**

Run: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`
Expected: tsc clean, oxlint clean (pre-existing warnings only), build success

- [ ] **Step 4: Update documentation**

Update AGENTS.md, ARCHITECTURE.md, RULES.md, PRD.md with Phase 6 status.

- [ ] **Step 5: Final commit**
