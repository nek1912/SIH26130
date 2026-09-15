# Engineering & Agent Rules

## Regulatory correctness
1. Never invent approval names, authorities, legal thresholds, SLAs, exemptions, prerequisites, or deadlines.
2. Regulatory data is untrusted until the team records the official source and effective/version information.
3. If the facts are insufficient, return `INSUFFICIENT_DATA` rather than guessing.
4. AI output must not be represented as a statutory determination.
5. Every user-visible regulatory claim must be traceable to a stored source.

## Codebase
1. Reuse existing code before creating new infrastructure.
2. Prefer the smallest change that satisfies the requirement.
3. Do not duplicate functionality already present in the adopted base repository.
4. Do not mix competing frameworks/libraries for the same responsibility.
5. Keep domain logic testable and independent of UI code.
6. No direct database access from React.
7. FastAPI owns business logic and privileged operations.

## Dependencies & versions
1. Use current stable APIs from official documentation at implementation time.
2. Do not copy old tutorials that use deprecated APIs/configuration.
3. Before adding a dependency, verify it is maintained, compatible with the current stack, and actually necessary.
4. Lock reproducible dependency versions after verification; do not use floating versions in committed lockfiles/config where the package manager supports locking.
5. Prefer official CLI/setup methods (for example current Vite/Tailwind/FastAPI guidance) over legacy scaffolding.

## Security
1. No secrets, service-role keys, passwords, tokens, or private URLs in Git.
2. Treat uploaded documents as untrusted input.
3. Validate authorization server-side on every protected operation.
4. Do not trust client-supplied ownership, role, status, or approval decisions.
5. Keep audit history append-only from the application perspective.

## API
1. Use REST and FastAPI-generated OpenAPI.
2. Use Pydantic schemas for request/response validation.
3. Return predictable error structures.
4. Do not expose internal database models directly when the API contract needs a stable domain schema.

## Testing
At minimum test:
- applicability rule boundaries,
- INSUFFICIENT_DATA cases,
- approval dependencies,
- SLA clock behaviour,
- document validation,
- authorization/RLS-sensitive paths,
- query/status transitions.

## AI/RAG
1. Retrieval must be source-aware and version-aware.
2. Citations must correspond to retrieved material.
3. Never fill missing regulatory facts with model knowledge.
4. Log enough evidence to reproduce why an answer was produced.
5. Do not add agents, tools, model providers, rerankers, or vector stores without measurable need.

## Migration reality
The source repos (Digital-Permit-Platform, Compliance-Grid) were TypeScript/Next.js full-stack. All necessary business logic has been rewritten in Python and ported to the FastAPI backend. Those repositories have been deleted. Do not reference them as runtime dependencies.

## Backend structure (Phase 3C)
`backend/app/` contains:
- `rules/` — obligation models, applicability engine, approval applicability engine, deadline, canonical, validation, **dependency models, dependency engine** (pure logic)
- `forms/` — form models, condition evaluator (pure logic)
- `workflow/` — status models, SLA, stage definitions, transition engine, assignments (pure logic)
- `audit/` — audit entry/record (pure logic)
- `auth/` — RBAC permissions, UserContext model, JWT verification, FastAPI auth dependencies
- `core/` — config with Pydantic BaseSettings (includes JWT settings, storage bucket)
- `db/` — Supabase client factory (`get_supabase()` with lru_cache)
- `repositories/` — database access layer (base CRUD + specialized repos, including `documents.py`)
- `api/` — FastAPI routes with auth dependencies (health, projects, approvals, applications, workflow, **documents**)
- `seed/` — workbook scenario, approval rules, dependency edges, **document requirements**, expected results
- `main.py` — FastAPI app with all routers

Tests in `backend/tests/`. Run with `cd backend && python -m pytest tests/ -v`. Lint with `python -m ruff check app/ tests/`.

## Frontend structure (Phase 3B)
`frontend/src/` contains:
- `lib/supabase.ts` — Supabase client initialization (env vars: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
- `lib/api.ts` — Thin REST API client (fetch wrapper with auth injection, all backend endpoints mapped)
- `types/api.ts` — TypeScript types matching backend API response shapes (14 ApplicationStatus values)
- `contexts/AuthContext.tsx` — Auth provider (session, role, signIn, signOut)
- `components/ProtectedRoute.tsx` — Auth guard with role-based access
- `components/layout/` — Sidebar, Topbar, AppLayout (responsive sidebar + topbar)
- `components/ui/` — Button, Input, Label, Card, Badge (Tailwind v4 compatible)
- `components/shared/` — StatusBadge (14 application statuses), LoadingSpinner
- `pages/auth/LoginPage.tsx` — Email/password login
- `pages/applicant/` — ProjectList, ProjectCreate, ProjectDetail (with facts editing), ApplicationList, ApplicationSubmit, ApplicationDetail (with status timeline)
- `pages/staff/` — QueuePage (real data, filters, pagination), ApplicationDetail (with workflow actions)
- `app.css` — Tailwind v4 CSS-first config with OKLCH design tokens

Run frontend checks: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`

## Agent context discipline
At the start of every new session, read `AGENTS.md`, `ARCHITECTURE.md`, `RULES.md`, and `PRD.md` before editing.

At the end of every task, review all four files and update changed facts/status/decisions. Keep them short. Do not add narrative history; keep only information a future agent needs.

When uncertain:
- inspect the repository,
- inspect current official documentation,
- inspect tests/types,
- then ask for clarification if the requirement still cannot be determined.

Do not guess.
