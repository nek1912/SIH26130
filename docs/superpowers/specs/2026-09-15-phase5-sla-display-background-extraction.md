# Phase 5 — SLA Display & Background Extraction

**Date:** 2026-09-15
**Status:** Approved
**Next engineering step after this phase:** Phase 6 (TBD)

## Goal

Expose existing SLA computation through the application workflow and add background document extraction so upload does not block on processing.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Workflow events persistence | Persist to DB | SLA computation requires stage entry timestamps; in-memory events are lost on restart |
| Background extraction mechanism | FastAPI BackgroundTasks | Simplest, no new dependencies, extraction is fast (<1s per doc) |
| Upload→extraction flow | Auto-extract on upload | Better UX, no extra user step |
| SLA visibility | Both applicant and staff pages | Applicant needs to see their timeline |

## Part A — SLA Display

### A1. Persist workflow_events

**New table:** `workflow_events`

```sql
CREATE TABLE workflow_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  from_status TEXT,
  to_status TEXT NOT NULL,
  action TEXT NOT NULL,
  performed_by UUID NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_workflow_events_app ON workflow_events(application_id, created_at);
```

**New repository:** `backend/app/repositories/workflow_events.py`
- `list_for_application(application_id: str) -> list[dict]` — ordered by created_at
- `create(event_data: dict) -> dict` — insert event

**Modify:** `backend/app/workflow/engine.py`
- `execute_transition()` currently returns an in-memory `WorkflowEvent` dict
- Add optional `events_repository` parameter; when provided, persist the event
- Existing callers without the repository continue to work (backward compatible)

**Modify:** `backend/app/api/workflow.py`
- Inject `WorkflowEventsRepository` into transition handlers
- Pass it to `execute_transition()` so events are persisted

### A2. SLA API endpoint

**New endpoint:** `GET /applications/{application_id}/sla`

Logic:
1. Load application from DB
2. Load workflow events from `workflow_events` table
3. Load approval to get workflow stages definition
4. Call existing `compute_application_sla()` from `app/workflow/sla.py`
5. Return SLA info or `null` if no SLA applies

**Response shape:**
```json
{
  "stage_key": "review",
  "stage_label": "Under Review",
  "sla_business_days": 10,
  "entered_at": "2026-09-10",
  "due_date": "2026-09-24",
  "used_business_days": 3,
  "remaining_business_days": 7,
  "overdue_business_days": 0,
  "state": "on_track"
}
```

**New repository method:** `ApplicationsRepository.get_approval_stages(approval_id)` — loads workflow_definition JSONB from approvals table.

### A3. Frontend SLA display

**Add SLA card** to both `frontend/src/pages/applicant/ApplicationDetailPage.tsx` and `frontend/src/pages/staff/ApplicationDetailPage.tsx`:

- Fetches from `GET /applications/{id}/sla` on load
- Displays:
  - Stage name + SLA target (e.g., "Under Review — 10 business days")
  - Due date
  - Remaining or overdue business days
  - Color-coded badge: green (on_track), yellow (due_soon), red (breached)
- Shows "No SLA" when response is null (inactive status or no SLA target)

**Add TypeScript type:** `SlaInfo` in `frontend/src/types/api.ts`

**Add API client method:** `api.applications.getSla(appId)` in `frontend/src/lib/api.ts`

## Part B — Background Extraction

### B1. Extraction status on documents

**Migration:** Add column to `documents` table:

```sql
ALTER TABLE documents ADD COLUMN extraction_status TEXT DEFAULT 'pending';
-- Values: pending | running | succeeded | failed | unsupported
```

This is the document-level status visible in the checklist, separate from `extraction_results` which stores the detailed extraction data. The `pending` state is transient — BackgroundTasks runs inline so the transition to `running` happens almost immediately after upload returns.

### B2. Background extraction on upload

**Modify:** `backend/app/api/documents.py` upload endpoint

After creating the document record and returning the response:
1. Enqueue a FastAPI `BackgroundTasks` job
2. The background job:
   - Sets `extraction_status = "running"` on the document
   - Downloads file from Supabase Storage
   - Calls `extract_document()` from `app/extraction/service.py`
   - Stores extraction results via existing repository methods (`delete_extracted_fields_for_document`, `create_extraction_result`, `create_extracted_fields_bulk`)
   - Updates `extraction_status` to `"succeeded"`, `"failed"`, or `"unsupported"`
   - Catches all exceptions; logs errors without exposing secrets or internal paths
   - If document already has `extraction_status = "succeeded"`, skips (idempotent)

