# Architecture — SIH 26130 Gujarat MVP

## 1. Product boundary

This is not a replacement for Gujarat's complete single-window system. It is a project-specific intelligence and workflow layer for a small, verified Gujarat industrial scenario.

Core flow:

`Project facts → applicability rules → approval graph → documents/workflow/SLA → next action`

RAG is a supporting layer:

`Official sources → retrieval → cited explanation`

## 2. Repository strategy

### Source repositories (deleted after extraction)
Both source repositories (`Digital-Permit-Platform/` and `compliance-grid/`) have been deleted after extraction. All necessary logic has been ported to Python. No executable references to them remain.

### Extracted from Digital-Permit-Platform
- Workflow state machine (14 statuses, stage types, SLA targets)
- Dynamic form model (FormSection, FormField, ConditionalRule)
- RBAC (4 roles, 18 permissions)
- SLA computation (business day calc, breach detection)
- Audit logging (append-only, previousValues/newValues)

### Extracted from Compliance-Grid
- Obligation schema and applicability engine
- Deadline rules (fixed-date, period-offset, event-offset, Indian fiscal year)
- Source citation enforcement and canonical key/versioning
- Applicability condition validation

## 3. Logical architecture

```text
React UI
  |
  v
FastAPI REST API
  |
  +-- Project / Applicant
  +-- Approval / Case
  +-- Documents
  +-- Rules / Applicability
  +-- Workflow / Tasks / Queries
  +-- SLA / Notifications
  +-- Regulatory Search / RAG
  +-- Incentives (small MVP)
  |
  v
Supabase PostgreSQL
  +-- relational domain data
  +-- pgvector if justified
  +-- RLS policies

Supabase Storage
  +-- uploaded documents

Background worker (only when needed)
  +-- document extraction/indexing
  +-- notifications
```

## 4. Frontend

React + TypeScript + Vite + Tailwind CSS.

Keep frontend responsibilities limited to presentation, form interaction, client validation, API state, navigation and user feedback. Business/regulatory rules belong in the backend.

Suggested feature areas:
- project creation/wizard
- approval journey
- approval detail/reasoning
- documents
- queries
- timeline/SLA
- regulatory assistant
- officer/admin views only if needed for the demo

## 5. Backend

FastAPI is the application/API boundary.

Suggested domain modules:

```text
app/
  api/
  core/
  auth/
  projects/
  approvals/
  rules/
  workflow/
  documents/
  regulatory/
  incentives/
  audit/
  tests/
```

Use Pydantic models for API contracts and validation. Keep domain logic out of route handlers. Use a repository/service boundary only where it removes real duplication; do not create layers mechanically.

## 6. Core domain model

```text
Project
  └─ ProjectFacts

Approval
  ├─ ApprovalRule
  ├─ Requirement
  ├─ Dependency
  ├─ SLARule
  └─ SourceReference

ApplicationCase
  ├─ ApprovalApplication
  ├─ Task
  ├─ Query
  ├─ Inspection
  └─ AuditEvent

Document
  ├─ ExtractedField
  ├─ ValidationResult
  └─ ConsistencyResult

RegulatorySource
  └─ SourceVersion
```

## 7. Applicability engine

Input: structured project facts + versioned rules.

Output for each approval:
- `APPLIES`
- `DOES_NOT_APPLY`
- `CONDITIONAL`
- `INSUFFICIENT_DATA`

Every non-trivial result must retain:
- rule ID/version,
- triggered facts,
- source reference,
- evaluation timestamp.

Never use an LLM as the final applicability calculator.

## 8. Approval graph

Represent relationships explicitly. Examples:
- prerequisite approval/status
- required document
- dependency between workflow stages
- parallel-safe task
- renewal relationship

Do not assume every ordering relationship is a legal prerequisite.

## 9. RAG

Pipeline:

`official source → parse → metadata → chunk/index → hybrid retrieval → rerank if justified → LLM → citation`

Metadata should include jurisdiction, authority, document type, source date, effective dates and version/supersession where available.

RAG can explain and locate evidence. It must not silently override structured rules.

## 10. Documents

`upload → secure storage → type/size validation → extraction → structured fields → deterministic validation → human review where needed`

Cross-document consistency checks produce warnings/flags, not automatic legal rejection.

## 11. Auth/security

Use Supabase Auth for identity unless the inherited base provides a simpler compatible path. The frontend must never receive privileged database credentials.

Apply least privilege, ownership checks, RBAC and Supabase RLS where applicable. Store an audit event for material state/data changes.

## 12. Government integration

Treat external government integration as an adapter boundary. Only implement real integration after an actual authorized API/process is verified. Otherwise use explicitly labelled mock/demo adapters.

## 13. Deployment

MVP should be deployable without a microservice fleet:
- React/Vite frontend
- FastAPI backend
- Supabase hosted Postgres/Auth/Storage
- optional single worker for asynchronous jobs

Do not introduce Kafka, Kubernetes, service mesh, separate vector database, or multiple backend services unless a measured requirement forces the decision.

## 14. Non-negotiable architectural principle

`Deterministic rules decide. RAG retrieves. LLM explains. Human authority decides.`

## 15. Repository inspection findings (2026-09-14)

### Digital-Permit-Platform
- **Stack**: Next.js 15 + Prisma 6.19 + PostgreSQL 16 + Azure (Blob, Bicep, Entra, OpenAI) + BullMQ/Redis. MIT (Microsoft).
- **No Python. No Vite. No Supabase.** Entirely TypeScript full-stack.
- **Reusable concepts** (port to Python, not copy-paste):
  - Configuration-driven module system (ModuleVersion with JSONB form/workflow/document schemas, versioned so historic submissions freeze)
  - Workflow state machine (14 states, stage types, SLA targets, optimistic locking, audit trail)
  - Dynamic form model (FormSection[] → FormField[], 14 field types, ConditionalRule evaluator)
  - RBAC (4 roles, 16 permissions, server-side enforcement)
  - SLA computation (business day calc, per-stage targets, breach detection)
  - Audit logging (append-only, previousValues/newValues snapshots)
  - Document lifecycle (upload → validate → extract → verify → flag inconsistencies)
- **Discard**: Next.js pages/API routes, Prisma client, NextAuth, Azure Blob, Azure Bicep, BullMQ, GOV.UK CSS, UK licensing domain, council setup, DOCX generation.

### Compliance-Grid
- **Stack**: Next.js 16 + pg driver + PostgreSQL 17 (pgvector) + Anthropic SDK. MIT (community).
- **No Python. No FastAPI.** TypeScript full-stack with raw SQL.
- **Reusable concepts** (port to Python):
  - Obligation schema: canonical_id, instrument_ref, applicability_conditions[], frequency, deadline_rule, penalty, source_refs[] (anti-hallucination: source_refs non-empty), version, confidence
  - Applicability engine: structured { field, op, value } predicates, deterministic evaluateApplicability()
  - Deadline rules: fixed-date, period-offset, event-offset (Indian fiscal year aware)
  - Source citation enforcement and canonical key/versioning
  - Document extraction pipeline: acquire → segment → extract → gate → commit or review
  - Source Index: 436 YAML files of Indian regulator portals (9 Gujarat entries exist)
  - Review queue: confidence threshold routing (≥0.9 auto-commit, <0.9 human review)
- **Discard**: Next.js pages/server actions, custom auth, federation protocol, OCR/Playwright, cg CLI, health scoring, projection cache.

### Key architectural fact
Both source repos are TypeScript/Next.js. Our locked stack requires Python/FastAPI backend + Vite frontend. **Every backend logic module must be rewritten in Python.** The frontend must be extracted from Next.js App Router into a Vite SPA. This is the primary migration cost.

## 16. Phase 1 implementation status (2026-09-14)

### Created
- `backend/` — FastAPI + Python project with pyproject.toml
- `supabase/migrations/001_initial_schema.sql` — 12 tables merging DPP + CG patterns

### Implemented (pure logic, all tested)
- `app/rules/models.py` — Obligation, ApplicabilityCondition, DeadlineRule, EntityProfile, Instrument, Source, Frequency, Penalty, ObligationCandidate, ApprovalRule, ApplicabilityEvaluation (Pydantic v2)
- `app/rules/engine.py` — `evaluate_applicability()` deterministic filter
- `app/rules/applicability.py` — `evaluate_rule()`, `evaluate_approval_applicability()`, `summarize_evaluations()` — generic, data-driven approval applicability engine returning APPLIES/DOES_NOT_APPLY/CONDITIONAL/INSUFFICIENT_DATA with full traceability
- `app/rules/deadline.py` — `compute_due_date()` with Indian fiscal year (March 31 year-end)
- `app/rules/canonical.py` — `canonicalize()` + `version()` monotonic integer-strings
- `app/rules/validation.py` — `validate_applicability_conditions()` semantic validation (7 allowed fields, type checks)
- `app/forms/models.py` — FormField, FormSection, ConditionalRule, DocumentRequirement, WorkflowStage (from DPP types/module.ts)
- `app/forms/conditions.py` — `evaluate_condition()` (8 operators), `get_visible_fields()`, `get_required_documents()`
- `app/workflow/models.py` — ApplicationStatus (14 states), STAGE_TYPE_TO_STATUS mapping, ACTIVE_STATUSES
- `app/workflow/sla.py` — `compute_application_sla()` + `summarise_sla()` with business day arithmetic
- `app/audit/service.py` — AuditEntry, AuditRecord, `create_audit_record()`
- `app/auth/permissions.py` — 4 roles, 18 permissions, `has_permission()`, `has_any_permission()`

### Tests
- 271 tests across 10 test files, all passing
- Coverage: applicability, approval applicability, deadline, canonical, validation, conditions, SLA, permissions, audit, models

### Not yet implemented
- Supabase Storage for documents
- Frontend (Vite SPA)
- RAG/LLM integration
- Document extraction/OCR

## 17. Phase 2A implementation status (2026-09-14)

### Created
- `backend/app/core/config.py` — Settings class with Pydantic BaseSettings (supabase_url, supabase_key, etc.)
- `backend/app/db/client.py` — Supabase client factory (`get_supabase()` with lru_cache)
- `backend/app/repositories/` — 7 repository modules (base, projects, project_facts, approvals, obligations, sources, applications)
- `backend/app/api/` — FastAPI routes (health, projects, approvals, applications) with dependency injection
- `backend/app/main.py` — FastAPI app with all routers

### Implemented
- Database access layer with BaseRepository CRUD (get_by_id, get_all, create, update, delete)
- Specialized repositories for project facts (upsert), applications (create_with_reference), etc.
- FastAPI dependency injection via `app/api/deps.py`
- REST API endpoints: health, projects CRUD, approvals/obligations read, applications CRUD
- Applicability evaluation endpoint (`POST /obligations/applicable`)

### Tests
- 137 passing tests (119 original + 18 new Phase 2A tests)
- 4 skipped (API DB-dependent tests requiring real Supabase connection)
- All lint checks passing (ruff)

### Known limitations
- API endpoint tests for DB-dependent routes are skipped (mock injection issue with lru_cache)
- No Supabase RLS enforcement (backend only)

### Next phase
- Phase 2C: Frontend (Vite SPA with React + TypeScript)

## 18. Phase 2B implementation status (2026-09-14)

### Created
- `backend/app/auth/models.py` — `UserContext` Pydantic model (frozen, user_id/email/role/raw_claims)
- `backend/app/auth/dependencies.py` — FastAPI dependencies for auth + authorization
- `backend/tests/conftest.py` — Test env vars for JWT secret/audience
- `backend/tests/test_auth.py` — 48 auth tests

### Implemented
- JWT verification using PyJWT with HS256 (Supabase-compatible)
- Token extraction from `Authorization: Bearer <token>` header
- User identity extraction: `sub` → user_id, `email`, `app_metadata.role` → role
- `get_current_user` FastAPI dependency — verifies JWT, returns `UserContext`
- `require_permission(Permission)` — dependency factory enforcing single permission
- `require_any_permission(*Permission)` — dependency factory enforcing at least one permission
- `check_project_ownership()` — ownership enforcement for projects (applicant must own, staff bypasses)
- `check_application_ownership()` — ownership enforcement for applications
- Role resolution from `app_metadata.role` with fallback to APPLICANT
- All non-health API endpoints protected with auth dependencies
- Proper 401 (missing/invalid token) and 403 (insufficient permission) responses
- Settings expanded: `auth_jwt_secret`, `auth_jwt_algorithm`, `auth_jwt_audience`

### Auth flow
1. Client sends `Authorization: Bearer <supabase_jwt>` header
2. `get_current_user` dependency extracts and verifies the JWT
3. JWT is decoded with the Supabase JWT secret (HS256)
4. `sub` claim → `user_id`, `app_metadata.role` → `SystemRole`
5. `UserContext` is passed to the route handler
6. `require_permission` / `require_any_permission` checks RBAC
7. Ownership functions verify resource access for applicants

### RBAC mapping to routes
| Route | Required permission(s) |
|-------|----------------------|
| `POST /projects` | `application:create` |
| `GET /projects/{id}` | `application:view_own` OR `view_team` OR `view_all` |
| `GET /projects/{id}/facts` | `application:view_own` OR `view_team` OR `view_all` |
| `POST /projects/{id}/facts` | `application:create` |
| `POST /applications` | `application:create` |
| `GET /applications/{id}` | `application:view_own` OR `view_team` OR `view_all` |
| `GET /projects/{id}/applications` | `application:view_own` OR `view_team` OR `view_all` |
| `GET /approvals` | `module:view` |
| `GET /approvals/{id}` | `module:view` |
| `GET /obligations` | `module:view` |
| `POST /obligations/applicable` | `module:view` |
| `GET /health` | (none — public) |
| `GET /` | (none — public) |

### Tests
- 185 passing tests (137 original + 48 new Phase 2B tests)
- 4 skipped (API DB-dependent tests requiring real Supabase connection)
- All lint checks passing (ruff)

### Dependencies added
- `PyJWT>=2.8,<3` — JWT decoding/verification

### Known limitations
- User role is read from `app_metadata.role` in the JWT (Supabase user metadata)
- No user-role lookup from Supabase database yet (role stored in JWT)
- No session refresh or token rotation (handled by Supabase client)
- No CORS middleware configured yet (frontend not implemented)
- Ownership checks for applications are simplified (no project lookup for applicant verification)

### Next phase
- Phase 2C: Frontend (Vite SPA with React + TypeScript)

## 19. Phase 2C implementation status (2026-09-14)

### Created
- `backend/app/workflow/stages.py` — `StageType` enum, `WorkflowStage`, `WorkflowDefinition` Pydantic models
- `backend/app/workflow/engine.py` — Transition engine with rules, guards, optimistic locking, event creation
- `backend/app/workflow/assignments.py` — Assignment/queue helpers, status display names
- `backend/app/api/workflow.py` — 8 workflow API endpoints (submit, advance, request-info, respond, assign, approve, refuse, withdraw)
- `backend/tests/test_workflow_engine.py` — 68 workflow tests

### Implemented
- Workflow stage definitions: 8 stage types, ordered stages, SLA targets per stage
- Transition rules matrix: 22 valid transitions covering all application statuses
- Role-permission enforcement per transition
- `can_transition()` — validates transition legality (status + action + role)
- `execute_transition()` — stateless transition executor (creates events + audit records)
- Workflow event creation: immutable record of every state change
- Audit record creation for every transition (previous/new values snapshots)
- Assignment: MANAGER/ADMIN can assign, REVIEWER can review, role-based queue filtering
- Terminal status detection and display name helpers
- Full lifecycle paths: submit→review→decide, query→respond, withdraw, cancel
- All 14 statuses have valid outgoing transitions

### Tests
- 253 passing tests, 4 skipped, all lint clean

### Known limitations
- No optimistic locking at the database level (caller must use conditional updates)
- No notification system for SLA breaches
- No auto-assignment logic (manual assignment only)
- Workflow definition is not persisted in DB yet (stages are passed at call time)

### Next phase
- Phase 3B: Frontend pages (project wizard, application journey, documents)

## 20. Phase 3A implementation status (2026-09-14)

