# PRD — Gujarat Industrial Approval Intelligence MVP

## Problem
For a selected Gujarat chemical-manufacturing scenario, an applicant must understand which approvals may apply, why they apply, what is needed, what is blocked, what can proceed, and what action is next.

## Users
- Applicant/industrial entrepreneur
- Demo officer/reviewer
- Admin/data maintainer

## MVP outcome
Given a structured project profile, generate a traceable approval journey for a deliberately small, verified Gujarat dataset.

## MVP features
1. Project profile and dynamic questions.
2. Project-specific approval applicability: Applicable / Not applicable / Conditional / Unknown.
3. Reason for every recommendation: triggered facts + rule + source.
4. Approval dependency graph and readiness/blocking status.
5. Document checklist and upload.
6. Basic document extraction and validation.
7. Cross-document inconsistency flags.
8. Approval application workflow: draft, submitted, scrutiny, query, response, inspection, decision.
9. SLA tracking using researched clock rules.
10. Source-cited regulatory RAG assistant.
11. Small incentive eligibility section only if authoritative data is collected.
12. Audit history for material changes.

## Explicit non-goals
- Full Gujarat coverage.
- All sectors/departments/clearances.
- Real integration with every government portal.
- Automated legal determinations.
- ML processing-time prediction.
- General-purpose risk scoring.
- Complete grievance platform.
- Nationwide regulatory crawling.

## Demo scope
Use one narrow chemical-industry scenario and a small verified approval set. The exact sector/product/location/capacity and approval list are DATA decisions and must not be invented in code before the research dataset is frozen.

## Key acceptance tests
A demo case must be able to:
- create a project,
- produce a non-static approval result,
- show why at least one approval was triggered,
- show an INSUFFICIENT_DATA case when required facts are missing,
- expose at least one dependency/blocker,
- detect at least one document inconsistency,
- show an approval moving through a realistic workflow,
- show an SLA based on the researched rule,
- answer a regulatory question with a source citation.

## Quality bar
A feature is rejected if it is only a visually attractive CRUD screen with no domain logic, or if it presents unverified regulatory assumptions as fact.

## Current status
- Tech direction locked: React + TypeScript + Vite + Tailwind, FastAPI, Supabase.
- Source repositories deleted after extraction — all necessary logic ported to Python.
- **Key finding**: Business logic must be rewritten in Python (not copy-pasted). Frontend must be extracted from Next.js into Vite SPA.
- Gujarat regulatory dataset: not yet collected/frozen.
- **Phase 1 complete (2026-09-14)**: Backend foundation with 12-table SQL schema, all pure logic engines ported to Python, 119 tests passing.
- **Phase 2A complete (2026-09-14)**: FastAPI API routes + Supabase data access layer, 137 tests passing.
- **Phase 2B complete (2026-09-14)**: Supabase Auth integration — JWT verification, RBAC enforcement, ownership checks, 185 tests passing.
- **Phase 2C complete (2026-09-14)**: Workflow foundation — transition engine, stage definitions, 22 transition rules, role enforcement, audit trail, 253 tests passing.
- **Phase 3A complete (2026-09-14)**: Frontend foundation — Vite + React + TypeScript + Tailwind v4 SPA, Supabase Auth, API client, protected routes, applicant flow (projects, applications), staff application detail with workflow actions, 253 backend tests passing.
- **Phase 3B complete (2026-09-14)**: Staff workflow UI — `GET /applications` endpoint with filters/pagination, staff queue with real data and status filter, staff application detail with workflow actions and error handling, applicant status timeline and project facts editing, 263 backend tests passing.
- **Phase 4 complete (2026-09-15)**: Dependency engine — approval dependency graph, readiness/blocking status, cycle detection, topological sort, stage assignment, 3 verified MVP dependencies (A02←A04, A03←A04, A03←A02), 41 dependency engine tests, full integration with applicability layer, 402 backend tests passing.
- **Phase 3C complete (2026-09-15)**: Document management foundation — 17 workbook document requirements (D01-D17), upload with MIME/size validation, Supabase Storage integration (backend-proxied), readiness tracking (pending/uploaded/valid/invalid/review_required), audit trail, frontend document checklist, auto-seed on application creation, 458 backend tests passing. Settings `extra = "ignore"` fix resolved 23 pre-existing Supabase config test failures.
- Next engineering step: Phase 5 — Document extraction/OCR, consistency engine, SLA display.
