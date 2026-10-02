# Engineering & Agent Rules

## Regulatory correctness
1. Never invent approval names, authorities, legal thresholds, SLAs, exemptions, prerequisites, or deadlines.
2. Regulatory data is untrusted until the team records the official source and effective/version information.
3. If the facts are insufficient, return `INSUFFICIENT_DATA` rather than guessing.
4. AI output must not be represented as a statutory determination.
5. Every user-visible regulatory claim must be traceable to a stored source.
6. Persisted jurisdiction/pack identity is authoritative: an existing application's (`jurisdiction`, `pack_version`) pair — never the global default — determines its RegulatoryPack. See `docs/architecture/persisted-jurisdiction-design.md`.

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

## Evidence boundary (G0-R5)
1. Unresolved regulatory facts live in `app/regulatory/evidence.py` (`EvidenceStatus`: VERIFIED / PARTIAL / NOT_ESTABLISHED / CONFLICTING) and `app/seed/evidence_gaps.py` (12 G0-R5 records, cut-off 25.09.2026).
2. Only VERIFIED evidence may back applicability rules — enforce with `require_verified()` / `is_encodable()`. PARTIAL, NOT_ESTABLISHED, and CONFLICTING records must fail closed to INSUFFICIENT_DATA.
3. Never create applicability rules, thresholds, authorities, SLAs, exemptions, or legal conclusions from gap records. In particular, never map "no groundwater extraction" to "no NOC" (G0R5-GW-NO-EXTRACTION stays NOT_ESTABLISHED).
4. Orchestration surfaces relevant gaps via `evidence_gaps_to_blockers()` (opt-in `evidence_gaps` / `evidence_gaps_by_approval` params; NOT_APPLICABLE is preserved). The orchestration endpoint opts in per assessed approval via `get_gaps_for_approval()` hints. Gap blockers carry structured traceability (`evidence_id`, `evidence_status`, `unresolved_question`). Default behaviour without gaps is unchanged.

## Migration reality
The source repos (Digital-Permit-Platform, Compliance-Grid) were TypeScript/Next.js full-stack. All necessary business logic has been rewritten in Python and ported to the FastAPI backend. Those repositories have been deleted. Do not reference them as runtime dependencies.

## Backend structure (Phase 9 + G0-R5)
`backend/app/` contains:
- `rules/` — obligation models, applicability engine, approval applicability engine, deadline, canonical, validation, **dependency models, dependency engine** (pure logic)
 - `rules/facts.py` — **jurisdiction-scoped fact registry**: 128 code-defined IN-MH facts (transcribed from the v5 facts artifact; F-BLD-02 excluded as do-not-implement), typed validation (boolean/integer/number/string/date/enum/enum-set/list/object), `None`-is-missing semantics, jurisdiction-mismatch detection. IN-GJ keeps the legacy `validation.ALLOWED_FIELDS` path.
 - `rules/derivations.py` — **IN-MH derived facts only**: `derive_msme_class()` (F-INC-01 ← F-INC-02 + F-INC-09, R-057 bands, AND per band), `derive_mah_status()` (F-PRC-03 ← F-HAZ-01 + F-HAZ-02, R-091 join semantics), `derive_mh_facts()` (fills absent keys only, never overrides, IN-GJ rejected). F-INC-03/F-INC-04 blocked by insufficient evidence (never produced). Wired once via `orchestration/facts.py::apply_derived_facts` in `_load_baseline_inputs` (merged `inputs["facts"]` + `inputs["fact_provenance"]`); What-If strips provenance keys before overrides and re-derives the alt branch; provenance exposed as `ApplicationOrchestration.fact_provenance` (`FactProvenance`: fact_id/derived/derivation/source_facts/value; unlisted = supplied). No persistence, no batch-2 rules.