**Helper function:** `backend/app/extraction/background.py`
- `run_extraction_background(document_id, application_id)` — the BackgroundTasks callable
- Accepts document_id, fetches all needed data internally
- Uses existing `extract_document()` service
- Uses existing `DocumentsRepository` for persistence

### B3. Idempotency

- `delete_extracted_fields_for_document()` already clears previous extraction data
- Background job checks `extraction_status` before starting; skips if already `"succeeded"`
- Re-running extraction (manual Extract button) replaces existing data deterministically

### B4. Error handling

- All exceptions caught inside background job
- `extraction_status` set to `"failed"` with error message stored in `extraction_results.errors`
- No secrets, storage paths, or internal details exposed to the client
- Failed extractions can be retried by clicking Extract button (re-triggers background job)

### B5. Frontend extraction states

**Update document checklist** in both applicant and staff `ApplicationDetailPage.tsx`:

- Show `extraction_status` badge per document:
  - `pending` → gray badge "Pending"
  - `running` → blue badge with spinner "Extracting..."
  - `succeeded` → green badge "Extracted"
  - `failed` → red badge "Failed" (with retry button)
  - `unsupported` → yellow badge "Unsupported"
- After upload, poll or refetch extraction summary to show status progression
- Existing Extract/Validate buttons remain for manual re-extraction

**Update TypeScript types:** Add `extraction_status` to `UploadedDocument` interface.

## Testing

### SLA tests
- `compute_application_sla()` already has unit tests — no changes needed to pure logic
- New tests for:
  - SLA endpoint returns correct data when events exist
  - SLA endpoint returns null for inactive status
  - SLA endpoint returns null when no SLA target on stage
  - SLA endpoint requires authentication
  - SLA endpoint enforces ownership

### Workflow events tests
- Events persisted on every transition
- `list_for_application()` returns events ordered by time
- Events include correct from_status, to_status, action, performed_by

### Background extraction tests
- Upload returns immediately with `extraction_status: "pending"`
- Background job sets status to `"running"` then `"succeeded"`
- Failed extraction sets status to `"failed"` with error logged
- Unsupported MIME type sets status to `"unsupported"`
- Idempotent: re-running on succeeded document skips
- Background job does not expose secrets in error messages

### Frontend tests
- TypeScript: `tsc --noEmit` — 0 errors
- Lint: `oxlint` — clean
- Build: `vite build` — success

### Full check suite
- Backend: `cd backend && python -m pytest tests/ -v`
- Backend lint: `cd backend && python -m ruff check app/ tests/`
- Frontend: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`

## Files to create/modify

### New files
- `backend/app/repositories/workflow_events.py` — workflow events repository
- `backend/app/extraction/background.py` — background extraction job
- `backend/tests/test_workflow_events.py` — workflow events persistence tests
- `backend/tests/test_sla_api.py` — SLA endpoint tests
- `backend/tests/test_background_extraction.py` — background extraction tests
- `supabase/migrations/005_workflow_events_sla.sql` — workflow_events table + extraction_status column

### Modified files
- `backend/app/workflow/engine.py` — optional events_repository parameter
- `backend/app/api/workflow.py` — inject events repository
- `backend/app/api/documents.py` — background extraction on upload
- `backend/app/api/applications.py` — add SLA endpoint
- `backend/app/main.py` — no new routers needed (SLA added to applications router)
- `backend/app/repositories/applications.py` — get_approval_stages method
- `frontend/src/types/api.ts` — SlaInfo type, extraction_status on UploadedDocument
- `frontend/src/lib/api.ts` — applications.getSla method
- `frontend/src/pages/applicant/ApplicationDetailPage.tsx` — SLA card + extraction status
- `frontend/src/pages/staff/ApplicationDetailPage.tsx` — SLA card + extraction status

## Known limitations

- No Indian holiday calendar — business days exclude weekends only
- No SLA breach notifications (deferred)
- No extraction retry queue (manual retry via button)
- No OCR for image-based documents (existing limitation)
- Background extraction runs in-process; if the server restarts mid-extraction, the document stays in "running" state (acceptable for MVP)
