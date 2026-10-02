# Audit: MH Frontend Journey (T3)

Date: 2026-10-02. Baseline: commit `74023c4` (2348 passed). This task is
integration-only: no rule, predicate, evidence, role, composition,
threshold, source, default-jurisdiction, or GJ-legacy change.

## 1. Previous UI state

- Project creation stamped the server default (IN-GJ) with no selector.
- Facts form was GJ-only (5 flat fields); `api.projects.upsertFacts`
  serialized the payload into the URL query string, so the backend's
  `facts_json` Body was never populated — MH F-* facts could not be saved.
- `api.applications.create` never sent the backend-required
  `approval_code` query param, so UI-driven application creation 422d.
- `WhatIfPanel.SUPPORTED_FIELDS` was a closed GJ-only allowlist; any F-*
  override was rejected client-side (`Unsupported field`).
- Applicant `OrchestrationPanel` rendered blockers only (no per-approval
  applicability/status cards); staff view already had them.
- No MH vocabulary, jurisdiction badges, or pack-driven approval picker.

## 2. Actual gaps found (traced UI → client → endpoint → state)

1. **Facts contract**: `POST /projects/{id}/facts` declares
   `facts_json: dict | None = Body(default=None)` alongside the complex
   query param `jurisdictions: list[str]`. Bisected with vanilla FastAPI
   probes: any sibling complex query param forces body-field embedding,
   so the client must send `{"facts_json": {...}}` — a bare-dict body is
   silently dropped to `None` (proven: 200 with empty payload, no error).
   The old query-string client therefore never stored MH facts.
2. **No IN-MH creation path**: `get_active_jurisdiction()` is a
   production constant (IN-GJ); projects stamped server-side only.
3. **No pack code listing**: `GET /approvals` serves DB catalog rows
   (GJ A-codes); MH APR-xxx codes had no endpoint, forcing hardcoding.
4. **Application FK**: `applications.approval_id` is `NOT NULL REFERENCES
   approvals(id)`; MH APR codes have no pre-seeded catalog rows, and
   `approval_id` was a required API param.
5. **Live handoff drift (found during live verification)**:
   `prepare_initiation` persists `portal_kind`, but migration 009 never
   created the column — `POST .../handoffs/initiate` raised
   `UndefinedColumn` on a real DB while mocked tests stayed green.

## 3. Files changed

Backend (contract-only; zero regulatory-semantics edits):
- `backend/app/api/projects.py` — `POST /projects` accepts optional,
  strictly-validated `requested_jurisdiction` (default path byte-identical);
  new `GET /projects/{id}/approval-codes` (read-only pack projection).
- `backend/app/api/applications.py` — `approval_id` optional; when omitted
  the server links (or inserts a minimal code+authority) catalog row for
  the validated `approval_code`. Explicit-UUID path unchanged.
- `backend/tests/test_api_mh_demo_contract.py` — 13 contract tests.
- `supabase/migrations/013_handoff_portal_kind.sql` — additive
  `portal_kind` column (backfill `'portal'` + CHECK).
- `docs/local-postgres.md`, `scripts/verify_local_db.py` — 013 coverage
  (new `4b portal_kind` check; 9/9 passing).

Frontend (render-only; no rule logic duplicated):
- `frontend/src/lib/api.ts` — jurisdiction on create; `upsertFacts`
  (legacy query + embedded `{"facts_json"}` body); `create` sends
  `approval_code` (+ optional `approval_id`); `getApprovalCodes`.
- `frontend/src/types/api.ts` — jurisdiction/pack_version on Project and
  Application; `facts_json` on ProjectFacts; `code` on Approval;
  `PackApprovalCode(s)` types.
- `ProjectCreatePage` (jurisdiction select, default IN-MH),
  `ProjectListPage` + `ProjectDetailPage` (jurisdiction/pack badges),
  `ApplicationSubmitPage` (pack-code picker for IN-MH; code passthrough
  for GJ rows that carry one).
- New `pages/shared/mhFacts.ts` (37 curated F-* fields + canonical fill
  values mirroring `scenario.py`; empty = unset, never false),
  `MhFactsEditor.tsx`, `MhAssessmentPanel.tsx` (per-code Assess/Open with
  backend overall-status chips).
- `WhatIfPanel` — custom-fact mode (any key + kind + unknown); backend
  remains the sole validator (422s surface verbatim).
- `OrchestrationPanel` — applicant per-approval cards (exact backend
  `applicability_result`/`status` vocabulary, explanation, doc/dep
  readiness, blockers with source_ref/evidence/action).