### Created
- `frontend/` — Vite + React + TypeScript + Tailwind v4 SPA
- `frontend/src/lib/supabase.ts` — Supabase client initialization
- `frontend/src/lib/api.ts` — Thin REST API client with auth header injection
- `frontend/src/types/api.ts` — TypeScript types matching backend API shapes
- `frontend/src/contexts/AuthContext.tsx` — Auth provider with Supabase session management
- `frontend/src/components/ProtectedRoute.tsx` — Auth guard with role-based access
- `frontend/src/components/layout/` — Sidebar, Topbar, AppLayout
- `frontend/src/components/ui/` — Button, Input, Label, Card, Badge (Tailwind v4)
- `frontend/src/components/shared/` — StatusBadge, LoadingSpinner
- `frontend/src/pages/auth/LoginPage.tsx` — Email/password login via Supabase
- `frontend/src/pages/applicant/` — ProjectList, ProjectCreate, ProjectDetail, ApplicationList, ApplicationSubmit
- `frontend/src/pages/staff/` — QueuePage (placeholder), ApplicationDetail with workflow actions
- `backend/app/main.py` — CORSMiddleware added for frontend dev server

### Implemented
- Vite + React + TypeScript + Tailwind v4 project setup
- CSS-first Tailwind v4 theme with semantic color tokens (OKLCH)
- Supabase Auth integration (login, logout, session persistence, role extraction)
- Protected routes with role-based access (APPLICANT vs REVIEWER/MANAGER/ADMIN)
- React Router v6 with role-separated route trees
- Sidebar + topbar layout with responsive design
- API client: all backend endpoints mapped (projects, approvals, obligations, applications, workflow)
- Workflow status display with available actions per status
- Applicant flow: login → project list → create → detail → application list → submit
- Staff flow: login → application queue (placeholder) → detail with workflow actions

### Checks
- TypeScript: `tsc --noEmit` — 0 errors
- Lint: `oxlint` — 1 minor warning (Fast Refresh: AuthContext exports component + hook)
- Build: `vite build` — success (20.83 kB CSS, 262.14 kB JS, gzipped 88.21 kB total)
- Backend tests: 253 passed, 4 skipped, 0 failed
- Backend lint: ruff — all checks passed

### Dependencies added (frontend)
- `react@^19.2.8`, `react-dom@^19.2.8`
- `react-router-dom@^7.18.3`
- `tailwindcss@^4.3.3`, `@tailwindcss/vite@^4.3.3`
- `@supabase/supabase-js@^2.116.0`
- Dev: `oxlint`, `typescript@~6.0.2`, `vite@^8.3.0`

### Dependencies added (backend)
- `fastapi[standard]` (CORSMiddleware — already included in FastAPI)

### Missing API contracts
- `GET /applications` — Staff queue requires listing all applications across projects. Currently only `GET /projects/{id}/applications` exists (scoped to a single project). Need a staff-level endpoint that returns all applications with optional status/assignee filters.

### Known limitations
- Staff queue does not show project names (requires a join or separate query)
- No workflow event history persistence (events created in-memory during transitions)
- No document upload/view UI (deferred)
- No SLA display in frontend (SLA logic exists in backend but not exposed via API)
- No CORS configuration for production deployment
- No environment variable validation at runtime

### Next phase
- Phase 3C: Document management, SLA display, workflow event history

## 21. Phase 3B implementation status (2026-09-14)

### Created
- `backend/app/api/applications.py` — `GET /applications` endpoint (staff-only, filters, pagination)
- `backend/app/repositories/applications.py` — `list_all_with_filters()` method
- `backend/tests/test_api_applications_list.py` — 13 tests (repository unit + endpoint validation)
- `frontend/src/pages/staff/QueuePage.tsx` — Real application queue with status filter and pagination
- `frontend/src/pages/staff/ApplicationDetailPage.tsx` — Staff detail with workflow actions, reason input, error handling
- `frontend/src/pages/applicant/ApplicationDetailPage.tsx` — Applicant detail with visual status timeline
- `frontend/src/pages/applicant/ProjectDetailPage.tsx` — Inline project facts editing

### Implemented
- `GET /applications`: staff-only, filters by status/assignee/applicant, pagination with total count
- Frontend `ApplicationStatus` aligned with backend (14 statuses)
- Staff queue: real data, status filter, pagination
- Staff detail: workflow actions per backend TRANSITION_RULES, role-based visibility, reason input, structured error handling (401/403/409/422)
- Applicant detail: visual timeline, next-action hints, status-aware actions
- Project facts editing: inline form (entity_type, sector, jurisdictions, headcount, turnover)
- Role-based routing for `/applications/:id`

### Checks
- Backend: 263 passed, 4 skipped, ruff clean
- Frontend: tsc clean, build success (21.58 kB CSS, 262.14 kB JS)

## 22. Phase 4: Dependency Engine (2026-09-15)

### Created
- `backend/app/rules/dependency_models.py` — ApprovalDependency, ReadinessStatus, ApprovalReadiness, DependencyCycleError, DependencyGraph (Pydantic v2)
- `backend/app/rules/dependency_engine.py` — `evaluate_readiness()` deterministic dependency engine with cycle detection, topological sort, stage assignment
- `backend/app/seed/dependencies.py` — 3 verified MVP dependency edges from workbook + dependency mapping report
- `backend/tests/test_dependency_engine.py` — 41 tests covering all acceptance criteria

### Implemented
- **Data models**: ApprovalDependency (directed prerequisite edge with source/evidence/traceability), ReadinessStatus (READY/BLOCKED/NOT_APPLICABLE/PENDING_EVALUATION), ApprovalReadiness (per-approval result with stage/blocking/trace), DependencyGraph (full evaluation result)
- **Dependency engine**:
  - Adjacency list construction from dependency edges
  - Cycle detection via DFS with three-color marking
  - Topological sort via Kahn's algorithm
  - Stage assignment via longest-path from root (cycle-safe)
  - Readiness evaluation in topological order
- **Dependency semantics**:
  - NOT_APPLICABLE prerequisite → not a blocker
  - INSUFFICIENT_DATA/CONDITIONAL prerequisite → BLOCKED
  - Unknown prerequisite (not in applicability) → BLOCKED
  - Prerequisite in `obtained` set → satisfied
  - Prerequisite not obtained → BLOCKED
- **MVP dependency dataset** (3 edges, all explicit):
  - A02 depends on A04 (GIDC Water requires GPCB NOC)
  - A03 depends on A04 (GIDC Drainage requires GPCB NOC)
  - A03 depends on A02 (GIDC Drainage requires water connection)
  - Produces 3-stage serial chain: A04 (stage 0) → A02 (stage 1) → A03 (stage 2)
- **Traceability**: Every readiness result includes dependency_trace with source_ref, evidence, and prerequisite_applicability

### Tests (41)
- Independent approvals run in parallel (2)
- Prerequisite blocks dependent approval (2)
- Prerequisite satisfied makes dependent READY (3)
- DOES_NOT_APPLY prerequisite not a blocker (2)
- INSUFFICIENT_DATA/CONDITIONAL prerequisite handled (3)
- Multi-level dependency produces correct stages (2)
- Independent branches share same stage (1)
- Cycle detection — simple, 3-node, false positive (3)
- Missing dependency definition (1)
- Deterministic ordering (2)
- Traceability — trace, count, explanation (3)
- Integration with applicability results (2)
- Workbook-backed scenario — blocker, unblocker, stage numbering (4)
- Edge cases — empty deps, empty applicability, self-dependency (3)
- Internal algorithms — adjacency, cycles, topo sort, stages (7)

### Checks
- Backend: 402 passed, 4 skipped, 23 failed (pre-existing Supabase config), ruff clean
- New dependency engine: 41 passed, 0 failed
- No regressions: baseline 23 failures unchanged

## 23. Phase 3C implementation status (2026-09-15)

### Created
- `backend/app/seed/documents.py` — 17 document requirements from workbook Document_Register (D01-D17)
- `backend/app/repositories/documents.py` — DocumentsRepository with requirement + document CRUD
- `backend/app/api/documents.py` — 5 REST endpoints (list reqs, list docs, upload, get, delete)
- `backend/tests/test_document_requirements.py` — 18 seed data + lookup + repository tests
- `backend/tests/test_document_upload.py` — 15 upload validation + auth tests
- `supabase/migrations/002_document_requirements.sql` — document_requirements table + document_readiness enum

### Implemented
- Document requirements per application (seeded from workbook D01-D17)
- Document upload with server-side MIME/size validation
- Supabase Storage integration (backend-proxied, private bucket)
- Filename sanitization (path traversal prevention)
- Document readiness tracking (pending/uploaded/valid/invalid/review_required)
- Audit events for upload/delete actions
- Frontend document checklist in applicant ApplicationDetailPage
- Auto-seed requirements on application creation (via approval_code parameter)
- Settings `extra = "ignore"` fix (resolved 23 pre-existing Supabase config test failures)

### Checks
- Backend: 458 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean (pre-existing warnings only), vite build success

### Known limitations
- No OCR/extraction/LLM processing (deferred to later milestone)
- No document verification/review workflow (deferred)
- No cross-document consistency checks (deferred)
- Storage bucket must be created manually in Supabase dashboard
- No signed URL generation for direct download (deferred)

### Next phase
- Phase 3D: Document extraction/OCR, consistency engine, SLA display

## 24. Phase 3D implementation status (2026-09-15)

### Created
- `backend/app/extraction/__init__.py` — extraction module
- `backend/app/extraction/models.py` — ExtractedField, ExtractionResult, ValidationResult, FieldFinding, ExtractionStatus, ValidationOutcome
- `backend/app/extraction/service.py` — PDF metadata extraction, CSV/Excel header validation
- `backend/app/extraction/validation.py` — Deterministic validation engine with rules per document domain
- `backend/app/api/extraction.py` — 5 REST endpoints (extract, validate, get extraction, get validation, summary)
- `backend/tests/test_extraction_service.py` — 15 extraction service tests
- `backend/tests/test_validation_engine.py` — 13 validation engine tests
- `backend/tests/test_extraction_api.py` — 14 API endpoint + repository tests
- `supabase/migrations/003_document_extraction.sql` — extracted_fields, extraction_results, validation_findings, validation_results tables

### Implemented
- Structured extracted-field storage linked to documents
- Document extraction status/error tracking
- Deterministic extraction for PDF (metadata: title, author, pages, file size), CSV (headers, row/column counts), Excel (sheet info, headers)
- Deterministic validation rules per document domain (11 domains from workbook)
- Explicit outcomes: VALID, INVALID, REVIEW_REQUIRED, INSUFFICIENT_DATA
- Source/rule traceability for every validation result
- Field-level findings with rule ID, description, expected/actual values
- API endpoints: POST extract, POST validate, GET extraction status, GET validation status, GET extraction summary
- Frontend extraction/validation status display in document checklist
- Frontend extract/validate buttons per uploaded document
- Frontend validation findings display with color-coded outcomes

### Checks
- Backend: 500 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean, vite build success

### Known limitations
- No OCR for image-based documents (requires external OCR service)
- No cross-document consistency checks (deferred)
- No async background extraction (runs synchronously on request)
- Storage bucket must be created manually in Supabase dashboard

### Next phase
- Phase 3E: Cross-document consistency engine
- Phase 5: SLA display, background extraction

## 25. Phase 3E implementation status (2026-09-15)

### Created
- `backend/app/consistency/__init__.py` — consistency module
- `backend/app/consistency/models.py` — ConsistencyOutcome, ConsistencyRule, ConsistencyFinding, ConsistencyResult
- `backend/app/consistency/engine.py` — `check_application_consistency()` deterministic cross-document comparison
- `backend/app/seed/consistency.py` — 18 consistency rules (C01-C18) from workbook Consistency_Fields sheet
- `backend/app/repositories/consistency.py` — ConsistencyRepository with CRUD for consistency_results/findings
- `backend/app/api/consistency.py` — 2 REST endpoints (POST check, GET latest)
- `backend/tests/test_consistency_engine.py` — 20 engine + model + seed tests
- `backend/tests/test_consistency_api.py` — 7 repository + API tests
- `supabase/migrations/004_consistency.sql` — consistency_results, consistency_findings tables

### Implemented
- Deterministic cross-document consistency engine comparing 18 canonical fields across documents
- Seed config mapping each canonical field to document requirement keys (D01-D17)
- Exact string comparison (no normalization) per workbook MUST_MATCH rules
- On-demand consistency checks via API
- Results persisted with findings per canonical field
- Frontend consistency section in both staff and applicant application detail pages
- "Run Check" button with outcome badge and findings table
- Re-running replaces previous results deterministically

### Checks
- Backend: 527 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean (pre-existing warnings only), vite build success

### Known limitations
- No OCR for image-based documents (extracted fields depend on extraction layer)
- No automatic trigger on extraction (on-demand only)
- Single-document rules always VALID (nothing to compare)
- No normalization (exact string comparison)
- Storage bucket must be created manually in Supabase dashboard

## 26. Phase 5 implementation status (2026-09-15)

### Created
- `backend/app/repositories/workflow_events.py` — WorkflowEventsRepository with `list_for_application()` and `create()`
- `backend/app/extraction/background.py` — `run_extraction_background()` for FastAPI BackgroundTasks
- `backend/tests/test_workflow_events_repo.py` — 3 repository tests
- `backend/tests/test_workflow_events_persistence.py` — 3 persistence tests
- `backend/tests/test_sla_api.py` — 2 SLA endpoint tests
- `backend/tests/test_background_extraction.py` — 3 background extraction tests
- `supabase/migrations/006_documents_extraction_status.sql` — extraction_status column on documents

### Implemented
- Workflow events persistence: optional `events_repository` parameter on `execute_transition()`, all 7 transition endpoints inject and persist events
- SLA API endpoint: `GET /applications/{id}/sla` — loads events, approval stages, computes SLA via existing `compute_application_sla()`
- Background extraction: runs via FastAPI BackgroundTasks on document upload, sets extraction_status (pending→running→completed/failed/unsupported), idempotent, error-safe
- Frontend SLA card: color-coded badge (on_track/due_soon/due_today/breached) on both applicant and staff application detail pages
- Frontend extraction status: badges for pending/running/completed/failed/unsupported with spinner animation

### Checks
- Backend: 538 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean (warnings only), vite build success

### Known limitations
- No Indian holiday calendar — business days exclude weekends only
- No SLA breach notifications (deferred)
- No extraction retry queue (manual retry via button)
- No OCR for image-based documents (existing limitation)
- Background extraction runs in-process; server restart mid-extraction leaves document in "running" state

### Next phase
- Phase 6: Orchestration / Readiness (see below)

## 27. Phase 7 implementation status (2026-09-16)

### Created
- `backend/app/regulatory/__init__.py` — regulatory module
- `backend/app/regulatory/models.py` — SourceRecord, SourceChunk, Citation, RegulatoryExplanation, ExplanationRequest, EvidenceState
- `backend/app/regulatory/ingestion.py` — source ingestion (seed 32 sources, chunk generation)
- `backend/app/regulatory/retrieval.py` — full-text search via PostgreSQL tsvector/tsquery with ts_rank_cd
- `backend/app/regulatory/explanation.py` — template-based source-grounded explanations (no LLM)
- `backend/app/seed/sources.py` — 32 verified Gujarat regulatory sources (S01-S32) from workbook
- `backend/app/api/regulatory.py` — 6 REST endpoints (list sources, get source, seed, explain, explain approval, orchestration citations)
- `backend/tests/test_regulatory_ingestion.py` — 22 ingestion + seed data tests
- `backend/tests/test_regulatory_retrieval.py` — 19 retrieval tests
- `backend/tests/test_regulatory_explanation.py` — 18 explanation tests
- `backend/tests/test_regulatory_api.py` — 14 API endpoint tests
- `supabase/migrations/005_rag_sources.sql` — source metadata columns, source_chunks table, GIN indexes
- `frontend/src/pages/shared/RegulatoryAssistant.tsx` — search + citation display component

