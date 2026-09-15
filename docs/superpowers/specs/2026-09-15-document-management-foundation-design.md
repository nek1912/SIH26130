# Design Spec: Phase 3C — Document Management Foundation

**Date:** 2026-09-15
**Status:** Approved
**Scope:** MVP document checklist, upload, metadata, requirement/readiness status, Supabase Storage, deterministic validation, auditability

## 1. Goal

Implement the document management foundation required by the PRD:
- Document checklist per application (derived from workbook Document_Register)
- Document upload with server-side validation
- Document metadata and readiness status
- Secure Supabase Storage integration (backend-proxied)
- Deterministic file type/size validation
- Audit trail for document actions

Explicitly deferred: OCR, PDF extraction, LLM extraction, embeddings, RAG, cross-document consistency.

## 2. Data Model

### 2.1 New table: `document_requirements`

```sql
create type document_readiness as enum (
  'pending', 'uploaded', 'valid', 'invalid', 'review_required'
);

create table document_requirements (
  id                  uuid primary key default gen_random_uuid(),
  application_id      uuid not null references applications(id) on delete cascade,
  requirement_key     text not null,          -- D01-D17 from Document_Register
  document_name       text not null,          -- human-readable name
  approval_id         text not null,          -- A01-A18, the approval this req serves
  domain              text not null,          -- LAND, BUILDING, ENVIRONMENT, etc.
  requirement_level   text not null default 'required', -- 'required' | 'mandatory' | 'conditional'
  readiness           document_readiness not null default 'pending',
  accepted_mime_types jsonb,                  -- e.g. ["application/pdf"]
  max_size_mb         integer,
  description         text,
  source_basis        text,                   -- "GIDC page"
  source_url          text,                   -- official URL
  document_role       text,                   -- "Applicant document", etc.
  uploaded_document_id uuid references documents(id),
  rejection_reason    text,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create unique index idx_doc_req_app_key on document_requirements(application_id, requirement_key);
create index idx_doc_req_application on document_requirements(application_id);
```

### 2.2 Existing table: `documents` (unchanged)

The existing `documents` table stores uploaded files. Its `status` enum (`pending_upload`, `uploaded`, `verified`, `rejected`, `virus_detected`, `expired`) maps to validation outcomes. Its `requirement_key` links back to `document_requirements.requirement_key`.

### 2.3 Status mapping

| Task concept | `document_requirements.readiness` | `documents.status` |
|---|---|---|
| REQUIRED | `pending` | (no document) |
| UPLOADED | `uploaded` | `uploaded` |
| VALID | `valid` | `verified` |
| INVALID | `invalid` | `rejected` |
| REVIEW_REQUIRED | `review_required` | `uploaded` |

## 3. Seed Data

### 3.1 New file: `backend/app/seed/documents.py`

Contains the 17 document requirements from the verified workbook's Document_Register sheet, hardcoded as Python data (matching pattern in `approvals.py`).

Each entry:
- `requirement_key`: D01-D17 (workbook `doc_id`)
- `document_name`: workbook `document` column
- `approval_ids`: derived from workbook `used_for` column via `parse_used_for()`
- `domain`: workbook `domain`
- `requirement_level`: workbook `requirement` (mapped to standardized values)
- `source_basis`, `source_url`, `document_role`: from workbook

### 3.2 Approval-to-document mapping

The `used_for` text maps to approval IDs:

| used_for text | approval_ids |
|---|---|
| GIDC Plan/Water/Drainage | A01, A02, A03 |
| GIDC Water/Drainage | A02, A03 |
| GIDC Plan | A01 |
| GPCB CTE | A04 |
| GPCB CTE + environmental | A04, A05 |
| GPCB/ HOWM | A04, A11 |
| MSIHC | A12 |
| Fire Safety | A06 |
| CEICED/IFP | A10 |
| Labour/DISH | A07, A08 |
| PARIVESH | A05 |
| PESO | A17 |
| CGWA | A18 |

### 3.3 Per-application requirement generation

When listing requirements for an application:
1. Look up the application's `approval_id`
2. Find all document requirements where the approval is in the `approval_ids` list
3. Return those requirements with their current readiness status

## 4. Supabase Storage

### 4.1 Bucket

Private `documents` bucket (no public access). Created via Supabase dashboard or migration.

### 4.2 Storage path

```
applications/{application_id}/{requirement_key}/{sanitized_filename}
```

### 4.3 Upload flow (server-side)

