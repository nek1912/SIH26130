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
11. Small incentive eligibility section only if authoritative data is collected. **(Implemented: 6 verified GIP 2020 schemes)**
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
- **Phase 3D complete (2026-09-15)**: Document extraction & deterministic validation — structured extracted-field storage, extraction status/error tracking, deterministic extraction for PDF/CSV/Excel, validation rules per document domain (11 domains), explicit outcomes (VALID/INVALID/REVIEW_REQUIRED/INSUFFICIENT_DATA), source/rule traceability, field-level findings, 5 API endpoints, frontend extraction/validation status display, 500 backend tests passing.
- **Phase 3E complete (2026-09-15)**: Cross-document consistency engine — 18 workbook consistency rules (C01-C18), deterministic field comparison across documents, seed config mapping canonical fields to document keys, persistence in consistency_results/findings tables, 2 API endpoints, frontend consistency section with Run Check button and findings table, 27 new tests, 527 backend tests passing.
- **Phase 5 complete (2026-09-15)**: SLA display + background extraction — workflow events persistence, GET /applications/{id}/sla endpoint, background extraction on upload via FastAPI BackgroundTasks, extraction status (pending/running/completed/failed/unsupported) on documents, SLA status card on applicant and staff pages, idempotent extraction with error handling, 11 new tests, 538 backend tests passing.
- **Phase 6 complete (2026-09-16)**: Orchestration / Readiness — deterministic orchestration service combining applicability + dependency + documents + extraction + validation + consistency + SLA into per-approval readiness with explainable blockers, OrchestrationStatus (7 states), BlockerDetail with full traceability, next-action computation, GET /applications/{id}/orchestration endpoint, ReadinessCard on both staff and applicant detail pages, 20 new tests, 558 backend tests passing.
- **Phase 7 complete (2026-09-16)**: Official-Source RAG & Regulatory Explanation — 32 verified Gujarat regulatory sources (S01-S32) seeded from workbook, PostgreSQL tsvector full-text search with GIN indexes, template-based source-grounded explanations (no LLM), citation generation with source metadata, 6 API endpoints (sources CRUD, explain, explain approval, orchestration citations), RegulatoryAssistant component on detail pages, 67 new tests, 625 backend tests passing.
- **Phase 8 complete (2026-09-16)**: Government Support & Incentive Intelligence — 6 verified Gujarat incentive schemes from GIP 2020 (MSME capital/interest subsidy, large industry capital subsidy, electricity duty exemption, power connection charges, quality certification), deterministic eligibility engine reusing existing condition tree evaluator, 4 relevance states (potentially_relevant/not_relevant/conditional/insufficient_data), source traceability to S33 (GIP 2020 official PDF), 3 API endpoints (list/get/assess), IncentiveSchemes component on both applicant and staff detail pages, 37 new tests, 662 backend tests passing.
- **Phase 9 complete (2026-09-16)**: End-to-end integration — orchestration endpoint wired to fetch extraction/validation/consistency/SLA from DB, obtained_approvals computed from sibling applications, ~350 lines of frontend duplication eliminated via shared components (SLACard, DocumentChecklist, ConsistencyPanel, OrchestrationPanel), consistency API normalized (path params, DI, deprecated datetime), permission mismatches fixed, dead code removed, frontend polish (SLA/orchestration re-fetch after workflow action, consistency error feedback), 8 new integration tests, 665 backend tests passing.
- **Maharashtra Location Cluster (2026-09-28)**: R-077 (CGWA OE), R-083 (CRZ), R-084 (Forest), R-096 (HW Sch II) encoded in IN-MH pack (26 rules total); R-091 partially implemented via derive_mah_status(); R-060, R-061, R-085 gated and deferred with verified reasons. 1263 backend tests passing.
- **Maharashtra Planning & Fire Cluster (2026-09-28)**: R-041, R-078, R-079, R-080, R-082 audited across 20 evidence dimensions; all 5 gated and deferred in MH_DEFERRED_RULES (25 total deferred) fail-closed; active pack unchanged at 26 rules; 1285 backend tests passing.
- **Maharashtra Environmental / Consent Cluster (2026-09-28)**: R-003, R-004, R-007, R-008, R-013, R-014 audited across 20 evidence dimensions; R-007 verified already active; R-003, R-004, R-008, R-013, R-014 gated and deferred in MH_DEFERRED_RULES (30 total deferred); active pack unchanged at 26 rules; 1314 backend tests passing.
- **Maharashtra Labour & Factory Establishment Cluster (2026-09-28)**: R-019, R-020, R-027, R-022, R-023, R-090 audited across 20 evidence dimensions; all 6 gated and deferred in MH_DEFERRED_RULES (35 total deferred) fail-closed; active pack unchanged at 26 rules; 1342 backend tests passing.
- **Maharashtra Utilities, Water & Power Cluster (2026-09-28)**: R-038, R-048, R-052, R-053, R-097 audited across 20 evidence dimensions; all 5 gated and deferred in MH_DEFERRED_RULES (40 total deferred) fail-closed; active pack unchanged at 26 rules; 1374 backend tests passing.
- **Maharashtra Safety, Hazardous Chemicals & Transport Cluster (2026-09-29)**: R-030, R-032, R-033, R-034, R-035, R-062, R-092 audited across 20 evidence dimensions; R-030 and R-035 active status verified; R-032, R-033, R-034, R-062, R-092 gated and deferred in MH_DEFERRED_RULES (45 total deferred) fail-closed; prompt label mismatches resolved (R-032 is Petroleum routing, not GCR; R-033 is GCR Form F exemption, not SMPV; R-034 is SMPV definition; R-035 is MIDC branch guard, not factory safety; R-062 is CTO validity, not Biomedical Waste which is inapplicable to chemical domain); active pack unchanged at 26 rules; 1410 backend tests passing.
- **Maharashtra Sector-Specific Approvals / Clearance Pack Cluster (2026-09-29)**: R-051, R-068, R-069, R-095, R-105 audited across 20 evidence dimensions; all 5 gated and deferred in MH_DEFERRED_RULES (50 total deferred) fail-closed; active pack unchanged at 26 rules; 1449 backend tests passing.
- Next engineering step: Maharashtra Next Rule Cluster / Milestone.