### Implemented
- **32 regulatory sources** seeded from frozen workbook (S01-S32), all Official, Gujarat (IN-GJ)
- **Source chunks** with PostgreSQL tsvector full-text search and GIN indexes
- **Full-text retrieval** using `text_search` with `ts_rank_cd` ranking
- **Citation generation** — deduplicated by source_id, ranked by relevance
- **Template-based explanations** — deterministic, no LLM required
- **Evidence states**: sufficient, insufficient, partial
- **6 API endpoints**: GET /sources, GET /sources/{id}, GET /sources/status, POST /sources/seed, POST /regulatory/explain, GET /regulatory/approval/{id}/explanation, GET /regulatory/orchestration/{id}/citations
- **Frontend**: RegulatoryAssistant component with search input, explanation display, citation cards with source links
- **RAG boundary**: RAG never calculates or overrides applicability; it only explains existing deterministic results

### Architecture
```
Deterministic rules decide → RAG retrieves → Templates explain → Human decides
```

### Checks
- Backend: 625 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean (pre-existing warnings only), vite build success

### Known limitations
- No LLM integration (template-based explanations only)
- No vector embeddings (PostgreSQL tsvector only)
- No source content fetching/crawling (seed data only)
- No OCR for image-based documents (existing limitation)
- Source chunks are generated from metadata, not full document text
- No source freshness checking or re-crawling

### Next phase
- Phase 8: Government Support & Incentive Intelligence

## 28. Phase 8 implementation status (2026-09-16)

### Created
- `backend/app/incentives/__init__.py` — incentives module
- `backend/app/incentives/models.py` — SupportScheme, SchemeCategory, RelevanceState, RequiredInfo, SchemeBenefit, SchemeRelevance, ProjectIncentiveAssessment, IncentiveAssessmentRequest
- `backend/app/incentives/engine.py` — `assess_scheme()`, `assess_all_schemes()` deterministic incentive relevance engine (reuses `app.rules.applicability._evaluate_node`)
- `backend/app/seed/incentives.py` — 6 verified Gujarat incentive schemes from GIP 2020 (INC-MSME-CAP, INC-MSME-INT, INC-LARGE-CAP, INC-ELEC-DUTY, INC-POWER-CHG, INC-QUALITY)
- `backend/app/api/incentives.py` — 3 REST endpoints (list, get, assess)
- `backend/tests/test_incentives.py` — 24 engine + seed data tests
- `backend/tests/test_incentives_api.py` — 13 API endpoint + auth tests
- `frontend/src/pages/shared/IncentiveSchemes.tsx` — compact incentive assessment component

### Implemented
- **6 verified Gujarat incentive schemes** from GIP 2020 (Government of Gujarat, August 2020):
  - MSME Capital Subsidy (25%/20%/10% by taluka category)
  - MSME Interest Subsidy (7%/6%/5% by taluka category)
  - Capital Subsidy to Large Industries and Thrust Sector (12%/10%/6%/4%)
  - Electricity Duty Exemption (5 years)
  - Power Connection Charges Subsidy (35% up to INR 5 lakh)
  - Quality Certification Assistance (50% fee reimbursement)
- **Deterministic eligibility engine** reuses existing `_evaluate_node` from applicability engine
- **Relevance states**: POTENTIALLY_RELEVANT, NOT_RELEVANT, CONDITIONAL, INSUFFICIENT_DATA
- **Source traceability**: every scheme links to S33 (GIP 2020 official policy PDF)
- **3 API endpoints**: GET /incentives, GET /incentives/{id}, POST /incentives/assess
- **Frontend**: IncentiveSchemes component on both applicant and staff application detail pages
- **Assessment independence**: incentive assessment never modifies approval applicability outcomes
- Source S33 added to regulatory sources (33 total)

### Architecture
```
Deterministic rules decide → Incentive engine assesses → Source cites → Human decides
```

### Checks
- Backend: 662 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean (pre-existing warnings only), vite build success