- `ApplicationDetailShared` + both detail pages — approval_code and
  jurisdiction chips in the header.
- Untouched: RuleRole, compositions, all rules, GJ default, RAG wiring,
  incentives (still GJ GIP-2020 — pre-existing quarantine, out of scope).

## 4. APIs connected

`POST /projects (?requested_jurisdiction)` → `POST /projects/{id}/facts`
(body `{"facts_json"}`) → `GET /projects/{id}/approval-codes` →
`POST /applications (approval_code)` → `GET .../orchestration` →
`POST .../orchestration/what-if` → `GET .../handoffs` →
`POST .../handoffs/initiate|record-submission|report-status|verify` →
documents/consistency/SLA (pre-existing wiring, verified live).

## 5. Canonical MH scenario used

Sahyadri fixture values (`scenario.py`) via "Fill canonical demo values"
(form pre-fill only; submission still validated server-side).

## 6. Journey verification (live DB `gaia_dev`, real HTTP+SQL+engines)

21/21 live checks passed (temp script, rows cleaned up afterwards):
project create IN-MH stamped · 41 canonical facts persisted · 20 codes
projected · APR-010 blocked_by_dependency · APR-026 applies +
blocked_by_documents (DOC-008) · APR-006 ready · APR-001
insufficient_data · exact applicability vocabulary · explanation/docs/
source_refs present · What-If F-PET-02→50000 changes APR-026 with
project facts byte-identical afterwards · READY handoff initiates ·
non-ready handoff 409 (`only READY approvals can be handed off`) · no
GJ leakage in any MH payload · no fabricated sources.

## 7. Step classification

| Step | Verdict |
|---|---|
| Login | PASS (pre-existing) |
| Select/create MH project (explicit IN-MH) | PASS |
| Enter/submit MH facts (incl. canonical fill) | PASS |
| Assessment runs (per-code application) | PASS |
| Approval dashboard (codes + backend statuses) | PASS |
| Applicability states (exact vocabulary) | PASS |
| Approval detail (reason/authority/docs/deps/readiness/source) | PASS — authority shown where backend returns it (handoff ready list); per-approval authority is not in the orchestration model, so none is invented |
| Dependencies render | PASS (readiness + blocker text from backend) |
| Documents render (required/present/missing) | PASS |
| Readiness renders (all 7 states, backend-computed) | PASS |
| Blockers + next action | PASS |
| What-If works, non-mutating | PASS |
| Handoff preparation + non-ready 409 gate | PASS (after 013 fix) |
| No GJ fallback | PASS (explicit errors, jurisdiction chips everywhere) |
| MH RAG citations inline | PARTIAL — belongs to T5; blocker source_refs shown, nothing invented |

## 8. Tests / checks

- Backend `pytest tests/ -q`: **2467 passed, 0 failed** (= 2348 T2 baseline
  + 13 new T3 contract tests + 106 from parallel in-flight T4/T5 work —
  all green together; T3 files untouched by others).
- `ruff` on touched backend files: clean (20 pre-existing E501s in two
  older test files remain, none on touched lines).
- Frontend: `tsc --noEmit` 0 errors; `oxlint` no errors (pre-existing
  warnings only); `vite build` success.
- No frontend test runner exists in the repo (no vitest/jest) — none added
  per §17; API-level live proof above substitutes.
- Regulatory engine untouched: `git diff` on `seed/mh/approvals.py`,
  `rules/`, `regulatory/` (engine), compositions: no T3 edits (concurrent
  T4/T5 modifications to those paths are theirs, not this task's).
- GJ default untouched: `DEFAULT_JURISDICTION = "IN-GJ"`; GJ create/list/
  submit flows preserved (submit additionally forwards catalog codes when
  the DB row carries one, repairing the previously-422 GJ create path).

## 9. Known limitations

- Canonical fill values duplicate `scenario.py` in `mhFacts.ts` (drift risk
  if the fixture changes; submission still validated).
- Concurrent catalog-row insert for the same code can 409/500 on unique
  violation (single-user demo: negligible).
- Incentive panel still serves GJ GIP-2020 schemes on MH projects
  (pre-existing quarantine; needs an MH incentive pack, out of scope).
- `RegulatoryAssistant` free-text search remains GJ-backed (T5 owns MH
  citations); per-approval explain passes the application UUID as before.
- Two parallel workstreams (T4 R-087, T5 citations, T6 staging) are editing
  this same tree concurrently; this task touched none of their files.
