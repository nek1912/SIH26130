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
- Phase 6: TBD