- `forms/` — form models, condition evaluator (pure logic)
- `workflow/` — status models, SLA, stage definitions, transition engine, assignments (pure logic)
- `audit/` — audit entry/record (pure logic)
- `auth/` — RBAC permissions, UserContext model, JWT verification, FastAPI auth dependencies
- `core/` — config with Pydantic BaseSettings (includes JWT settings, storage bucket)
- `db/` — Supabase client factory (`get_supabase()` with lru_cache)
- `repositories/` — database access layer (base CRUD + specialized repos, including `documents.py`, **`consistency.py`**, **`workflow_events.py`**, **`sources.py` with search/chunk methods**)
- `api/` — FastAPI routes with auth dependencies (health, projects, approvals, applications, workflow, **documents**, **extraction**, **consistency**, **orchestration**, **regulatory**, **incentives**)
- `extraction/` — extraction models, service (PDF/CSV/Excel), deterministic validation engine, **background extraction job**
- **`consistency/`** — cross-document consistency models and deterministic comparison engine
- **`orchestration/`** — readiness/blocking status combining all engines into per-approval assessments with explainable blockers, **plus opt-in G0-R5 evidence-gap surfacing as INSUFFICIENT_DATA**
- **`regulatory/`** — RAG models, ingestion, retrieval (tsvector full-text search), template-based explanation engine, **evidence boundary (`evidence.py`: VERIFIED/PARTIAL/NOT_ESTABLISHED/CONFLICTING + fail-closed guards)**
- **`incentives/`** — government support/incentive scheme models, deterministic assessment engine (reuses applicability engine)
 - `seed/` — workbook scenario, approval rules, dependency edges, **document requirements**, **consistency rules**, **regulatory sources (32)**, **incentive schemes (6)**, **G0-R5 evidence gaps (12)**, expected results
    - `seed/pack.py` — **sole jurisdiction-aware regulatory boundary**: `load_regulatory_pack("IN-GJ"|"IN-MH")` returns a `RegulatoryPack` (rules, authorities, dependencies, documents, consistency, incentives, sources, evidence gaps+hints, portal catalog). API layers consume packs, never individual seed loaders. `DEFAULT_JURISDICTION = "IN-GJ"` is the single cutover point, resolved per-request via the `get_active_jurisdiction` dependency (constant in production; overridable only in tests — no client-controlled selector). IN-MH carries batch-1 + batch-2 + location-cluster safe-only v5 rules (`seed/mh/approvals.py`: 26 encoded, 56 deferred with reasons, ROC/DNI/UNKNOWN excluded by construction) plus batch-1 dependencies (`seed/mh/dependencies.py`: DEP-009 ×2, 33 triaged), documents (`seed/mh/documents.py`: DOC-001/002/003/008, 8 deferred), advisory evidence (`seed/mh/evidence.py`: UR-06/UR-11/DOC-012 with approval hints), the batch-1 + batch-2 + location-cluster referenced source corpus (`seed/mh/sources.py`: 22/188), the batch-1 portal catalog (`seed/mh/portals.py`: 14 entries, portal/reference only, no MAITRI), and batch-1 SLA display metadata (`seed/mh/slas.py`: 10 rows, target/outer never merged, UNKNOWN preserved, no computation). Consistency is explicitly empty (no v5 consistency records exist for batch-1 documents).
- `main.py` — FastAPI app with all routers

Tests in `backend/tests/`. Run with `cd backend && python -m pytest tests/ -v`. Lint with `python -m ruff check app/ tests/`.

## Frontend structure (Phase 9)
`frontend/src/` contains:
- `lib/supabase.ts` — Supabase client initialization (env vars: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)
- `lib/api.ts` — Thin REST API client (fetch wrapper with auth injection, all backend endpoints mapped including **orchestration**, **regulatory**, **incentives**)
- `types/api.ts` — TypeScript types matching backend API response shapes (14 ApplicationStatus values, **ApplicationOrchestration**, **OrchestrationStatus**, **Source**, **Citation**, **RegulatoryExplanation**, **SupportScheme**, **ProjectIncentiveAssessment**)
- `contexts/AuthContext.tsx` — Auth provider (session, role, signIn, signOut)
- `components/ProtectedRoute.tsx` — Auth guard with role-based access
- `components/layout/` — Sidebar, Topbar, AppLayout (responsive sidebar + topbar)
- `components/ui/` — Button, Input, Label, Card, Badge (Tailwind v4 compatible)
- `components/shared/` — StatusBadge (14 application statuses), LoadingSpinner
- `pages/auth/LoginPage.tsx` — Email/password login
- `pages/applicant/` — ProjectList, ProjectCreate, ProjectDetail (with facts editing), ApplicationList, ApplicationSubmit, ApplicationDetail (with status timeline, **readiness card**, **regulatory assistant**, **incentive schemes**)
- `pages/staff/` — QueuePage (real data, filters, pagination), ApplicationDetail (with workflow actions, **readiness card**, **regulatory assistant**, **incentive schemes**)
- `pages/shared/` — **RegulatoryAssistant** (search + citation display), **IncentiveSchemes** (eligibility assessment), **SLACard**, **DocumentChecklist**, **ConsistencyPanel**, **OrchestrationPanel**
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