1. Frontend sends `POST /applications/{app_id}/documents/{req_key}/upload` with multipart form data
2. Backend verifies application exists + user ownership
3. Backend validates: file present, MIME type, file size, filename sanitization
4. Backend uploads to Supabase Storage via service-role key
5. Backend creates `documents` record
6. Backend updates `document_requirements.readiness` to `uploaded`
7. Backend creates audit event

### 4.4 Security

- All storage access through FastAPI backend (service-role key never exposed to frontend)
- Ownership check on every upload
- Path traversal prevention (strip `/`, `\`, null bytes, `..`)
- Server-side MIME and size validation

### 4.5 Config

Add `supabase_storage_bucket: str = "documents"` to `Settings`.

## 5. API Endpoints

All endpoints use existing auth dependencies.

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/applications/{app_id}/document-requirements` | Checklist for application | owner/view |
| `GET` | `/applications/{app_id}/documents` | Uploaded documents list | owner/view |
| `POST` | `/applications/{app_id}/documents/{req_key}/upload` | Upload document | owner/create |
| `GET` | `/applications/{app_id}/documents/{doc_id}` | Document metadata | owner/view |
| `DELETE` | `/applications/{app_id}/documents/{doc_id}` | Delete uploaded document | owner/create |

### 5.1 Pydantic schemas

```python
class DocumentRequirementResponse(BaseModel):
    id: str
    requirement_key: str
    document_name: str
    approval_id: str
    domain: str
    requirement_level: str
    readiness: str
    accepted_mime_types: list[str] | None
    max_size_mb: int | None
    description: str | None
    source_basis: str | None
    source_url: str | None
    document_role: str | None
    uploaded_document_id: str | None
    rejection_reason: str | None

class DocumentResponse(BaseModel):
    id: str
    application_id: str
    requirement_key: str
    original_filename: str
    storage_path: str
    mime_type: str
    file_size_bytes: int
    status: str
    rejection_reason: str | None
    uploaded_by_user_id: str | None
    created_at: str
```

### 5.2 Error responses

- 404: Application or requirement not found
- 403: Not authorized
- 400: Invalid file type, oversized, missing
- 409: Requirement already has document (delete first)

## 6. Audit

Use existing `audit_log` table. Actions:
- `document:upload` — new_values includes filename, mime_type, file_size, requirement_key
- `document:validate` — new_values includes validation result
- `document:delete` — previous_values includes document metadata

Append-only, immutable (existing pattern).

## 7. Frontend

### 7.1 Types (`types/api.ts`)

Add `DocumentRequirement` and `Document` interfaces matching API schemas.

### 7.2 API client (`lib/api.ts`)

Add `documents` namespace with methods for list requirements, list documents, upload, get, delete.

### 7.3 Modified page: `pages/applicant/ApplicationDetailPage.tsx`

Add a "Documents" section below the existing workflow timeline:
- Checklist: requirement name, domain badge, required/optional indicator, readiness status
- Upload button per pending requirement (file input → API call)
- Show uploaded file: name, size, status badge
- Validation error display
- Loading and error states

No new pages. Documents are part of the existing application detail view.

## 8. Tests

### Backend

- Workbook document requirements load correctly (17 requirements)
- Requirement-to-approval traceability (each doc maps to correct approvals)
- Mandatory vs conditional requirements
- Authorization: applicant must own application
- Valid upload: creates document + updates readiness
- Unsupported file type: rejected with 400
- Oversized file: rejected with 400
- Missing file: rejected with 400
- Storage path isolation: different apps get different paths
- Document status transitions: pending → uploaded → valid/invalid
- Audit event creation on upload
- API error responses (404, 403, 400, 409)
- Requirement not found for application: 404
- Duplicate upload: 409

### Frontend

- `npx tsc --noEmit` — 0 errors
- `npx oxlint` — no new warnings
- `npx vite build` — success

### Backend baseline

Existing: 402 passed, 23 failed (pre-existing Supabase config), 4 skipped.
These 23 failures are NOT caused by this task and must not be deleted or weakened.

## 9. Implementation order

1. Migration: `document_requirements` table + enum
2. Seed data: `backend/app/seed/documents.py`
3. Repository: `backend/app/repositories/documents.py`
4. API routes: `backend/app/api/documents.py`
5. Auth deps: add document repo to `deps.py`
6. Config: add storage bucket setting
7. Storage integration: upload/download/delete helpers
8. Frontend types + API client
9. Frontend UI: document checklist in ApplicationDetailPage
10. Tests: backend + frontend checks
11. Context file updates