### Known limitations
- Scheme eligibility conditions are based on entity_type matching only (GIP 2020 doesn't provide project-level eligibility fields beyond entity type)
- No monetary benefit calculation (amounts depend on term loan/FCI which are not in project facts)
- Taluka category and sector type are not in project facts — these produce INSUFFICIENT_DATA
- Only GIP 2020 schemes seeded; no sector-specific or central government schemes
- No persistent assessment storage (computed on demand)
- Scheme eligibility conditions could be enriched with additional project facts in future

### Next phase
- Phase 9: End-to-end integration

## 29. Phase 9 implementation status (2026-09-16)

### Changes
- **Orchestration endpoint wired**: `GET /applications/{id}/orchestration` now fetches extraction results, validation results, consistency results, and SLA state from the database instead of passing empty stubs
- **Obtained approvals computed**: sibling applications in terminal/approved status within the same project are counted as obtained for dependency satisfaction
- **Frontend shared components extracted**: `SLACard`, `DocumentChecklist`, `ConsistencyPanel`, `OrchestrationPanel` extracted from duplicated code (~350 lines eliminated from staff/applicant detail pages)
- **Consistency API normalized**: path parameter renamed from `app_id` to `application_id`, `datetime.utcnow()` replaced with `datetime.now(UTC)`, DI-injected repositories instead of direct `get_supabase()` calls
- **Permission mismatches fixed**: extraction/consistency POST endpoints now require `APPLICATION_CREATE` instead of view-only permissions
- **Dead code removed**: duplicate S32 source (same URL as S10), unused `APPROVAL_TO_DOCS` dict and `parse_used_for()` function from seed/documents.py, duplicate delete call in extraction API
- **Frontend polish**: SLA/orchestration re-fetched after workflow actions, consistency check errors surfaced to user
- **ConsistencyRepository dependency**: added `get_consistency_repository` to `app/api/deps.py`

### Checks
- Backend: 665 passed, 4 skipped, 0 failed, ruff clean
- Frontend: tsc clean, oxlint clean (pre-existing warnings only), vite build success

### Known limitations
- Orchestration endpoint still evaluates all 18 approvals via seed data (not filtered to the application's approval type)
- No real-time updates (WebSocket/SSE) for status changes
- SLA uses business days only (no Indian holiday calendar)
- Background extraction runs in-process; server restart mid-extraction leaves document in "running" state

### Next phase
- Phase 10: TBD

## 30. G0-R5 evidence-boundary orchestration integration (2026-09-26)

### Wired
- `GET /applications/{id}/orchestration` attaches verified G0-R5 evidence gaps per assessed approval via `get_gaps_for_approval()` (hint mapping only) and passes them as `evidence_gaps_by_approval` to `orchestrate_application_full()`.
- Relevant PARTIAL / NOT_ESTABLISHED / CONFLICTING gaps surface as `INSUFFICIENT_DATA` with `BlockerDetail` blockers carrying structured traceability (`evidence_id`, `evidence_status`, `unresolved_question`; `source_ref` = source reference, `evidence` = verified scope, `action_required` = human-review next step).
- `NOT_APPLICABLE` is preserved when gaps exist; approvals without hints assess exactly as before. No applicability rules are created from gaps; the ApprovalRule/ConditionNode engine remains authoritative. No migrations, no new dependencies, no frontend changes.

### Checks
- Backend: 708 passed, 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean — includes 9 new `test_evidence_orchestration_integration.py` tests (endpoint + structured-field tests watched fail before implementation).
- Frontend: OrchestrationPanel renders blocker description + action_required plus structured evidence fields (`evidence_id`, `evidence_status`, `unresolved_question`) for gap blockers in both applicant and staff views; TS `BlockerDetail` carries them as optional (additive, backward compatible); no frontend checks required beyond tsc/oxlint/build.

### Known limitations
- EODB-2026 / VGIP-2026 gaps map to no approval and never surface per-approval (hint-only by design).
- Gap surfacing is computed on demand from seed hints; no persistence.

## 31. Approval catalog seeding + Dahej scenario verification (2026-09-26)

### Added
- `ApprovalsRepository.get_by_code()` — lookup by canonical workbook code (migration 008 column; UUIDs stay persistence ids).
- `POST /approvals/seed` — seeds canonical A01–A18 from the single `load_approval_catalog()` source (no catalog duplication). Idempotent: skips matching codes; same-code name/authority mismatch fails loudly (409, human mapping required) instead of re-identifying rows. Mirrors `POST /sources/seed` auth (any authenticated user).

### Verified on a scratch database (ephemeral local Postgres 18, removed afterwards)
- Migrations 001–008 apply cleanly in order to a fresh database (only the Supabase-platform `auth.users` stub was needed; the supported Supabase mechanism provides it natively).
- 18 catalog rows insert exactly once (A01–A18); duplicate code rejected by `idx_approvals_code_unique`; NULL-code unresolved rows coexist; `applications.approval_code` present.
- Live-Supabase/PostgREST verification remains unavailable here (no docker stack, remote DNS blocked); the app-level seed path is covered by mocked-repository endpoint tests, consistent with all other API tests.

### Dahej end-to-end (frozen `load_scenario()` facts, unchanged)
- All 18 approvals assessed through applicability → evidence → dependencies → documents → orchestration: 17× applies, A18 does_not_apply.
- Statuses: A05/A08/A11/A16/A17 READY; A04/A13 BLOCKED_BY_DOCUMENTS; A01/A02/A03/A06/A07/A09/A10/A12/A14/A15 INSUFFICIENT_DATA (relevant gaps only); A18 NOT_APPLICABLE (GW gaps attached but inert — no "no NOC" conclusion fabricated); overall BLOCKED_BY_DOCUMENTS.

### Checks
- Backend: 725 passed (708 prior + 8 catalog-seed + 9 Dahej), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. Seed-endpoint tests watched fail (404/missing method) before implementation.
- Frontend unchanged (no contract changes to consumed shapes; new endpoint unconsumed); no frontend checks required.

## 32. Deployment-readiness validation (2026-09-26)

### Added
- `Settings.cors_allow_origins` (`CORS_ALLOW_ORIGINS`, default `http://localhost:5173,http://localhost:3000`) + `parse_cors_origins()`; `main.py` builds the CORSMiddleware allowlist from it. Explicit origins only — never a wildcard with credentials. 5 new `test_config.py` tests (TDD: watched fail on missing helper first).

### Verified
- Env contract: every `Settings` field is documented (`README` env table now includes `AUTH_JWT_ALGORITHM`, `SUPABASE_STORAGE_BUCKET`, `CORS_ALLOW_ORIGINS`); `.env` files ignored/untracked, examples contain placeholders only; secret grep clean.
- CORS live: allowed-origin preflight 200 with origin echo + credentials; disallowed origin 400 with no allow-origin header; unauthenticated orchestration 401.
- Migrations: additive-only (no DROP/DELETE/GRANT), FKs coherent (only platform FK is `projects.applicant_id → auth.users`), no duplicate enum creation, no RLS/policies/storage objects by design (backend-only access; do not expose PostgREST to browsers without adding RLS).
- Auth coverage: all 46 non-health/root routes carry auth dependencies; seed endpoints require authentication per existing convention; no new roles/permissions.
- Smoke (localhost-only, nothing external touched): uvicorn boots, `/health` 200, `/openapi.json` 45 paths incl. `/approvals/seed`, production `dist/` serves 200 via `vite preview`.
- Demo path needs no new mechanism: catalog/sources seeds + API-created project/facts/applications reproduce the verified Dahej assessment deterministically.

### Checks
- Backend: 730 passed (725 prior + 5 config), 4 skipped, 0 failed, ruff clean. Frontend: tsc 0 errors, oxlint 4 pre-existing warnings only, vite build success.

### Known limitations
- No staging/production target available here: real Supabase Auth login, DB-backed writes, cross-origin browser flow, and PostgREST/RLS behavior are externally unverified (locally/scratch-verified only).
- `debug` setting exists but is unwired (FastAPI defaults apply); placeholder defaults fail closed at request time, not startup — misconfiguration surfaces as auth/DB errors, not a fast startup failure.

## 33. Phase 1 loader scaffold — jurisdiction-aware regulatory boundary (2026-09-26)

### Added
- `backend/app/seed/pack.py` — `RegulatoryPack` dataclass (rules, authorities, dependencies, document requirements, consistency rules, incentive schemes, sources, evidence gaps + surfacing hints, portal catalog; reuses engine contract types, no second domain model) + `load_regulatory_pack(jurisdiction)`.
- Jurisdiction validation: `IN-GJ` → existing Gujarat data (unchanged); `IN-MH` → explicitly empty placeholder (v5 CSVs NOT loaded); anything else → `UnknownJurisdictionError` (no silent default).
- `DEFAULT_JURISDICTION = "IN-GJ"` in `pack.py` is the single cutover point; production behavior unchanged.
- Rerouted API-layer seed consumption through the pack: `api/orchestration.py` (`_load_baseline_inputs` now returns `pack` + `jurisdiction`), `api/handoffs.py` (portal entries via pack), `api/regulatory.py` (explain rules via pack), `api/applications.py` (doc seeding via pack), `api/consistency.py` (rules via pack), `api/incentives.py` (schemes via pack).
- `backend/tests/test_regulatory_pack.py` — 18 tests (GJ parity, MH-empty, invalid-jurisdiction, orchestration/what-if/impact/handoff input equivalence, no-direct-seed-imports in orchestration). Two `test_regulatory_api.py` mock targets updated to the pack boundary.

### Intentionally untouched
- Engines (`applicability`, `dependency_engine`, `orchestration/service`, `whatif`, `impact`, `handoff/service`), auth, migrations 001–009, frontend, GJ seed contents.
- Service-internal seed uses remain: `handoff/service.py::prepare_initiation` (portal lookup) and `regulatory/impact.py` (evidence registry + source index). These are quarantined for the MH-population phase, not this scaffold.

### Checks
- Backend: 852 passed (834 prior + 18 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean.

## 34. Phase 2 — MH fact ontology + literal/temporal semantics (2026-09-26)

### Added
- `backend/app/rules/facts.py` — 128 code-defined IN-MH facts (v5 facts.csv transcription; F-BLD-02 excluded as DNI), `FactSpec` (type/unit/allowed/unknown/derived/group/description/used_in), `validate_fact_value()` (`None` always valid; explicit `FactValidationError` codes), jurisdiction-mismatch detection both directions. Mechanism only — no v5 rules encoded, IN-MH pack still empty.
- `LiteralNode("unknown"|"not_applicable")` in the ConditionNode union (`rules/models.py`): unknown→None (never FALSE); NOT_APPLICABLE sentinel propagates explicitly (AND: FALSE>None>NA; OR: TRUE>None>NA; NOT never negates NA); rule-level NA→DOES_NOT_APPLY with explicit reason, UNKNOWN/missing never reach DOES_NOT_APPLY.
- Effective window on `ApprovalRule` (`effective_from`/`effective_to`, optional): `evaluate_rule(..., evaluation_date=...)` pre-check (before→not-in-force, after→no-longer-in-force DOES_NOT_APPLY; open ends open; `None` date preserves behavior).
- What-If registry path: `apply_fact_overrides(..., jurisdiction=)` + `run_whatif_assessment(..., jurisdiction=)`; endpoint threads `inputs["jurisdiction"]`. IN-GJ path byte-identical.

### Checks
- Backend: 920 passed (852 prior + 68 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. No migration. No frontend changes.

## 35. Phase 3 — MH safe-rule batch 1 (2026-09-26)

### Added
- `backend/app/seed/mh/approvals.py` — 19 directly encodable IMPLEMENTATION_SAFE rules (R-002/007/009/011/012/018/026/028/030/035/043/044/046/056/067/070/089/093/094) with v5 source refs, EXACT effective dates (YEAR_ONLY windows omitted, never invented), v5 authority strings; classification sets (76/26/3 + UNKNOWN R-015/052/074) with fail-closed `_encode()` guard; 9 deferrals with reasons.
- `load_regulatory_pack("IN-MH")` now returns the batch-1 pack (rules + authorities; deps/docs/sources/gaps/portals still empty). Default stays IN-GJ.
- `backend/tests/test_mh_pack.py` — 34 tests (pack contract, per-rule APPLIES/DOES_NOT_APPLY/missing/boundary/window cases from v5 semantics, R-074/R-015/R-052 absence, GJ↔MH contamination, MH orchestration end-to-end).

### Checks
- Backend: 954 passed (920 prior + 34 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. No migration. No frontend changes.

## 36. Phase 4 — MH pack dimensions for batch-1 (2026-09-26)

### Added
- `backend/app/seed/mh/dependencies.py` — DEP-009 split into 2 explicit edges (APR-010←APR-008/APR-009, HOWM r.6); all other 33 register rows triaged in `MH_DEP_DEFERRED` (22 out-of-scope, 8 non-approval endpoints, DEP-002 UNKNOWN, DEP-013 ROC, DEP-020 facilitation).
- `backend/app/seed/mh/documents.py` — DOC-001/002/003→APR-010, DOC-008→APR-026 (required, verified URLs from sources.csv); 8 deferred with reasons (DOC-012 ROC surfaced as evidence instead).
- `backend/app/seed/mh/evidence.py` — 3 advisory records (UR-06→APR-001, UR-11→APR-055, DOC-012→APR-043) + hints; evaluated-not-surfaced conflicts documented (CON-004/009/011/014/019, UR-09/15).
- `load_regulatory_pack("IN-MH")` now serves rules + authorities + deps + docs + evidence. Default stays IN-GJ.
- `backend/tests/test_mh_pack_dimensions.py` — 21 tests (dimensions, graph integrity, scenarios A–F, GJ/MH isolation).

### Checks
- Backend: 975 passed (954 prior + 21 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. No migration. No frontend changes.

## 37. Phase 5 — MH source corpus + portal catalog (2026-09-26)

### Added
- `backend/app/seed/mh/sources.py` — 14/188 v5 sources referenced by batch-1 rules/deps/docs/evidence (tiers/source-types verbatim, labeled PROVES/DOES_NOT_PROVE in notes); 174 deferred.
- `backend/app/seed/mh/portals.py` — 14 batch-1 portal catalog entries (portal/reference only; PARIVESH, ecMPCB, PESO, CGWA as portals; Labour RTS, mahaboiler, MIDC pages/GIS as references; no MAITRI; `is_portal_cta()` safety helper refusing missing/non-https URLs).
- `load_regulatory_pack("IN-MH")` now serves rules + authorities + deps + docs + evidence + sources + portals. Default stays IN-GJ.
- `backend/tests/test_mh_sources_portals.py` — 28 tests (corpus, resolution, portals, POR-003-style safety, e2e chains, isolation, decisions-unchanged).
- Caught by this phase: Phase-4 DOC-001/002/003 source URLs were truncated — corrected to exact SRC-013 registry URLs; SRC-092 (Petroleum Act, cited by R-030) was missing from the corpus — added.

### Checks
- Backend: 1003 passed (975 prior + 28 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. No migration. No frontend changes.

## 38. Phase 6 — MH consistency (empty by evidence) + SLA display data (2026-09-26)

### Added
- `backend/app/seed/mh/consistency.py` — explicit STOP outcome: register-wide search of all 73 v5 CSVs found zero cross-document consistency records for batch-1 docs, so nothing is transcribed (loader returns []).
- `backend/app/workflow/sla.py` — `SlaMetadata` frozen dataclass (display-only; target vs outer fields never merged; verbatim values).
- `backend/app/seed/mh/slas.py` — 10 SLA rows referenced by batch-1 timelines (SLA-004/008/011/012/013/031/032/040/045/047; SLA-009/029/039 corrected to deferred — their approvals have no batch-1 rules); UNKNOWN/"-"/NOT_STATED preserved; no conversions, no computation.
- `backend/app/seed/pack.py` — `RegulatoryPack.sla_records` (default []); IN-MH serves SLA + explicit-empty consistency.
- `backend/app/seed/mh/sources.py` — +SRC-031/117/136 (SLA provenance, transcribed exactly); corpus now 17/188.
- `backend/tests/test_mh_consistency_sla.py` — 22 tests (empty-consistency, verbatim SLA, source resolution, dual-display incl. SLA-040/047 coexistence, 6-scenario decision regression, isolation).

### Checks
- Backend: 1025 passed (1003 prior + 22 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. No migration. No frontend changes.

## 39. Phase 7 — MH end-to-end FastAPI verification (2026-09-26)

### Added
- `get_active_jurisdiction()` dependency (`api/deps.py`): returns DEFAULT_JURISDICTION in production (no query param/header/body selector); tests override it per-app for IN-MH. Threaded through orchestration (GET + what-if), handoffs (list/initiate), regulatory (rehearse + 2 explain), application creation (doc seeding).
- `prepare_initiation(..., portal_entry=None)` (`handoff/service.py`): optional pack-resolved portal entry; None preserves the legacy GJ lookup (GJ behavior identical).
- `RehearsalInputs` gains optional `known_source_ids` / `evidence_registry` / `evidence_hints` (None = legacy GJ registries; GJ behavior identical).
- `backend/tests/test_mh_api_e2e.py` — 27 tests (MH orchestration A–F, what-if incl. 422s + non-persistence, rehearse incl. 403/statelessness, handoff incl. verify/409/422/403 + events, doc seeding, 404/409/422/401, GJ baseline, isolation scans, invalid-jurisdiction rejection, default regression).

### Checks
- Backend: 1052 passed (1025 prior + 27 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. No migration. No frontend changes. Default stays IN-GJ.

## 40. Phase 8 — Cutover readiness GATE A outcome: BLOCKED (2026-09-26)

Gate A (identity/data-contract safety) FAILS; the default was NOT flipped:

- N-2: zero VERIFIED_MATCH mappings exist (no repository evidence links any A01–A18 identity to any APR/CMP identity). 8 AMBIGUOUS (same central statute, unproven), 10 NO_VERIFIED_MATCH (state-specific institutions). Nothing may be used as a deterministic migration mapping.
- Persisted-data safety: `projects`/`applications`/`project_facts`/`documents`/`workflow_events`/`approval_handoffs` carry NO jurisdiction or pack-version marker (`project_facts.jurisdictions` is applicant-supplied entity data, unread by the decision path). Flipping the default would 422 all GJ-coded applications in orchestration, orphan D0X document keys against DOC-xxx requirements, void GJ handoff portal lookups, and silently seed zero requirements for GJ-coded creates.
- Safe coexistence requires a jurisdiction/pack-version column = a database migration, which is out of scope for the cutover phase itself.
- Added: `backend/tests/test_mh_readiness_checklist.py` (10 tests, explicit IN-MH context; technical readiness green).
- Frontend audit (read-only): `OrchestrationPanel` compares backend lowercase statuses against UPPERCASE literals (badges/filtering broken — pre-existing, display-only; handoff actions are server-driven and unaffected); `WhatIfPanel` field list is GJ-only; incentives-empty and SLA-metadata have no MH UI yet.
- STAKEHOLDER SIGN-OFF REQUIRED: N-2 mapping, demo scenario, portal wording, held-incentives display, legacy-record interpretation.

### Checks
- Backend: 1062 passed (1052 prior + 10 new), 4 skipped (pre-existing DB-dependent), 0 failed, ruff clean. No migration. No frontend changes. Default stays IN-GJ.

## 41. Phase 9 — Persisted-jurisdiction design (DESIGN ONLY, 2026-09-26)

Full design: `docs/architecture/persisted-jurisdiction-design.md` (20 sections).
Summary: per-application (`jurisdiction`, `pack_version`) is authoritative;
`projects.jurisdiction` is the creation guard; facts/documents/handoffs/events
inherit (no new columns there); legacy backfills to (`IN-GJ`,
`gj-legacy-unversioned`); new records derive server-side from the default;
approval_code validated per-pack at creation (A04-under-MH → 422); rollback
is a default flip-back with no data rewrite. No migration, code, default, or
N-2 change in this phase. STAKEHOLDER SIGN-OFF REQUIRED (N-2, pack-version
strings, project-column acceptability, backfill window).

## 42. Phase 10 — Persisted-jurisdiction implementation (2026-09-26)

### Added
- `supabase/migrations/010_persisted_jurisdiction.sql` — nullable
  `jurisdiction`/`pack_version` on `projects` + `applications`,
  deterministic IN-GJ backfill, validating DO block, NOT NULL, value
  CHECKs, indexes. Additive only; A-codes untouched. (Written and
  review-verified; live-DB execution pending staging — the sandbox
  postgres server cannot start here.)
- `seed/pack.py` — `PACK_RELEASES`, `DEFAULT_PACK_VERSIONS`,
  `UnknownPackError`, `resolve_persisted_pack()` (exact pairs only,
  never the default, never inferred).
- Read paths resolve persisted identity: orchestration baseline
  (422 on unscoped/unknown), consistency check, handoff list/initiate
  (pack portal entries), rehearsal (+pack registries), doc seeding.
- Creation paths: projects stamp server default (+version);
  applications inherit project identity + per-pack approval_code
  validation (A04-under-MH / APR-under-GJ → 422); facts upsert gains
  optional `facts_json` validated per project vocabulary (MH strict,
  GJ legacy-permissive); client-supplied jurisdiction ignored.
- `backend/tests/test_persisted_jurisdiction.py` — TEST-01…17 +
  extras (override-ignored, app-authoritative, no-translation,
  flip-simulation, unscoped-422).

### Checks
- Backend: 1084 passed (1062 prior + 21 new + 1 e2e addition), 4 skipped
  (pre-existing DB-dependent), 0 failed, ruff clean. No default flip
  (IN-GJ). N-2 untouched. No A↔APR translation. No frontend changes.

## 43. Phase 11 — Staging migration + flip rehearsal (2026-09-28)

### Staging (PostgreSQL 18.3, disposable `sih_staging_11`, dropped after)
- Migrations 001–010 applied in order via psql (001 needed an
  `auth.users` stub, the only Supabase-platform object; supported
  natively in real Supabase). Migration 010 executed cleanly.
- Schema verified: 4 columns NOT NULL, 2 CHECKs, 2 indexes; 5
  inheriting tables column-free; all FKs intact (incl. no-cascade
  projects→applications, cascade applications→children).
- Backfill gates: 4× zero-NULL; sole pair IN-GJ/gj-legacy-unversioned.
- Legacy preservation: A04, facts, D05 doc, workflow event, handoff
  row byte-identical apart from added identity. CHECK rejects IN-XX.
  App-level cascade verified (children removed, project+facts kept).
- App layer: TEST-01…17 + flip/flip-back/CASE-A rehearsals green
  (mocked transport; Supabase PostgREST path untested — same standing
  exclusion as the 4 pre-existing DB skips).

### Checks
- Backend: 1088 passed (1084 prior + 4 new), 4 skipped (pre-existing
  DB-dependent), 0 failed, ruff clean. Production default NOT
  flipped (IN-GJ).

## 44. Phase 12 — Production-flip authorization gate: NOT AUTHORIZED (2026-09-28)

N-2: zero verified A↔APR mappings (repo-wide search: both namespaces
co-occur in 2 test files + 1 design doc, zero same-line linkages).
Frontend: enum-casing mismatch, GJ-only WhatIf fields + facts form,
dead ApplicabilityResult type, held-dimension wording pending.
Supabase: migrations-only repo footprint — no linked hosted staging
project available (NOT VERIFIED). DEFAULT_JURISDICTION stays IN-GJ.

## 45. Gujarat coherence restoration (scope-locked task)

- Migration 010 re-verified on scratch PostgreSQL 18 (001→010 clean;
  backfill/columns/constraints/indexes proven; legacy rows keep
  identity). No migration change was needed.
- Frontend `OrchestrationStatus` + comparisons aligned to backend
  lowercase wire values; dead `ApplicabilityResult` type + stale
  `ObligationApplicabilityResponse` removed. ValidationOutcome /
  ConsistencyOutcome uppercase comparisons verified correct as-is.
- Dahej canonical result re-verified byte-exact (5 READY / 2
  BLOCKED_BY_DOCUMENTS / 10 INSUFFICIENT_DATA / A18 NOT_APPLICABLE).
- Backend 1088/4 green, ruff clean; tsc 0 errors; oxlint pre-existing
  warnings only; vite build success. No hosted deployment performed.

## 46. Local PostgreSQL development database (infra migration)

- Supabase PostgREST/Storage client replaced with direct PostgreSQL
  (psycopg 3 + pool, `app/db/postgres.py`) and a local filesystem
  storage adapter (`app/storage/`, `data/uploads/`, git-ignored).
- All repositories rewritten to parameterized SQL with identical
  interfaces/shapes; full-text search kept (tsvector + GIN,
  `ts_rank_cd`); auth unchanged (standalone PyJWT + RBAC/ownership).
- Migrations 011 (`approvals.workflow_definition`) and 012
  (`applications.applicant_id`) backfill application-read columns the
  code already required (demonstrated UndefinedColumn failures).
- Local DB `gaia_dev`: migrations 001–012 applied; catalog A01–A18
  seeded once with uniqueness enforced; Dahej mapping unchanged.
- Procedure: `docs/local-postgres.md` + `scripts/verify_local_db.py`
  (14 checks).

## 47. MH fact-ontology audit + UNKNOWN fail-closed fix (2026-09-28)

- Ontology: `app/rules/facts.py` carries 128 ACTIVE IN-MH facts =
  129 v5 `facts.csv` rows minus F-BLD-02 (DEPRECATED, explicitly
  excluded). CSV <-> registry verified exact, zero dupes, zero drift.
  Batch-1 rules consume 29 facts; the 105-row v5 register mentions 98;
  all 129 CSV facts are referenced somewhere in the 73-file v5 pack
  (rules/incentives/decision-paths/changelogs).
- Fix: `_evaluate_leaf()` treated a supplied `"UNKNOWN"` token (which
  validation accepts) as a decidable value -> FALSE ->
  DOES_NOT_APPLY, contradicting the registry contract and failing OPEN
  on trigger rules (R-018/046/056/067/089/093/094). Now None/`"UNKNOWN"`
  evaluate to INSUFFICIENT_DATA and count as missing inputs, both
  jurisdictions. No GJ behavior change (full suite green).
- Leakage kept quarantined: incentives API serves GJ GIP-2020 schemes via
  hardcoded DEFAULT_JURISDICTION; `/sources*` + `POST /regulatory/explain`
  are GJ-backed with no jurisdiction threading; WhatIfPanel + project
  facts form are GJ-only; extraction VALIDATION_RULES cite GJ
  authorities in source_refs. Persisted-pack paths (orchestration,
  what-if, handoffs, rehearse, consistency, doc seeding, fact upsert)
  are jurisdiction-clean.
- Checks: 1112 passed (1106 prior + 6 new
  `test_unknown_token_fail_closed.py`), ruff clean. No migration.
  Next: 76-rule MH encoding only after stakeholder review of this
  audit (derived-fact computation, WAT-09/GW-01 + HAZ-01/HAZ-04
  overlap, incentive-pack population, frontend MH vocabulary).

## 48. IN-MH derived facts F-PRC-03 + F-INC-01 (2026-09-28)

- New `app/rules/derivations.py` (IN-MH only; pure, no I/O):
  `derive_msme_class()` implements R-057 bands verbatim (MICRO
  inv<=2.5 AND to<=10; SMALL <=25/100; MEDIUM <=125/500; else LARGE;
  either input missing/UNKNOWN/invalid -> UNKNOWN). `derive_mah_status()`
  implements R-091 join semantics over supplied F-HAZ-01 + F-HAZ-02
  only (exact chemical-string match; TRUE dominates; FALSE iff all
  resolved and none >= col 3; else UNKNOWN; empty inventory -> FALSE).
  `derive_mh_facts()` fills only absent keys, never overrides, never
  mutates; IN-GJ raises JURISDICTION_MISMATCH.
- BLOCKED by insufficient evidence (fail closed, never produced):
  F-INC-03 (INC-001 states only "sector falls in thrust sector #6",
  no input mapping/member list) and F-INC-04 (R-058
  DO_NOT_IMPLEMENT_YET, "Annexure not digitised in this pack", no
  taluka->basket table in-repo).
- NOT wired into orchestration/what-if/API (separate decision; R-002
  + R-043 still fail closed on missing derived inputs as before).
  No FactSpec changes. No GJ changes.
- Checks: 1151 passed (1112 prior + 39 new
  `test_mh_derivations.py`), ruff clean. No migration.

## 49. Derivation wiring into the IN-MH decision path (2026-09-28)

- Single point: `_load_baseline_inputs` resolves persisted facts, then
  `apply_derived_facts()` (`orchestration/facts.py`, IN-MH only;
  `derive_mh_facts` remains the sole implementation) merges F-INC-01 /
  F-PRC-03 and records provenance. `inputs["facts"]` merged,
  `inputs["fact_provenance"]` carried; IN-GJ passes through
  byte-identical (empty provenance).
- Shared by all four consumers with no second path: GET orchestration,
  What-If (`run_whatif_assessment` strips provenance keys from base
  before overrides, then re-derives the alt branch; direct
  derived-key overrides keep precedence), handoffs
  (`_run_orchestration`), rehearse (consumes merged `inputs["facts"]`).
- Provenance: `FactProvenance` (fact_id, derived, derivation fn,
  source_facts, value) on `ApplicationOrchestration.fact_provenance`
  (default {}); unlisted facts are supplied. No LLM, no persistence
  (derived-at-evaluation-time), no frontend change (additive field).
- Observed: R-002 scenario APR-001 applicability applies (F-PRC-03=False
  derived) while status stays insufficient_data (UR-06 gap blocker);
  R-043 scenario APR-043 applies (F-INC-01=MICRO derived) while status
  stays insufficient_data (DOC-012 gap blocker). F-INC-03/04 never
  produced. No batch-2 rules. Global default untouched (IN-GJ).
- Checks: 1169 passed (1151 prior + 18 new
  `test_mh_derivation_wiring.py`), ruff clean. No migration.

## 50. MH batch-2 safe rules R-073/R-086/R-087 (2026-09-28)

- Encoded (`seed/mh/approvals.py`, pack now 22 rules): R-073
  BOE_REQUIRED := F-BLR-06 > 1000 m2 (strict >, ET-096; operating
  condition, SRC-085, eff. 2025-09-23); R-086 BOILER_REGISTRATION :=
  R-028 tree restated exactly AND F-BLR-07 == NOT_REGISTERED
  (registration, SRC-034 s.12, eff. 2025-05-01; mirror test pins
  R-028 agreement); R-087 BOILER_EXISTING :=
  F-BLR-07 == REGISTERED_UNDER_1923_ACT -> deemed registered
  (transitional, SRC-034 s.45(2), eff. 2025-05-01). All APR-023/AUT-007
  (existing identity); no new deps/docs/SLAs (s.9 erection inspection
  is an event, not an approval edge).
- Source corpus 17 -> 18/188: SRC-085 transcribed verbatim
  (BOE Rules 2025, T1); every rule source_ref resolves (pinned).
- Deferred with reasons (fail-closed via _encode): R-075 (no EC-date
  fact + no DATE arithmetic), R-088 (no event facts), R-100/101/102
  (no licence-held input fact, SSC-01..03), R-103 (no new-licence /
  application-date facts; gas-only would over-apply vs ET-v5-12),
  R-104 (no licence/purpose/filling-plant facts). R-100..104 have no
  encodable effective_to handling: their date dimension has no fact,
  so no boundary behavior was added or assumed.
- Checks: 1204 passed (1169 prior + 35 new
  `test_mh_pack_batch2.py`), ruff clean. No migration. No default
  flip. Next: location cluster (R-077/096/091/060/061/083/084/085)
  as its own task.

## 51. MH Location Cluster R-077/R-096/R-083/R-084 & Gated Deferrals (2026-09-28)

- Encoded (`seed/mh/approvals.py`, pack now 26 rules):
  - R-077: CGWA NOC for groundwater abstraction in over-exploited assessment units
    (APR-043, AUT-013, SRC-052, eff. 2020-09-24).
  - R-083: CRZ Notification 2019 applicability (LOC-CRZ, MCZMA / MoEFCC,
    SRC-112, eff. 2019-01-18).
  - R-084: Forest land involved under Van Adhiniyam 1980 / Rules 2023
    (LOC-FOREST, MoEFCC / Regional Office / State Forest Dept, SRC-113, eff. 2023-12-01).
  - R-096: Hazardous waste authorisation Schedule II characteristic test
    (APR-010, AUT-003, SRC-120, eff. 2016-04-04).
- Sources expanded from 18 to 22:
  - SRC-112 (CRZ Notification 2019, T1)
  - SRC-113 (Van Rules 2023, T1)
  - SRC-114 (Supreme Court order 04-12-2006 NBWL note, T2)
  - SRC-120 (HOWM Rules 2016 Schedule II copy, T2)
  All source refs resolve.
- Gated Deferrals (documented reasons in `MH_DEFERRED_RULES`):
  - R-060: MSIHC general duty under rule 4(1) requires existential quantifier (EXISTS)
    unsupported by condition primitives.
  - R-061: MSIHC 500m aggregation requires spatial multi-site computation unsupported by engine.
  - R-085: Standing Committee NBWL recommendation requires EC_REQUIRED precondition which
    is NOT represented in the fact registry and cannot be inferred.
  - R-091: Partial implementation via `derive_mah_status()` in `rules/derivations.py`
    (M3-M7-M9); direct ApprovalRule deferred due to unselected M2 identity resolution
    and unconfirmed CON-021 thresholds. Fail closed when unresolved.
- Checks: 1263 passed (1204 baseline + 59 new tests in `test_mh_pack_location_cluster.py`),
  ruff clean. No migration. No default flip (IN-GJ remains default).

## 52. MH Planning & Fire Cluster Audit & Gated Deferrals (2026-09-28)

- Cluster Audited: R-041, R-078, R-079, R-080, R-082 across 20 evidence dimensions.
- Decision: All 5 rules are DEFERRED (fail-closed against premature/invalid activation):
  - R-041 (Building permission non-MIDC): fact `construction` is absent from the
    fact registry; authority routing `R-080` and DCR regime routing `R-082` require
    cross-rule composition unsupported by `ConditionNode`; dual approval target
    `APR-038;APR-041` conflates pre-construction permission and post-construction occupancy.
  - R-078 (Provisional fire NOC authority): authority routing expression computing
    `FIRE_AUTHORITY` string; no boolean approval applicability predicate (mirrors R-047 precedent).
  - R-079 (Schedule-I fire approval class): Schedule-I building class predicate
    requires composition with non-MIDC guard (`F-LOC-01 == False`) and fire authority
    `R-078` under `R-042`; standalone encoding under `APR-039` would over-apply to MIDC
    estates (`F-LOC-01 == True`) where MIDC Fire Services govern (`APR-030` / `R-036`);
    `R-042` itself is held in `REQUIRES_OFFICIAL_CONFIRMATION` due to fire renewal conflict `CON-013`.
  - R-080 (Planning authority routing): authority routing expression computing
    `BP_AUTHORITY` string; no boolean approval applicability predicate (mirrors R-047 precedent).
  - R-082 (UDCPR applicability regime selector): regulation regime selector (UDCPR vs own DCR),
    not an approval applicability predicate; encoding under `APR-038` would falsely
    negate building permission in excluded jurisdictions (e.g. MCGM, NAINA) where
    building permission is mandatory under local DCRs.
- Deferral Enforcement:
  - All 5 registered in `MH_DEFERRED_RULES` (`seed/mh/approvals.py`, now 25 deferred rules).
  - `_encode()` rejects all 5 fail-closed with explicit error messages.
  - Pack active rule count stays unchanged at 26 rules.
  - IN-GJ pack remains isolated with 19 rules; global default remains `IN-GJ`.
- Checks: 1285 passed (1263 baseline + 22 new tests in `test_mh_pack_planning_fire.py`),
  ruff clean, frontend TypeScript clean. No migration. No default flip.

## 53. MH Environmental / Consent Cluster Audit & Gated Deferrals (2026-09-28)

- Cluster Audited: R-003, R-004, R-007, R-008, R-013, R-014 across 20 evidence dimensions.
- R-007 (EIA Item 8(a) Building & Construction): Verified already implemented and active
  in pack (`_r007()`, APR-003, AUT-002, SRC-001/179, eff. 2006-09-14; lower bound 20,000 m2
  inclusive, upper bound 150,000 m2 exclusive; industrial shed exclusion quashed by Supreme
  Court in Vanashakti respected).
- 5 Rules DEFERRED (fail-closed against false negatives and non-applicability encoding):
  - R-003 (EIA 5(f) Category A vs B appraisal determination): Category determination
    (`CAT_BASE := A | B`), not an approval applicability predicate. Both Cat A and B projects
    require Prior EC (APR-001); encoding as an approval rule would falsely negate EC for
    Category B units. Requires cross-rule composition with R-002.
  - R-004 (EIA 5(f) General Condition category escalation): Category escalation rule
    modifying appraisal authority, not an approval applicability predicate. Requires
    composition with R-003 and existential quantifier evaluation over F-LOC-07 sub-facts.
  - R-008 (EIA 8(a) General Condition negative declaration): Meta-rule declaring General
    Condition category escalation inoperative for Item 8(a); not an independent approval
    applicability predicate. Encoding under APR-003 would contradict R-007.
  - R-013 (Consent to Establish Red/Orange/Green trigger): Requires rule composition with
    R-014 sector lookup and unmodeled intermediate fact MPCB_CATEGORY; standalone encoding
    cannot evaluate against F-MPCB-01 codes without lookup engine capability; multi-code
    cardinality guard R-015 emits UNKNOWN.
  - R-014 (CPCB sector code to pollution category lookup): Sector classification lookup
    function (operator LOOKUP), not an approval applicability predicate; full sector table
    not digitized; multi-activity cardinality guard R-015 emits UNKNOWN.
- Deferral Enforcement:
  - All 5 registered in `MH_DEFERRED_RULES` (`seed/mh/approvals.py`, now 30 deferred rules).
  - `_encode()` rejects all 5 fail-closed with explicit error messages.
  - Pack active rule count stays unchanged at 26 rules.
  - IN-GJ pack remains isolated with 19 rules; global default remains `IN-GJ`.
## 54. MH Labour & Factory Establishment Cluster Audit & Gated Deferrals (2026-09-28)

- Cluster Audited: R-019, R-020, R-027, R-022, R-023, R-090 across 20 evidence dimensions.
- Decision: All 6 rules are DEFERRED (fail-closed against false negatives, unmodeled statutory exceptions, and non-applicability classification):
  - R-019 (MSIHC Site Notification Rule 7): requires existential quantifier (`EXISTS c:`)
    over complex chemical inventory `F-HAZ-01`, multi-schedule evaluation (Sch 4 / Sch 3
    col 3 vs Sch 2 col 3 isolated storage), quantity aggregation across installations, and
    dynamic authority routing per Sch 5 (AUT-005 DISH, AUT-003 MPCB, AUT-008 PESO, District
    Collector) unsupported by `ConditionNode` primitives; standalone encoding cannot be
    simplified to `F-PRC-03 == True` without severe regulatory omission.
  - R-020 (MSIHC Safety Report Rules 10-12): requires existential quantifier (`EXISTS c:`)
    over `F-HAZ-01`, column 4 threshold lookup (distinct from and significantly higher than
    col 3 `derive_mah_status()`), and aggregation unsupported by condition primitives;
    unconfirmed col 4 values (UR-01 ethylene oxide '501' in S.O. 2882; ET-v4-06/ET-v5-05);
    targets APR-012 with different lifecycle/frequency (3-yearly update).
  - R-027 (Contractor Licence under OSH Code s.45(1)(ii) / s.47): contractor worker-count
    fact is absent from the registry (mapping to `F-LAB-03` would be regulatory guessing, as
    `F-LAB-03` measures contract labour engaged by the principal employer, not the contractor's
    workforce); applicant is the manufacturing occupier / principal employer, not the contractor.
  - R-022 (Factory Plan Approval & Licence under OSH Code s.2(1)(w) / s.79): statutory
    definition of "factory" rather than an approval applicability predicate; dual target
    `APR-015;APR-016` conflates pre-construction plan approval and pre-operation licensing;
    sub-threshold (<20 with power / <40 without) cannot safely evaluate to FALSE (`DOES_NOT_APPLY`)
    because saved s.85 hazardous-process notifications apply factory provisions to smaller
    chemical units regardless of headcount (ET-017 requires `CONDITIONAL`); Maharashtra
    pre-Code proviso number unverified (UNK-029).
  - R-023 (Factory Registration & Licence Category selector): DISH online service category
    selector (`DISH_LICENCE_CATEGORY := 'MAH/HAZARDOUS' | 'OTHER'`) determining scrutiny
    stream, fee schedule, and SLA (30 d vs 7 d), not an approval applicability predicate;
    outputs string classification, not boolean; 'hazardous process' criterion unencoded.
  - R-090 (BOCW Establishment Registration under OSH Code s.2(1)(h) / s.2(1)(v)): Section
    2(1)(h) explicitly excludes construction work related to a factory; whether construction
    of a new factory falls within the statutory exclusion is an unresolved legal interpretation
    in Maharashtra (ET-126 explicitly requires `UNKNOWN`); exception fact is unmodeled in the
    registry; naive encoding of `F-LAB-05 >= 10` would create a dangerous false positive.
- Deferral Enforcement:
  - All 6 registered in `MH_DEFERRED_RULES` (`seed/mh/approvals.py`, now 35 deferred rules).
  - `_encode()` prioritizes deferred check and rejects all 6 fail-closed with explicit error messages.
  - Pack active rule count stays unchanged at 26 rules.
  - IN-GJ pack remains isolated with 19 rules; global default remains `IN-GJ`.
- Checks: 1342 passed (1314 baseline + 28 new tests in `test_mh_pack_labour_factory.py`),
  ruff clean, frontend TypeScript clean. No migration. No default flip.

## 55. MH Utilities, Water & Power Cluster Audit & Gated Deferrals (2026-09-28)

- Cluster Audited: R-038, R-048, R-052, R-053, R-097 across 20 evidence dimensions.
- Decision: All 5 rules are DEFERRED (fail-closed against premature/invalid activation, unmodeled spatial/GIS data, unresearched legal bases, and utility-workflow conflation):
  - R-038 (MIDC water connection): utility service request (`MIDC-RTS-01`) under MIDC RTS with 15-day timeline, rather than a statutory approval applicability predicate; dual target conflation in register (`APR-034` water vs `APR-035` drainage with divergent predicates: a ZLD unit inside MIDC requires water connection but not drainage connection); requires set-membership on `F-WAT-01` enum-set; statutory regulations unread (UR-19 open; backed only by Tier T3 portal evidence `SRC-043`); status `REQUIRES_OFFICIAL_CONFIRMATION`.
  - R-048 (Electrical installation approval / energisation): statutory inspection and energisation approval under CEA Safety Regulations 2023 reg. 32/43; State-notified self-certification voltage threshold `F-ELE-02` is unestablished in Maharashtra (UNK-005 open); Central 11 kV threshold (PIB 05-08-2024) cannot be applied to Maharashtra per explicit edge tests ET-050 and ET-101 (which mandate `UNKNOWN`); CEI RTS 2018 notification (`SRC-041`) cites superseded CEA 2010 regulations; conflates approval applicability with inspection workflow and dynamic officer hierarchy routing (`approving_officer := 'Electrical Inspector' | 'Superintending Engineer' | 'CEI'`); status `REQUIRES_OFFICIAL_CONFIRMATION`.
  - R-052 (CETP membership / discharge arrangement): no statutory source cited (`source_id: -`); classified `UNKNOWN` in machine summary and register (one of only 3 UNKNOWN rules); estate-level CETP existence, hydraulic capacity, and effluent acceptance are unmodeled site-specific facts (`UNK-011` open; ET-055 strictly requires `UNKNOWN`); contractual/infrastructure arrangement or consent condition rather than an independent statutory approval applicability predicate.
  - R-053 (WRD river / surface water abstraction): statutory legal basis explicitly unresearched across all v5 datasets ("Not researched" in rules/approvals/authorities); backed solely by Tier T3 MAITRI portal list (`SRC-070`); competent WRD authority routing unverified (`UR-17` open; `authority_status REQUIRES_CONFIRMATION`); distinguishes river/surface source without authoritative basin GIS layer; prompt conflated approval identity with `APR-045` (electricity) and `AUT-014` (GSDA), while true approval is `APR-051` under `AUT-021` (WRD); status `REQUIRES_OFFICIAL_CONFIRMATION`.
  - R-097 (Maharashtra Groundwater Authority deep well prohibition): statutory prohibition condition (`CND-024` / `MH_GW_DEEP_WELL_PROHIBITION`) under Maharashtra Groundwater Act 2009 s.8(1), not an approval application; complete village list for 80 notified watersheds (MWRRA Order 31-07-2015, `SRC-166`) unencoded in GIS layer (`UR-15` open; partial machine parse); post-2015 order currency unconfirmed; unconfirmed location must fail closed to `INSUFFICIENT_DATA` per ET-v5-24, never `DOES_NOT_APPLY`; status `REQUIRES_OFFICIAL_CONFIRMATION`.
- Deferral Enforcement:
  - All 5 registered in `MH_DEFERRED_RULES` (`seed/mh/approvals.py`, now 40 deferred rules).
  - `_encode()` prioritizes deferred check and rejects all 5 fail-closed with explicit error messages.
  - Pack active rule count stays unchanged at 26 rules.
  - IN-GJ pack remains isolated with 19 rules; global default remains `IN-GJ`.
- Checks: 1374 passed (1342 baseline + 32 new tests in `test_mh_utilities_water_power.py`),
  ruff clean, frontend TypeScript clean. No migration. No default flip.

## 56. MH Safety, Hazardous Chemicals & Transport Cluster Audit & Gated Deferrals (2026-09-29)

- Cluster Audited: R-030, R-032, R-033, R-034, R-035, R-062, R-092 across 20 evidence dimensions.
- Disambiguation of Prompt Starting Inventory vs Authoritative Register:
  - R-030: Petroleum storage licence / Class B statutory exemption under Petroleum Act 1934 s.7(1)(a)
    and Petroleum Rules 2002 (APR-026, AUT-008 Circle Controller / AUT-009 District Authority). Prompt
    listed candidate APR-024 (non-existent). Already active in pack (`_r030()`, line 361); audit confirms
    `PET_EXEMPT_B` is a statutory exemption predicate rather than a positive licence applicability rule;
    active inclusion preserved with limited-scope boundaries pinned.
  - R-032: Prompt labeled candidate as "Gas cylinder storage licence". In authoritative register, R-032 is
    Petroleum licence form and authority routing expression computing `PET_FORM := 'XII (DA)' | 'XIII (DA)' |
    'XVI (PESO)' | 'XV (PESO)'` under APR-026. This is a form/authority selector rather than an approval
    applicability predicate; combination rules for multiple classes unmodeled; cannot be expressed by
    boolean `ConditionNode` primitives. DEFERRED.
  - R-033: Prompt labeled candidate as "Static and Mobile Pressure Vessels licence". In authoritative register,
    R-033 is Gas cylinder storage licence statutory exemption under Gas Cylinders Rules 2016 r.44 (`GCR_EXEMPT`,
    APR-027). Requires list iteration and per-group quantifiers over complex inventory `F-GAS-01`; LPG clause
    under r.44(c) is legally ambiguous (UNK-016, PT-05); gas classification unmodeled (UNK-039); unread GCR
    amendments remain (UR-10). DEFERRED.
  - R-034: True SMPV(U) Rules 2016 rule under APR-028 (LS-1A licence & r.2 definition). Requires existential
    quantifier (`EXISTS`) over `F-PV-01` list and process vessel exclusion filtering (r.3 16-hr feed rule);
    official status is `REQUIRES_OFFICIAL_CONFIRMATION` due to unread amendments (UR-10). DEFERRED.
  - R-035: Prompt labeled candidate as "Factory safety / hazardous-process approval". In authoritative register,
    R-035 is MIDC plot allotment branch guard (`MIDC_BRANCH := F-LOC-01 == True`, APR-029 / AUT-010). Already
    active in pack (`_r035()`, line 375). The prompt's conceptual target (Factory safety / hazardous process)
    was independently audited in the Labour cluster: R-022 (Factory Plan Approval APR-015 & Licence APR-016)
    and R-023 (DISH licence category) remain safely deferred, while R-070 is active under CMP-018. Preserved active.
  - R-062: Prompt labeled candidate as "Biomedical Waste authorization APR-011". In authoritative register,
    R-062 is Consent to Establish CTO validity rule under GSR 62/63 (`CTO_VALIDITY := 'VALID_TILL_CANCELLED'`),
    a lifecycle validity rule under APR-008, not an approval applicability predicate; CTO grant date fact is
    absent from registry; Maharashtra MPCB operational implementation is unconfirmed (UNK-032). Candidate
    Biomedical Waste Management Rules 2016 do NOT apply to synthetic organic chemical manufacturing (zero BMW
    rules/approvals in domain; APR-011 in register is integrated consent + HW, `DO_NOT_IMPLEMENT_YET`). DEFERRED.
  - R-092: Petroleum District Authority NOC under Petroleum Rules 2002 r.144 (APR-026); requires cross-rule
    composition with deferred R-032 (form and authority routing); cannot be evaluated standalone. DEFERRED.
- Deferral Enforcement:
  - R-032, R-033, R-034, R-062, R-092 registered in `MH_DEFERRED_RULES` (`seed/mh/approvals.py`, now 45 deferred rules).
  - `_encode()` prioritizes deferred check and rejects all fail-closed with explicit error messages.
  - Active pack rule count stays unchanged at 26 rules (R-030 and R-035 active).
  - IN-GJ pack remains isolated with 19 rules; global default remains `IN-GJ`.
- Checks: 1410 passed (1374 baseline + 36 new tests in `test_mh_safety_hazardous_transport.py`),
  ruff clean, frontend TypeScript clean. No migration. No default flip.

## 57. MH Sector-Specific Approvals / Clearance Pack Audit & Gated Deferrals (2026-09-29)

- Cluster Audited: R-051, R-068, R-069, R-095, R-105 across 20 evidence dimensions.
- Decision: All 5 rules are DEFERRED (fail-closed against premature activation, spatial GIS data absence, statutory definition mismatches, unresearched amendments/forms, and rule-type conflation):
  - R-051 (AAI Height Clearance NOC under MoCA G.S.R. 751(E) 2015, APR-049 / AUT-020): requires 3D GIS spatial intersection against aerodrome Obstacle Limitation Surfaces (OLS) and Colour Coded Zoning Map (CCZM) elevation grids; structure AMSL elevation (Site elevation + structure/chimney height) vs grid cell permissible AMSL; spatial datasets and elevation models unrepresented in repository; status in register is `REQUIRES_OFFICIAL_CONFIRMATION` with LOW confidence (`SRC-063`, `SRC-104`).
  - R-068 (Drug / bulk drug / API manufacturing licence under Drugs Rules 1945 Part VII, APR-056 / Maharashtra FDA): applies strictly to manufacturing statutorily defined drugs/APIs under Drugs & Cosmetics Act 1940 s.3(b); synthetic organic chemicals and general chemical intermediates are not drugs; licensing form numbers not re-extracted; UNK-036 and UR-11 open for MH FDA authority routing and state notification; status `REQUIRES_OFFICIAL_CONFIRMATION` (`SRC-101`, `SRC-070`).
  - R-069 (Explosives licence (manufacture/possession) under Explosives Rules 2008, APR-059 / AUT-008 PESO): substance classification as explosive is an expert/PESO input outside engine scope (peso_gating note); general chemical manufacturing does not manufacture explosives; possession thresholds unextracted (UNKNOWN for possession-only); Schedule VII safety distance geometry unsupported by condition primitives; distinct from Petroleum (APR-026), Gas Cylinders (APR-027), SMPV (APR-028), and MSIHC (APR-012); status `REQUIRES_OFFICIAL_CONFIRMATION` (`SRC-107`, `SRC-119`).
  - R-095 (Ozone Depleting Substances regulation under ODS Rules 2000 r.8, CND-022 / MoEFCC Ozone Cell): represents a compliance condition / registration obligation (`RULE_LOGIC`), NOT an approval in `approvals.csv`; producer (r.3) and seller (r.6) branches unmodeled in fact registry (`F-ODS-01` only covers use in Schedule IV activities); post-2000 amendments unverified (Kigali Amendment, 2014 & 2021 amendments); status `VERIFIED_CONDITIONAL` (`SRC-127`).
  - R-105 (Planning Zone Industrial Permissibility under MRTP Act 1966 s.44 and UDCPR Reg. 1.4(iii), PS-02 / Planning Authority): planning workflow gate (`RULE_LOGIC`), NOT an approval in `approvals.csv`; never produces binary `APPLIES` / `DOES_NOT_APPLY`; requires 4 inputs (`F-LOC-05`, `F-PLN-02`, `F-PLN-03`, `F-PLN-04`); emits `CONDITIONAL (AUTHORITY_SITE_DEPENDENT)` when all 4 known, else `INSUFFICIENT_DATA` (per edge tests ET-v5-21 and ET-v5-22); municipal DP/RP zoning data unmodeled; composes with deferred planning rules R-041, R-078, R-080, R-082 and active R-035; status `VERIFIED_CONDITIONAL` (`SRC-123`, `SRC-124`).
- Deferral Enforcement:
  - All 5 registered in `MH_DEFERRED_RULES` (`seed/mh/approvals.py`, now 50 deferred rules).
  - `_encode()` prioritizes deferred check and rejects all 5 fail-closed with explicit error messages.
  - Active pack rule count stays unchanged at 26 rules.
  - IN-GJ pack remains isolated with 19 rules; global default remains `IN-GJ`.
- Checks: 1449 passed (1410 baseline + 39 new tests in `test_mh_sector_specific.py`),
  ruff clean, frontend TypeScript clean. No migration. No default flip.

## 58. MH Environmental Protection & Extended Producer Responsibility (EPR) Pack Audit (2026-09-29)

- Cluster Audited: Plastic Waste Management / EPR (`EPR-PWM`, `EPRS-01`, `EPRS-02`), Battery Waste Management 2022 (`EPR-BAT`, `EPRS-03`, `EPRS-04`), E-Waste Management 2022 (`EPR-EWASTE`, `EPRS-05`, `EPRS-06`, `R-094`), Hazardous Waste Import/Export (HOWM Rules 2016 r.11-15, Schedule III/IV/VI/VII, step `H5`), Environmental Statement / Form V (`CMP-005`), Environment Audit (`R-072` / `CMP-014`), and additional EPR regimes (`EPR-OIL`, `EPR-TYRE`, `EPR-NFM`, `EBWGR-SWM`, `SWM-RDF`).
- Boundary Decision & Product Layer Separation:
  - ZERO new active approval rules added.
  - Regulated entity roles vs industrial consumers: chemical manufacturing units are ordinary industrial users/consumers of packaging, batteries, and electrical equipment; they do NOT automatically hold statutory "Producer", "Importer", or "Brand Owner" (PIBO) roles under PWM, BWM, or E-Waste Rules.
  - Per edge test `ET-v5-18`, chemical manufacturing alone with no role facts evaluates to `INSUFFICIENT_DATA (never APPLIES)`. Per `ET-v4-17`, unknown battery role evaluates to `UNKNOWN`.
  - EPR regimes (`EPR-PWM`, `EPR-BAT`, `EPR-OIL`, `EPR-TYRE`, `EPR-NFM`, `EBWGR-SWM`) are classified in the repository registers as `OPERATING_DUTY / REGISTRATION (not a project-stage approval)`. None exists in `approvals.csv` as an `APR-xxx`. Modeling them as pre-establishment approval rules would create fake approvals and violate architectural boundaries.
  - E-Waste bulk consumer duty (Rule 8, handover to registered entities if `F-EEE-01 >= 1000`) is already actively encoded as `R-094` targeting `CMP-025`. EEE Producer EPR registration (`EPRS-06`) is inapplicable to the chemical manufacturing domain.
  - Hazardous Waste Import / Export: Governed by MoEFCC under HOWM Rules 2016 Chapter III / Form 5 (transboundary movement procedure) and Customs verification (Schedule VII), not an MPCB industrial approval. Step `H5` in `howm_decision_path.csv` requires trade facts and evaluates to `UNKNOWN`. No import/export trade facts exist in `facts.py`; fails closed to `INSUFFICIENT_DATA` / `UNKNOWN`.
  - Environmental Statement / Form V (`CMP-005`): Classified in `compliance.csv` as an annual statutory compliance return (`record_type: RETURN`, `lifecycle_stage: OPERATION`), due on or before 30 September each year to MPCB (`AUT-003`) under EP Rules 1986 r.14. It belongs to the compliance obligations, deadline engine, and operational return layer, NOT the approval applicability engine.
  - Environment Audit (`R-072` / `CMP-014`): Governed by Environment Audit Rules 2025 S.O. 3973(E); in `compliance.csv`, `CMP-014` is explicitly marked `DO_NOT_IMPLEMENT_YET` because audit is not a blanket obligation (applies only when assigned by authority or engaged by proponent); unmodeled in fact registry.
- Isolation & Counts:
  - Active MH rule count stays strictly unchanged at 26 rules (R-094 already active).
## 59. MH Consent to Operate (CTO) & Renewal Audit (2026-09-29)

- Cluster Audited: R-017 (CTO under Water & Air Acts, APR-009), R-063 (CTO expansion/amendment outer limit, APR-009 / SLA-036), R-055 (MPCB consent amendment vs fresh consent, APR-053), CMP-007 (CTO validity / renewal / MPCB auto-renewal), and R-062 (CTO validity under GSR 62/63).
- Boundary Decisions & Architectural Subsystem Segregation:
  - ZERO new active approval rules added (active MH approval rules strictly 26).
  - R-017: CTO applicability under Water Act s.25 and Air Act s.21 conceptually belongs to the approval applicability layer (`APR-009`), but its condition `CTO_REQUIRED := CONSENT_REQUIRED == TRUE` requires rule composition with deferred rule `R-013`. `R-013` itself requires full CPCB/MPCB sector classification lookup `R-014` over `F-MPCB-01` and cardinality guard `R-015` (multi-activity emits `UNKNOWN`, maximum-category convention is unevidenced). White category units are explicitly exempt from consent management (`ET-049`). Because the engine lacks a rule-composition primitive and sector lookup is not digitized, R-017 cannot be evaluated standalone and is deferred fail-closed. In dependency evaluation, CTO is satisfied via `obtained_approvals` for downstream approvals like `APR-010` (`DEP-009`).
  - R-063: Register cross-check resolves label mismatch: R-063 is NOT an approval applicability rule deciding whether CTO applies. It is an SLA timeline outer limit specification (`CTO_EXPANSION_OUTER_LIMIT := 90 / 60 / 30 days`, `SLA-036`) under GSR 62/63 para 8 table Sl.3. Column headings mapping to Red/Orange/Green are unresolved (`UNK-031`, `GSR-11`), and register status is `REQUIRES_CONFIRMATION` / `REQUIRES_OFFICIAL_CONFIRMATION`. Deferred in `MH_DEFERRED_RULES` and retained in `MH_REQUIRES_CONFIRMATION_RULE_IDS`.
  - R-055: MPCB consent amendment vs fresh consent (circular 25-08-2025, `SRC-068`) belongs to the modification-stage workflow / change-assessment layer (`APR-053`), NOT boolean approval applicability. Outputs categorical branch `'AMENDMENT'` (clerical, name change, HW disposal path) vs `'FRESH'` (fuel, DG set, HW quantity, process change) over `F-CHG-01`. Unlisted changes (inventory increase `ET-107`, water source change `ET-109`) and pollution load increases require technical officer appraisal (`CONDITIONAL` / `INSUFFICIENT_DATA`). Deferred in `MH_DEFERRED_RULES`.
  - CMP-007: Classified in `compliance.csv` as a continuing compliance renewal obligation (`record_type: RENEWAL`, `lifecycle_stage: RENEWAL`), NOT an approval rule. Explicitly marked `implement_status: DO_NOT_IMPLEMENT_YET`. Subject to statutory regime conflict `CON-006` between central MoEFCC GSR 62(E)/63(E) (valid-till-cancelled, 2026-01-27) and State MPCB circular 13-08-2025 (5/10/15-year auto-renewal). State fee structure is un-notified (`GSR-04` BLOCKED), treatment of legacy pre-2026 CTOs is unconfirmed (`UNK-032`, `UR-05`), and post-2026 MPCB implementation is unresolved (`UNK-001`). Resolution: do not compute validity; display both with status.
  - Auto-Renewal: MPCB circular 13-08-2025 (`SRC-069`) is an administrative self-declaration workflow (`SLA-037`, 7 days), NOT a statutory deemed consent. Central law has eliminated periodic renewal for post-2026 CTOs (`GSR-06`).
- Deferral Enforcement:
  - `MH_DEFERRED_RULES` updated with R-017, R-055, and R-063 (count increases from 50 to 53).
  - All deferred rules rejected fail-closed via `_encode()` with explicit error messages.
  - Active MH rule count stays strictly unchanged at 26 rules.
  - IN-GJ pack remains isolated with 19 rules; `DEFAULT_JURISDICTION = "IN-GJ"` strictly preserved.
  - Fact registry untouched: zero new facts added (128 MH facts preserved).
- Checks: 1520 passed (1479 baseline + 41 new tests in `test_mh_cto_renewal.py`), ruff clean, frontend TypeScript clean. No migration. No default flip.

## 60. MH Establishment & Labour Registration Cluster Audit (2026-09-29)

- Cluster Audited: R-024 (OSH Code s.3 establishment registration, APR-017 / APR-060), R-025 (Shops & Establishments intimation, APR-018), R-098 (Mathadi/manual workers regulation, CND-025).
- Boundary Decisions & Architectural Subsystem Segregation:
  - ZERO new active approval rules added (active MH approval rules strictly 26).
  - R-024: APR-017 and APR-060 (split record) both recorded as `DO_NOT_IMPLEMENT_YET` in authoritative `approvals.csv`. Maharashtra OSH State rules remain **DRAFT as of 06-05-2026** (UR-12 OPEN, UNK-008 active). Administrative procedure, electronic registration portal, and designated registering officer in MH are unnotified. Chemical factories are regulated by DISH (AUT-005) under saved Factories Act rules; s.3(8) provides deemed registration for existing factories. Dual authority routing AUT-006/AUT-005 is unresolvable without additional facts. Second OR-clause (hazardous process) requires an unmodeled fact. Deferred fail-closed.
  - R-025: Source SRC-027 is a T5 secondary mirror of a T2 circular — LOW confidence. `approvals.csv` explicitly notes "Relevance to a factory establishment not verified" for APR-018. Industrial chemical factories are regulated by DISH / Factories Act / OSH Code and are outside the S&E Act scope. Status `REQUIRES_OFFICIAL_CONFIRMATION`. Deferred fail-closed.
  - R-098: CND-025 appears in `conditional_regs.csv` as obligation type `RULE_LOGIC`, NOT in `approvals.csv` as an APR-xxx. Encoding it as an `ApprovalRule` would violate the architectural boundary (approval applicability ≠ compliance condition). Chemical manufacturing per se is not a "scheduled employment" under the Mathadi Act 1969. The Thane/Raigad loading/unloading notification (01-08-1983) covers specific activities, not all manufacturing. Both required facts (F-LOC-19, F-LAB-10) exist in the MH fact registry but a generic `F-LAB-10 == TRUE → APPLIES` encoding is unsafe without verified area-specific board scheme data. Deferred fail-closed.
- Deferral Enforcement:
  - `MH_DEFERRED_RULES` updated with R-024, R-025, R-098 (count increases from 53 to 56).
  - All three rejected fail-closed via `_encode()` with explicit traceable rationale.
  - Active MH rule count stays strictly unchanged at 26 rules.
  - IN-GJ pack remains isolated with 19 rules; `DEFAULT_JURISDICTION = "IN-GJ"` strictly preserved.
  - Fact registry untouched: zero new facts added.
- Checks: 1553 passed (1520 baseline + 33 new tests in `test_mh_establishment_labour.py`), ruff clean, frontend TypeScript clean. No migration. No default flip.

## 61. MH Fire Protection, Building Permissions & Local Authority Approvals Audit (2026-09-29)

- Cluster Audited: R-037 (MIDC OC, APR-032, PRE_OPERATION, AUT-010, T3 SRC-044),
  R-041 (non-MIDC BP, APR-038 PRE_CONSTRUCTION + APR-041 PRE_OPERATION, AUT-011,
  T1/T2 SRC-123/124/067), R-078 (fire authority routing CASE, APR-039/APR-040,
  AUT-012, T1 SRC-121), R-079 (Schedule-I class predicate, APR-039/APR-040,
  AUT-012, T1 SRC-121), R-080 (BP authority CASE, APR-038, AUT-011, T1 SRC-123),
  R-082 (UDCPR regime NOT-IN exclusion, APR-038, AUT-011, T2 SRC-124).
- Boundary Decisions (all verified against rule_register/rules/approvals/
  authorities/facts/sources/dependencies/requires_confirmation/unknowns/
  unresolved/sla/edge_tests/planning_fire_tree/planning_steps):
  - ZERO new active approval rules. `approvals.py` untouched; active pack 26.
  - R-037: C. EVIDENCE INCOMPLETE — portal-only (UR-19 OPEN, CON-001 SLA
    conflict); gated by `MH_REQUIRES_CONFIRMATION_RULE_IDS`; deps
    DEP-005/006/007 are readiness edges, not applicability conditions.
  - R-041: D. ENGINE LIMITATION (`construction` fact absent; needs R-080 +
    R-082 composition) + E. MISCLASSIFIED (dual lifecycle APR-038/APR-041).
  - R-078: E. MISCLASSIFIED — FIRE_AUTHORITY string CASE, mirrors R-047.
  - R-079: D. ENGINE LIMITATION — needs non-MIDC guard + R-078 + R-042
    composition; standalone over-applies to MIDC (J-class test).
  - R-080: E. MISCLASSIFIED — BP_AUTHORITY CASE, mirrors R-047.
  - R-082: E. MISCLASSIFIED — regime selector; MCGM/NAINA/MIDC exclusion ≠
    DOES_NOT_APPLY (ET-119). No planning-regime selector in architecture.
  - Engine has no rule-reference / dynamic-authority / regime primitives
    (by design); `construction` unmodeled; fire/building sources correctly
    deferred from 22-source loaded pack; UNKNOWN never FALSE.
- Tests: `backend/tests/test_mh_fire_building.py` — 139 tests (identity,
  per-rule audits, composition limits, fact ontology, classification,
  edge cases incl. MIDC≠auto-BP, UNKNOWN-construction, routing/regime
  separation, R-082-no-negation, R-079-no-overapply, jurisdiction isolation,
  evidence gaps, batch-1/batch-2/location + GJ regression). Five draft
  failures fixed (deferred-source assertions, string `result`, R-037
  not-safe message) + ruff fixes.
- Checks: 1692 passed (1553 baseline + 139 new), ruff clean, frontend
  TypeScript clean. No migration. No default flip. Fact registry 128,
  unchanged. Artifact: `audit_mh_fire_building.md`.

## 62. MH Workflow/Lifecycle Cluster Audit (2026-09-29)

- Cluster Audited: R-081 (BP_DEEMED_POSSIBLE, APR-038, PRE_CONSTRUCTION,
  AUT-011, T1 SRC-123 s.45(5), 1966 YEAR_ONLY), R-099
  (FINAL_FIRE_APPROVAL_RENEWAL, APR-040, PRE_OPERATION, AUT-012, T2 SRC-145,
  EXACT 2023-05-30), R-036 (MIDC_BP combined, APR-030/031/033 spanning
  PRE_CONSTRUCTION/CONSTRUCTION/PRE_OPERATION, AUT-010, T3 SRC-043/044,
  effective UNKNOWN).
- Boundary Decisions (verified against current rule_register/rules/approvals/
  authorities/facts/sources/dependencies/requires_confirmation/unknowns/
  unresolved/sla/edge_tests/fire_renewal_model/compliance):
  - ZERO new active ApprovalRules. `approvals.py` change is 2 deferred
    entries only; active pack 26; no builder, engine, fact, or pack change.
  - R-081: E (workflow consequence, not applicability) — DATE arithmetic
    over absent application/requisition dates, DCR-conformance proviso,
    register forbids asserting grant; SLA-042 display-only.
  - R-099: E (renewal/lifecycle, never APPLIES) — FR-01/CON-013 general
    DOES_NOT_APPLY, FR-02 conditional pointer via modeled F-FIR-20,
    FR-03/CON-024/UR-04 sector exception unresolved, FR-04/CMP-008 Form B
    separate; FR-07 portal listing never a trigger.
  - R-036: C (confirmation-gated, unchanged) — T3 portal-only (UR-19),
    absent `construction` fact, triple-stage/record-class bundle;
    DEP-003/004/019 correctly triaged out; ET-v5-28 holds.
  - R-042 composition hub (R-079 + R-078 + R-099) stays confirmation-gated;
    no rule-reference/dynamic-authority/regime/DATE/grant primitives added.
- Tests: `backend/tests/test_mh_workflow_lifecycle.py` — 58 tests (identity,
  deemed analysis, renewal analysis with F-FIR-20 engine checks, portal
  analysis, cross-rule, fact/evidence discipline, isolation,
  classification). Two draft assertions fixed to actual code behavior.
- Checks: 1750 passed (1692 baseline + 58 new), ruff clean, frontend
  TypeScript clean. No migration. No default flip. Fact registry 128,
  unchanged. Artifact: `audit_mh_workflow_lifecycle.md`.

## 63. MH MIDC Lifecycle Tail Audit (2026-09-29)

- Cluster Audited: R-039 (MIDC tree felling, APR-036 + APR-042 dual-target
  routing fork, AUT-010/AUT-022, T3 SRC-043/070, effective UNKNOWN), R-040
  (MIDC change in manufacturing activity, APR-037 OPERATION/MODIFICATION,
  AUT-010, T3 SRC-043, effective UNKNOWN), APR-031 (plinth/commencement
  e-intimation: REGISTRATION/REPORT, CONSTRUCTION lifecycle, rule R-036
  gated), DEP-019 (APR-029 plot holder -> APR-030 BP: YES_INFERRED,
  MEDIUM, T3 service list, OFFICIAL_WORKFLOW).
- Boundary Decisions (verified against current rule_register/rules/
  approvals/authorities/facts/sources/dependencies/requires_confirmation/
  unknowns/unresolved/sla/edge_tests):
  - ZERO new active ApprovalRules. Only code change: DEP-019 rationale
    strengthened to record inferred status (loaded edges still DEP-009 x2).
  - R-039: C (confirmation-gated, unchanged) — routing fork unexpressible
    in ConditionNode; MIDC branch portal-only (UR-19); urban branch cites
    unfetched Trees Act 1975 (LOW, UR-17 routing OPEN); no edge tests.
  - R-040: C (confirmation-gated, unchanged) — portal-only; change fact
    unmodeled and F-EXP-01 is wrong semantics + BOOL-without-UNKNOWN;
    modification events belong to workflow state, not regulatory facts.
  - APR-031: REPORT, correctly unmodeled (zero code refs; no pack
    authority/edge/SLA/source); no rule equates it with approvals.
  - DEP-019: inferred ordering, never statutory; zero impact on active
    rules (APR-030 rule-less; R-035 needs no BP input).
- Tests: `backend/tests/test_mh_midc_lifecycle_tail.py` — 59 tests
  (identity, REPORT boundary, inferred-dependency discipline,
  UNKNOWN/missing/invalid, no portal-to-statutory inference, cross-rule
  separation, isolation, classification).
- Checks: 1809 passed (1750 baseline + 59 new), ruff clean, frontend
  TypeScript clean. No migration. No default flip. Fact registry 128,
  unchanged. Artifact: `audit_mh_midc_lifecycle_tail.md`.

## 64. MH Consent Category Chain Audit (2026-09-29)

- Cluster Audited: R-013 (CONSENT_REQUIRED over MPCB_CATEGORY, APR-008,
  T2 SRC-011 + T4 SRC-010, EXACT 2025-06-23), R-014 (SECTOR_CATEGORY
  lookup(F-MPCB-01), operator LOOKUP, partial chemical codes, note
  "others → UNKNOWN"), R-015 (UNIT_CATEGORY multi-code := UNKNOWN,
  GUARD_OR_ROUTING, T4 SRC-011, MAX-convention forbidden, UNK-002 OPEN),
  R-017 (CTO_REQUIRED := CONSENT_REQUIRED, required_inputs literally
  R-013, APR-009 PRE_OPERATION, T1 SRC-004). Context: R-016 deemed CTE
  stays DNI (ET-072/073 never-granted).
- Boundary Decisions (verified against current rule_register/rules/
  approvals/authorities/facts/sources/dependencies/requires_confirmation/
  unknowns/unresolved/sla/edge_tests, incl. CSV-read identity tests):
  - ZERO new active ApprovalRules. Only pack-logic change: R-015 explicit
    deferral entry (loaded pack identical; `_encode` message upgrade).
  - R-013: D (needs R-014 output + unmodeled MPCB_CATEGORY; White exempt
    ET-049, UNKNOWN ET-110 preserved).
  - R-014: E (no LOOKUP operator — op set is eq/in/gte/lte/gt/lt; table
    undigitized and T4-mirror-sourced with OCR adoption circular).
  - R-015: D (mandated UNKNOWN; MAX explicitly forbidden; LIST input
    makes multi-code structurally possible, hence the guard).
  - R-017: D (register-level rule reference; CTE→CTO is lifecycle staging
    with precondition CTE, not a corollary; no renewal import; dependency
    engine proves unknown consent blocks downstream APR-010).
  - F-MPCB-01 LIST per-activity verified (None valid, scalars/mappings
    rejected, no element check — further R-014 evidence); no scalar
    industry-type fact exists; 128 facts unchanged.
- Tests: `backend/tests/test_mh_consent_category_chain.py` — 60 tests
  (CSV identity matrix, lookup-table audit, aggregation guard, CTO gate
  with engine BLOCKED proof, fact ontology, approval semantics incl.
  GSR-02/CMP-007 separation, isolation, classification). One draft
  assertion fixed to actual LIST validator behavior; two prior baseline
  pins updated 58→59.
- Checks: 1869 passed (1809 baseline + 60 new), ruff clean, frontend
  TypeScript clean. No migration. No default flip. Fact registry 128,
  unchanged. Artifact: `audit_mh_consent_category_chain.md`.

## 65. MH HW Authorization Content-Chain Audit (2026-09-29)

- Cluster Audited (first ACTIVE-rule audit, falsification mandate): R-018
  (HW_AUTH := F-HW-01==TRUE, APR-010, T1 SRC-013 r.6(1), EXACT 2016-04-04)
  and R-096 (HW_SCH2_TEST over F-HW-04, register operator ANY, T2 SRC-120
  Sch II, EXACT 2016-04-04). Both stay ACTIVE: R-018 class A
  (safe-as-implemented), R-096 class B (bounded: UNK-034 currency outside
  decision path, [] supply discipline, lab-conclusion token discipline).
- Chain Reconstruction: disjoint inputs, no composition; APPLIES-first
  priority verified fail-safe both contradiction ways; F-HW-02
  stream/entry content correctly absent from predicates (supplied, never
  inferred); DOC-001/002/003 + Forms in document layer; DEP-009 blocks
  APR-010 until CTE/CTO obtained (obtained cures only applies-state
  prereqs); per-stream Schedule-I mapping correctly unattempted (UNK-014
  content layer, 54-row hw_streams reference only).
- Surgical Fix: `_evaluate_leaf` `in` branch — list-embedded "UNKNOWN"
  with no established match now yields INSUFFICIENT_DATA instead of FALSE
  (register: never coerced to FALSE; docstring already promised it);
  established positives still APPLY. R-096 is the sole active list-`in`
  rule; full suite green with no other changes.
- Tests: `backend/tests/test_mh_hazardous_waste_authorization_chain.py` —
  63 tests (CSV identity, reconstruction, R-018/R-096 safety incl.
  windows, ANY semantics, approval matrix, propagation, content split,
  fact discipline, isolation, classification). One prior consent-test
  input corrected to lowercase engine contract (same conclusion).
- Checks: 1980 passed, ruff clean, frontend TypeScript clean. No
  migration. No default flip. Counts unchanged (26/59/26/19/128).
  Artifact: `audit_mh_hazardous_waste_authorization_chain.md`.

## 66. MH R-021 Closure Audit (2026-09-29)

- Candidate Closed: R-021 (MAH derivation: EXISTS over F-HAZ-01 with
  Sch2/Sch3 col-3 lookup, Part II class TOTALs, 500m aggregation;
  required_inputs literally R-019; APR-012 COMPLIANCE_APPROVAL/REPORT,
  PRE_OPERATION;OPERATION; 4-way Sch-5 routing; T1 SRC-016 as amended to
  2000; 2000 YEAR_ONLY; DOC-009/CMP-010/CMP-020/CMP-011 sibling duties).
- Disposition: **DEFERRED, class D** (composition with deferred R-019;
  EXISTS/lookup/aggregation/routing unrepresentable — op set asserted
  exact; partial pipeline derive_mah_status covers exact-string col-3
  join only; ET-081 UNKNOWN discipline; source ceilings: no post-2000
  amendments, no Sch 1 Part I, no sum-of-ratios; per-entry blocks
  S1-TOX/S2-18/S3P1-111 kept; UR-01/02/03 open).
- Falsification run: 8 attempted defeaters, all supporting deferral; no
  finding supports activation. APR-012 fully unmodeled in pack (no
  authority/docs/SLA/hints/edges/rules). DEP-010/011/026 correctly
  triaged (activity endpoints). F-HAZ-01/02 strict LISTs (UNKNOWN token
  rejected; None valid); F-PRC-03 derived-only.
- Change: one deferral entry (untriaged 6→5: R-054/059/071/072/076
  remain). Zero activations, facts, primitives, donor modifications.
- Tests: `backend/tests/test_mh_r021.py` — 49 tests (CSV identity,
  semantics, sources, facts + derivation matrix, engine, falsification,
  dependencies, isolation, decision). Cascades: three deferred pins +
  HW-chain pins 59→60; parallel inventory UNTRIAGED set minus R-021
  (already anticipated).
- Checks: 2077 passed, ruff clean, frontend TypeScript clean. No
  migration. No default flip. Counts 26/60/26/19/128. Artifact:
  `audit_mh_r021.md`.

## 67. MH R-054 Closure Audit (2026-09-29)

- Candidate Closed: R-054 (EC_EXPANSION_EXEMPT 6-conjunct AND, APR-052
  EXPANSION lifecycle, AUT-001/AUT-002, CENTRAL, T1 SRC-001 para 7(ii)(b),
  effective UNKNOWN, approval itself ROC with UNKNOWN preconditions).
- Falsification: facts-only probe (F-EXP-01 + F-EXP-02==FALSE) reports
  APPLIES while blind to item 2-5 scope, Appendix-XIII certificate,
  OCMS >=95%, B2->A/B1 exclusion, holder status (all verified absent;
  F-EXP-01 strict BOOL, no UNKNOWN); approval-level APPLIES inverts
  "exempt" into "approval applies" and erases Form-I else-branch (ET-068);
  ET-067/069 house covered. R-002/APR-001 separation verified (different
  approval, item scope, question). No APR-052 rows in deps/compliance/
  SLA/conditional/confirmation/unknowns/unresolved; containment proven
  (no live APR-052 rule).
- Disposition: **DEFERRED, class D** (missing conjunct facts; source T1
  suffices so not C; obligation real so not DNI/G; identity complete so
  not UNKNOWN). Untriaged 6→4 (R-059/071/072/076 remain).
- Change: one deferral entry; parallel draft adopted (header, baseline,
  triage test, `_encode` import, closure class with R-002/authority/
  strictness/temporal/arithmetic/R-021-preserved tests). Cascades 60→61
  across consent/workflow/tail/HW/r021 pins (+ parallel inventory/EC-core
  already converged).
- Checks: 2140 passed, ruff clean, frontend TypeScript clean. No
  migration. No default flip. Counts 26/61/26/19/128. Artifact:
  `audit_mh_r054.md`.

## 71. MH Remaining-Hygiene Closure (2026-09-29, documentary)

- Closed R-059 (incentive NOT_COMPUTED hard stop; criteria not located;
  relevance engine structurally value-free), R-071 (GW Act TRUE-from
  2014-06-01 date gate; FALSE forbidden by register note; orphan
  F-WAT-05 linkage harmless), R-072 (assignment-only audit duty; twin
  of CMP-014 DNI; no trigger fact), R-076 (1 Jun/1 Dec facet owned by
  CMP-006 text; para-10 attribution tension resolved 3-way corroborated;
  EC-granted state unmodeled).
- Dispositions are documentary (DNI-as-ApprovalRule ×2, documented-
  hygiene ×2): forcing code status entries would imply future ApprovalRule
  activation that must never happen (RULE_LOGIC rows, non-approval
  targets). Zero pack/engine/fact changes; semantic owners already hold
  each item.
- Checks: 2239 passed (11 new closure tests), ruff clean, no frontend
  change. Counts unchanged. Artifact:
  `docs/audits/audit_mh_remaining_hygiene_closure.md`.

## 68. P0 APR-001 Exception-Role Semantic Design (2026-09-29, design-only)

- Finding: `ApprovalRule` has one polarity — any TRUE aggregates
  (`summarize_by_approval` APPLIES-first) to "approval applies" and flows
  via `_determine_status` to READY and the handoff gate. Exemption TRUE
  (R-002/R-030/R-043/R-044/R-087, all live + test-pinned) reads as
  approval APPLIES; exemption FALSE reads as DOES_NOT_APPLY (fail-OPEN);
  trigger+exemption-UNKNOWN reads as APPLIES (defeater invisible).
- Contract: roles TRIGGER (default) / EXEMPTION / CLASSIFICATION with an
  explicit approval function — non-trigger outputs never APPLIES;
  TRIGGER+EXEMPTION-TRUE → reasoned DOES_NOT_APPLY (sole TRUE→negative);
  TRIGGER+EXEMPTION-UNKNOWN → CONDITIONAL; CLASSIFICATION consumed only
  by named composition (R-003 pattern); GUARD/ROUTING/LIFECYCLE/WORKFLOW
  stay out; defeat ≠ grant downstream; UNKNOWN never FALSE.
- Options (unranked): A — role field + approval composition (one model +
  one aggregator; needs explicit-role lint); B — facet layer + outcome
  mapping (safe by construction; second registry + mapping DSL + drift
  risk). Minimum decision: home of role information + frozen truth table.
- Backward compat: all pure triggers unchanged; deliberate re-pins only
  for R-002 (→CLASSIFICATION), R-030/R-043/R-044/R-087 (→EXEMPTION),
  R-077 (split or grandfathered); GJ byte-identical by default.
- Migration order: R-043 first → APR-001 → readiness verify → rest; TDD
  truth table before code; R-001/R-054 stay deferred throughout.
- Zero production changes in this task. Design:
  `docs/audits/audit_mh_apr001_exception_role_design.md` (18 sections).

## 69. P0 Exception-Semantics Implementation (2026-09-29)

- Implemented: `RuleRole` + `role` (TRIGGER default) on `ApprovalRule`,
  `ApprovalComposition` records, `compose_approval_evaluations` truth
  table wired through role-aware `summarize_by_approval` (opt-in per
  approval; legacy priority otherwise byte-identical), served via
  `RegulatoryPack.approval_compositions` through orchestration/whatif/
  handoff/regulatory paths.
- Migrated: R-043 → EXEMPTION (APR-043 with triggers R-044/R-077;
  TRUE-alone never APPLIES, defeat reasoned, UNKNOWN blocks);
  R-002 → CLASSIFICATION (APR-001 triggerless → honest
  INSUFFICIENT_DATA, never APPLIES/DNA). R-001/R-054 stay deferred.
- Deliberate re-pins (defect fixes): api_e2e APR-001, EC-core
  small/large approval verdicts, derivation-wiring orchestration/handoff/
  whatif/impact APR-001/APR-043 verdicts, consistency/SLA and
  sources/portals APR-001 verdicts (rule-level APPLIES + provenance
  intact everywhere). R-030/R-044/R-087/R-035/R-077 explicitly
  unmigrated.
- Checks: 2225 passed (56 new contract/migration/readiness tests),
  ruff clean, no facts/sources added, GJ byte-identical, counts
  26/61/26/19/128. Record:
  `docs/audits/implementation_mh_exception_semantics.md`.

## 70. R-043 EXEMPTION Migration Audit (2026-09-29, controlled audit)

- Verdict: **SAFE_WITH_LIMITATION** — all 8 truth-table positions live-
  verified (TRUE-alone never APPLIES; FALSE-alone never DNA; T+T→reasoned
  DNA; T+F→APPLIES; T+U→CONDITIONAL; U+T/U+U→INSUFFICIENT); fail-open
  defects dead in every path (2 production summarize sites composed;
  obligations client uncalled in UI; whatif/impact/handoff forward
  compositions); readiness/handoff proven (never READY via exemption;
  obtained = workflow `approved` only; gate raises pre-lookup).
- Limitation (precise): sibling R-044 domestic limb still trigger-
  composed → domestic-only cases overstate duty (fail-safe direction);
  scoped future migration, not this audit.
- Integrity: interpretation-only change (rule-level pins green
  unmodified); 128 facts, T1 evidence, DOC-012 deferred-loaded split
  preserved. APR-001 gate: OPEN (separate task; R-002 CLASSIFICATION
  production-safe as audited).
- Checks: 2228 passed (3 dependency-footprint tests added), ruff clean,
  counts unchanged. Record:
  `docs/audits/audit_mh_r043_exception_migration.md`.

## 71. R-044 Controlled EXEMPTION Migration Audit (2026-09-29)

- Verdict: **SAFE_TO_RETAIN** — R-044 (CGWA domestic groundwater exemption)
  migrated from TRIGGER to EXEMPTION in `APR-043` composition (triggers `["R-077"]`,
  exemptions `["R-043", "R-044"]`).
- Semantic integrity: raw predicate unchanged; R-044 TRUE alone yields
  `insufficient_data` (never APPLIES); TRUE+TRUE defeats trigger R-077 with
  statutory reason; TRUE+UNKNOWN yields CONDITIONAL (non-READY); readiness and
  handoff gates proven closed; DEP-009 dependency isolation preserved.
- Staged state: R-002 is CLASSIFICATION, R-043 and R-044 are EXEMPTION;
  R-030/R-087/R-035/R-077 remain unmigrated TRIGGER; R-054 deferred.
- Checks: 2287 passed (39 dedicated tests added in test_mh_r044_exemption.py), ruff clean, counts unchanged (26/61/26/19/128).
  Record: `docs/audits/audit_mh_r044_exemption_migration.md`.

## 72. Maharashtra End-to-End API Verification & Demo Readiness (2026-09-29, audit-only)

- Audited 11-step PS 26130 sequence end-to-end against live API routes: Project → Facts → Application → Applicability → Summary → Dependencies → Readiness → Documents → Explanation → What-If → Handoff.
- Results: 9 PASS, 2 PARTIAL (legacy standalone `POST /approvals/evaluate` unmigrated to RegulatoryPack; regulatory explanation endpoints lack seeded MH sources in DB and `orchestration_citations` omits persisted-pack threading). Zero BLOCKED. Zero NOT_IMPLEMENTED.
- Core pipeline demonstrated end-to-end: What-If and Orchestration share the same composed pack, handoff enforces strict readiness gates (non-ready blocked with 409; ready initiates to handed_off), and zero Gujarat data leaks into IN-MH.
- Zero code changes, zero rule semantics modified. Artifact: `docs/audits/audit_mh_e2e_demo_readiness.md`.

## 73. R-030 Petroleum Class-B Exemption Migration Audit (2026-09-29, controlled audit)

- **Verdict**: **STOP_UNSAFE_TO_MIGRATE (RETAIN UNMIGRATED / REQUIRE TRIGGER ENCODING)**.
- **Approval ID Disambiguation**: Prompt candidate `APR-024` does not exist in any dataset. True statutory target of `R-030` is `APR-026` (*Petroleum storage licence Form XII/XIII District Authority + Form XV/XVI PESO + Rule 144 NOC*, authority `AUT-008/AUT-009`).
- **Sibling Rule Disambiguation**: `R-087` is `BOILER_EXISTING` (`F-BLR-07 == 'REGISTERED_UNDER_1923_ACT'`) for `APR-023` (*Boiler registration*, *Boilers Act 2025* s.45(2)(f)), entirely unrelated to petroleum. Its grouping with `R-030` in the audit prompt derived from a clerical error in §14 of `audit_mh_r044_exemption_migration.md`. `R-087` remains untouched in `APR-023`.
- **Missing Trigger Finding**: `R-030` is the **sole** active rule targeting `APR-026`; no active statutory trigger rule for the general petroleum storage obligation (*Petroleum Act 1934* s.3(2)) is encoded. Candidate rules `R-029` (DNI), `R-031` (unencoded), `R-032/R-092/R-100` (all deferred) provide no live trigger.
- **Invariant Preserved**: Migrating `R-030` to `EXEMPTION` with `triggers=[]` would collapse `compose_approval_evaluations` to `INSUFFICIENT_DATA` for all inputs, erasing the licence duty for high-volume petroleum facilities and breaking downstream e2e contracts. Section 5 / Criterion 3 mandate `triggers MUST remain non-empty` — violation confirmed; migration halted.
- **Safety Tests**: 38 dedicated tests in `backend/tests/test_mh_r030_exemption.py` — predicate boundaries (A–H), fail-open, readiness, dependency, handoff, alternate-path, jurisdiction isolation, hypothetical 8-row truth table (all correct when a trigger exists). All 38 pass.
- **Staged State**: R-002 CLASSIFICATION; R-043/R-044 EXEMPTION; R-030/R-087/R-035/R-077 remain unmigrated TRIGGER; R-054 deferred.
- **Prerequisite for Future Activation**: Encode a live petroleum-storage trigger rule (Petroleum Act 1934 s.3(2)), associate with `APR-026`, then migrate `R-030` to `EXEMPTION` with composition `ApprovalComposition(approval_id="APR-026", triggers=[trigger_id], exemptions=["R-030"])`.
- **Exact Next Migration**: R-087 (*Boilers Act 2025* s.45(2) deemed registration) under `APR-023`, where active sibling triggers `R-028`, `R-073`, `R-086` already exist.
- **Checks**: 2325 passed (38 new), ruff clean, TypeScript clean; active pack 26, deferred 61, facts 128 unchanged; GJ byte-identical.
- Record: `docs/audits/audit_mh_r030_exemption_migration.md`.







## 74. Closure: T3 frontend journey + T4 R-087 + T5 citations reconciled (2026-10-02)

- T3: MH demo drivable through the UI (explicit IN-MH creation via optional
  validated `requested_jurisdiction` on `POST /projects`; embedded
  `{"facts_json"}` body contract; `GET approval-codes` pack projection;
  code-linked `POST /applications`; MH facts editor + assessment dashboard
  + applicant per-approval cards + custom-fact What-If + truthful handoff).
  Additive migration 013 (`approval_handoffs.portal_kind`) fixed live
  handoff drift. Zero rule/role/composition/evidence changes.
- T4: R-087 TRIGGER?EXEMPTION + APR-023 composition
  (triggers R-028/R-073/R-086). R-030 stays TRIGGER, APR-026 uncomposed.
- T5: pack-backed same-jurisdiction citations + persisted-pack
  orchestration citations; DB sources stay GJ-only by design.
- T6 stays BLOCKED (no verified staging target; local DB reference-only).
- Final: 26 active / 61 deferred / 11 confirmation-only / 3 DNI /
  4 hygiene-terminal (105); roles TRIGGER 22 / EXEMPTION 3 / CLASSIFICATION 1;
  compositions APR-001/APR-043/APR-023; GJ 19 rules, no compositions,
  DEFAULT_JURISDICTION IN-GJ. Backend 2467 green; tsc/build clean.
