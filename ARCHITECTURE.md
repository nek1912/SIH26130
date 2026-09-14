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
- `APPLICABLE`
- `NOT_APPLICABLE`
- `CONDITIONAL`
- `UNKNOWN`

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
- `app/rules/models.py` — Obligation, ApplicabilityCondition, DeadlineRule, EntityProfile, Instrument, Source, Frequency, Penalty, ObligationCandidate (Pydantic v2)
- `app/rules/engine.py` — `evaluate_applicability()` deterministic filter
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
- 119 tests across 8 test files, all passing
- Coverage: applicability, deadline, canonical, validation, conditions, SLA, permissions, audit, models

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
- No workflow_events table persistence yet (events created in-memory)
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
