# Audit: Maharashtra Canonical Demo / Rehearsal (P1 parallel)

Date: 2026-10-02. Baseline: HEAD `f2c68d1` (working tree clean at start).
Scope: READ/AUDIT/REHEARSAL ONLY. No rule, role, composition, FactSpec,
GJ-behavior, DEFAULT_JURISDICTION, canonical-fact, R-091, migration-010,
or feature changes made in this task.

Mandate: determine whether the CURRENT implementation can be demonstrated
coherently and honestly using the existing canonical scenario — not to
improve it. R-091 is worked on separately (T7) and was intentionally
excluded: where the scenario touches it, the existing behavior is recorded
without modification.

Context read: AGENTS.md, ARCHITECTURE.md, RULES.md, PRD.md,
`docs/audits/MASTER_MH_IMPLEMENTATION_STATUS.md`,
`backend/app/seed/mh/scenario.py`,
`docs/audits/audit_mh_frontend_journey.md` (T3),
`docs/audits/audit_mh_e2e_demo_readiness.md`,
`docs/audits/audit_mh_rag_citations.md` (T5),
`docs/audits/audit_mh_r087_semantic_migration.md` (T4).

## 1. Environment

- Repo: `D:\SIH`, branch `main`, HEAD `f2c68d1`
  (`feat(mh): complete Maharashtra implementation baseline`).
  `git status --short`: clean (no uncommitted changes before or after;
  this task adds only the audit file itself).
- Backend: `D:\SIH\backend` (FastAPI + Python). No server started, no DB
  written, no migration run. All rehearsal below is in-process engine
  calls + read-only code/route inspection + existing test suites.
- Canonical pack: `load_regulatory_pack("IN-MH")` → 26 rules, 2
  dependencies (DEP-009 ×2), 22 sources, compositions
  `{APR-001, APR-023, APR-043}`. `DEFAULT_JURISDICTION = "IN-GJ"`
  (`backend/app/seed/pack.py:74`) preserved.
- Checks run (non-destructive):
  - `pytest tests/test_mh_canonical_scenario.py
    tests/test_mh_rag_citations.py tests/test_mh_r087_semantics.py
    tests/test_mh_r044_exemption.py tests/test_api_mh_demo_contract.py -q`
    → **181 passed** (this task).
  - `pytest tests/test_mh_canonical_scenario.py -q` → **23 passed**.
  - Ad-hoc in-process rehearsal scripts in
    `C:\Users\nekmp\AppData\Local\Temp\opencode\mh_rehearse*.py`
    (temp only, not committed): orchestration over canonical facts,
    expected-assessment comparison, GJ-leak scan, What-If non-mutation,
    handoff gate, citation resolution, role checks (outputs quoted in §4).
- Live-DB/UI path not re-executed here: T3 already proved 21/21 live
  checks on `gaia_dev` through the real HTTP+SQL+engine path
  (see `audit_mh_frontend_journey.md` §6). Repeating it would require a
  staging target and is out of scope for this read-only rehearsal.

## 2. Scenario

Canonical fixture: `backend/app/seed/mh/scenario.py`
(Sahyadri Specialty Chemicals Pvt. Ltd., MIDC Kurkumbh, Daund, Pune).

- Project meta: `name`, `entity_type=pvt-ltd`, `sector=chemical`,
  `jurisdictions=["IN-MH"]`, headcount 60, turnover Rs. 50 cr.
- Facts: 41 keys (`CANONICAL_MH_SCENARIO_FACTS`), all inside the
  128-entry IN-MH registry (`test_all_scenario_facts_valid_in_mh_registry`
  passes). Derivations: `F-INC-01=SMALL` (via `derive_msme_class`),
  `F-PRC-03=False` (via `derive_mah_status`, provenance
  `source_facts=[F-HAZ-01, F-HAZ-02]` — the R-091-adjacent derivation,
  recorded as-is per the R-091 exclusion).
- Expected assessments: 20 entries (`CANONICAL_MH_EXPECTED_ASSESSMENTS`),
  each with `expected_applicability` + `expected_readiness` + source_ref
  + portal where mapped.

## 3. Journey steps (endpoint/UI used per stage)

The demo-drives-UI path is T3's contract (audited, not re-implemented).
Each row names the actual endpoint/UI, the expected behavior, the
behavior verified in this rehearsal (engine-level unless noted), and
PASS/FAIL. UI reachability itself is taken from the T3 audit's 21/21
live proof; engine correctness is re-verified here.

| # | Stage | Actual endpoint / UI | Expected | Actual (this rehearsal) | Verdict |
|---|---|---|---|---|---|
| 1 | Login | `LoginPage.tsx` → Supabase Auth; backend `get_current_user` JWT | Authenticated session, role from JWT | Code path unchanged since Phase 2B/3A; T3 marks PASS live; no reason to re-probe auth here | PASS (by prior live proof) |
| 2 | Create IN-MH project | `POST /projects?requested_jurisdiction=IN-MH` via `ProjectCreatePage` (default IN-MH select) | Project stamped `jurisdiction=IN-MH`, `pack_version=mh-v5-batch1`, server-side | Contract covered by `test_api_mh_demo_contract.py` (in the 181-green run); T3 live check "project create IN-MH stamped" PASS | PASS |
| 3 | Enter canonical MH facts | `POST /projects/{id}/facts` body `{"facts_json": {...}}` via `MhFactsEditor.tsx` + "Fill canonical demo values" | 41 facts persisted, validated against 128-registry; GJ keys 422 | Registry validity re-verified (`test_all_scenario_facts_valid_in_mh_registry` green); in-process `apply_derived_facts` yields derived `F-INC-01`, `F-PRC-03` with provenance | PASS |
| 4 | Save | Same facts endpoint (persist) | Facts stored per project; GET returns them | API contract tests green; T3 live "41 canonical facts persisted" | PASS |
| 5 | Select approvals/codes | `GET /projects/{id}/approval-codes` (pack projection) via `MhAssessmentPanel.tsx` | 20 assessable codes, no hardcoding | Pack serves `sorted(pack.approval_authorities)` = 20 codes; T3 live "20 codes projected" | PASS |
| 6 | Create application | `POST /applications` with `approval_code` (code-linked catalog row) via Assess/Open | Application inherits `(IN-MH, mh-v5-batch1)`; `APR-010` seeds DOC-001/002/003, `APR-026` seeds DOC-008 | Seeding verified in e2e audit §Step 3 and canonical tests (23 green); no GJ `Axx` code accepted (422 by `resolve_persisted_pack`/code validation) | PASS |
| 7 | Run orchestration | `GET /applications/{id}/orchestration` via `OrchestrationPanel.tsx` | Full pipeline: applicability → composition → dependencies → documents → gaps → readiness | In-process `orchestrate_application_full` over canonical facts returns `overall_status=blocked_by_dependency`, 20 per-approval results, all matching `CANONICAL_MH_EXPECTED_ASSESSMENTS` (20/20, see §4) | PASS |
| 8 | Inspect applicability | Same orchestration payload, `applicability_result` per approval | Exact vocabulary (lowercase wire values) | Observed values only from `{applies, does_not_apply, conditional, insufficient_data}`; enum `ApprovalResult` (`models.py:393-396`) is the single source | PASS |
| 9 | Inspect dependencies/documents | `dependency_readiness` / `document_readiness` + `blockers[]`; `DocumentChecklist.tsx`; `GET .../document-requirements` | APR-010 `blocked_by_dependency` (APR-008/009); APR-026 `blocked_by_documents` (DOC-008) | Reproduced exactly: APR-010 `applies/blocked_by_dependency nb=3`; APR-026 `applies/blocked_by_documents nb=1` | PASS |
| 10 | Inspect readiness | `status` per approval + `overall_status`; `MhAssessmentPanel` chips render backend strings verbatim | 7-state readiness, backend-computed | Observed `status` vocab `{ready, blocked_by_dependency, blocked_by_documents, insufficient_data, not_applicable}` on canonical data (remaining states `blocked_by_consistency`, `conditional` reachable via other inputs per engine tests); frontend only renders (`statusBadge`), never computes | PASS |
| 11 | Inspect citations/explanations | `GET /regulatory/approval/{id}/explanation`, `GET /regulatory/orchestration/{id}/citations` (T5-wired, persisted-pack path) | MH citations resolve to MH sources, never `[]` for active rules | `get_approval_citations(pack.sources, pack.approval_rules, code)`: APR-006 → `[SRC-001/IN-MH]`; APR-026 → `[SRC-092, SRC-017/IN-MH]`; APR-023 → `[SRC-034, SRC-085/IN-MH]`; full 26-rule inventory resolves (T5 §3-4, 44 tests green in this run) | PASS |
| 12 | Run What-If | `POST .../orchestration/what-if` via `WhatIfPanel` (custom-fact mode) | Same-pack baseline+alt, stateless, persisted facts untouched | `run_whatif_assessment(..., jurisdiction="IN-MH")` returns `{baseline, what_if, diff, applied_overrides}`; `facts == before` after run (True); T3 live "F-PET-02→50000 flips APR-026, project facts byte-identical" | PASS |
| 13 | Inspect changed result | `diff.status_changes` / `blocker_changes` in What-If response | Changed approval visible, baseline preserved | What-If response shape verified (`application_id, applied_overrides, baseline, diff, note, what_if`); canonical what-if flips covered by `test_mh_canonical_scenario.py` (4 flips) + e2e APR-003 flip | PASS |
| 14 | Prepare handoff | `GET .../handoffs` (ready list) + `POST .../handoffs/initiate` via `HandoffPanel.tsx` | Only READY approvals listed; initiate allowed for READY | `prepare_initiation(..., orchestration_status="ready", reported_by, portal_entry=pack.get_portal_entry(code))` → APR-006 ALLOWED (`handed_off`, `MoEFCC / PARIVESH`, `portal_kind=portal`, `verification=user_reported`); APR-010/APR-026/APR-001/APR-003 REJECTED with `HandoffStateError` | PASS |
| 15 | Verify handoff gate | `POST .../record-submission`, `.../report-status`, `.../verify` (applicant-recorded, staff-verified) | Non-ready 409; READY initiates; verification=`user_reported` (never claims government acceptance) | Gate `is_ready_to_handoff(s) == (s == "ready")` (`handoff/service.py:54-56`); canonical + e2e suites assert 409 on blocked (`test_mh_canonical_scenario.py:624-661`, `test_mh_api_e2e.py:610-647`); T3 live "READY handoff initiates, non-ready 409" | PASS |

## 4. Results — the 15 verification items

1. **IN-MH explicit and persisted: PASS.** Pack boundary raises
   `UnknownJurisdictionError` on anything but `IN-GJ`/`IN-MH`; persisted
   `(jurisdiction, pack_version)` resolved via `resolve_persisted_pack`
   (never the global default). Canonical project meta carries
   `jurisdictions=["IN-MH"]`; T3 creation stamps server-side.
2. **No silent IN-GJ fallback: PASS.** `DEFAULT_JURISDICTION = "IN-GJ"`
   is new-records-only; unknown jurisdictions/versions raise 422, GJ fact
   keys under MH raise 422 `jurisdiction_mismatch`, GJ approval codes
   under MH raise 422. In-process: `DEFAULT: IN-GJ` printed while the MH
   pack still loads and assesses independently.
3. **Applicability vocabulary exact: PASS.** Only
   `applies / does_not_apply / conditional / insufficient_data`
   (`ApprovalResult`, `rules/models.py:393-396`). Canonical run uses all
   of `applies`, `does_not_apply`, `insufficient_data` (conditional
   covered by exemption-unknown paths in `test_mh_r087_semantics.py` and
   e2e suites). Frontend renders `applicability_result` verbatim
   (`OrchestrationPanel`); no synonym mapping found.
4. **R-043/R-044 exemption semantics correct: PASS.** Both
   `role=exemption` (`approvals.py:525,542`), composition
   `APR-043 = triggers[R-077] + exemptions[R-043, R-044]`. Canonical
   APR-043 → `does_not_apply/not_applicable` (trigger FALSE, exemptions
   correctly inert — no false APPLIES). Truth-table/readiness/handoff
   suites green in this run (`test_mh_r044_exemption.py` in the 181).
5. **R-087 current semantics correct: PASS.** `role=exemption`,
   composition `APR-023 = triggers[R-028, R-073, R-086] +
   exemptions[R-087]`; triggers non-empty (R-030 invariant N/A).
   Canonical: R-028 `does_not_apply` (no boiler), R-087
   `insufficient_data` (F-BLR-07 missing, fail-closed), APR-023
   `does_not_apply/not_applicable` — matches expected. The 62-test T4
   suite (truth-table, readiness, handoff, What-If, GJ isolation) green
   in this run. Known T4 limits (§20 of that audit) stand and are demoed
   honestly (2025-registered defeat unencoded; BOE limb rides
   registration triggers).
6. **R-030 stays TRIGGER, no regress: PASS.** `role=trigger`
   (STOP verdict), APR-026 uncomposed (legacy priority). Canonical:
   R-030 `applies`, APR-026 `applies/blocked_by_documents` (DOC-008) —
   matches expected. The 38-test STOP/falsification suite green.
7. **APR-001 classification composition correct: PASS.**
   `APR-001 = classifications[R-002]`, no trigger → honest
   `insufficient_data/insufficient_data` with advisory UR-06 blocker
   (`nb=1`). Matches expected; `test_mh_ec_core.py:288-323` pins
   designed-INSUFFICIENT_DATA.
8. **MH citations resolve to MH sources: PASS.** See §3 row 11 and T5
   inventory: all 26 active rules resolve within the 22-record MH corpus
   (17 distinct refs, missing=[]). Spot checks this task: APR-006→SRC-001,
   APR-026→SRC-092/SRC-017, APR-023→SRC-034/SRC-085 — all `IN-MH`.
9. **No GJ source in MH results: PASS.** Blocker blob scan over all 20
   canonical approvals for `GIDC/GPCB/Dahej/R-GIDC`: zero hits.
   Citation spot-check blobs: no `S01`/`IN-GJ`. Jurisdiction-isolation
   suites (`test_persisted_jurisdiction.py`, T5 cross-contamination
   tests) green by suite membership.
10. **What-If does not mutate persisted facts: PASS.** Engine takes
    `base_facts` by value (`dict(base_facts)`), strips provenance keys,
    re-derives the alt branch; `facts == before` → True in this run.
    API contract: "zero database writes (strictly in-memory)" (e2e audit
    §Step 10); T3 live byte-identical check PASS.
11. **Readiness is backend-derived: PASS.** Statuses computed by
    `orchestrate_application_full` (applicability + `evaluate_readiness`
    + documents + gaps); frontend `MhAssessmentPanel`/`OrchestrationPanel`
    render `overall_status`/`status` strings only. No frontend
    applicability/readiness computation found (T3 §"render-only").
12. **Non-ready handoff rejected: PASS.** `prepare_initiation` raises
    `HandoffStateError` unless `status == "ready"`; API maps to 409
    (`only READY approvals can be handed off`). Reproduced for APR-010,
    APR-026, APR-001, APR-003.
13. **READY handoff allowed: PASS.** APR-006 → `handed_off` with portal
    `MoEFCC / PARIVESH https://parivesh.nic.in/`, `portal_kind=portal`,
    `verification=user_reported`. Matches canonical expectation
    ("fully handoff-ready").
14. **No UI claims actual government submission: PASS.** `HandoffPanel`
    disclaimer is explicit: "UdyamDwaar does not submit applications to
    the government. Apply on the authority's official portal below, then
    record your external reference here. Documents prepared here are not
    sent anywhere automatically." Verification badges distinguish
    "Staff verified" vs "Reported by applicant — unverified". No
    "submitted to government / approved by government" claim found in MH
    journey components.
15. **Missing evidence visible, never silently converted: PASS.**
    APR-001 surfaces the UR-06 gap blocker (`Evidence gap UR-06
    (NOT_ESTABLISHED)...`); empty-facts → `insufficient_data`;
    `"UNKNOWN"`/None → `insufficient_data` (never FALSE); trigger-TRUE +
    unknown defeater → `CONDITIONAL` (never APPLIES). INSUFFICIENT_DATA
    copy in the UI keeps the backend term (chips/badges), not a
    "required/not required" rewrite.

**R-091 note (as instructed):** `R-091` is absent from
`pack.approval_rules` (checked: `any(r.id == "R-091")` → False) — the
ApprovalRule stays deferred while `derive_mah_status()` supplies the
partial `F-PRC-03=False` derivation with provenance. Canonical APR-055
does not depend on it. Statement for the record: **R-091 intentionally
excluded from this rehearsal baseline**; existing behavior tested
without modification (derivation + wiring suites green).

## 5. Screenshots / evidence

The existing workflow does not produce screenshots in-repo; evidence is
the deterministic engine output + test results + cited code lines:

- Canonical orchestration (this task, in-process):
  `APR-001 insufficient_data/insufficient_data ·
   APR-003 does_not_apply/not_applicable · APR-004 · APR-006
   applies/ready · APR-007 · APR-010 applies/blocked_by_dependency (3
   blockers) · APR-019 applies/ready · APR-022 · APR-023
   does_not_apply/not_applicable · APR-026 applies/blocked_by_documents
   (1 blocker) · APR-029 applies/ready · APR-043 does_not_apply/
   not_applicable (1 advisory blocker) · APR-044 · APR-054 · APR-055 (1
   advisory blocker) · CMP-018 · CMP-024 · CMP-025 · LOC-CRZ ·
   LOC-FOREST` — **20/20 match** against
  `CANONICAL_MH_EXPECTED_ASSESSMENTS`.
- Handoff record (APR-006): `status=handed_off`,
  `external_system=MoEFCC / PARIVESH`, `portal_kind=portal`,
  `verification=user_reported` (full dict in §3 row 14).
- Test evidence: 181-test rehearsal subset green (canonical 23 +
  rag-citations 44 + r087 62 + r044 + demo-contract 13); canonical
  determinism ×10, what-if, handoff, traceability, and API-route tests
  all inside the 23.

## 6. Citation verification

- Source-reference inventory (T5 §3, re-confirmed): all 26 active rules
  resolve inside the MH pack (17 distinct `SRC-xxx` refs over 22-record
  corpus; missing=[]). No rule cites a GJ `Sxx` source; no GJ source
  cites an MH rule.
- Live resolution (this task): APR-006→SRC-001, APR-026→SRC-092+SRC-017,
  APR-023→SRC-034+SRC-085, each with `jurisdiction=IN-MH` and official
  URLs verbatim (e.g. PARIVESH upload, peso.gov.in, Gazette text).
- Explanation discipline (T5 §12, unchanged): templates only restate the
  deterministic result + jurisdiction label + evidence qualifier; no
  "must/shall/mandatory/deadline" claims in generated text (tested); RAG
  never recalculates applicability (no engine calls from
  retrieval/explanation); orchestration/What-If/readiness/handoff
  byte-identical with/without citations.
- Structural honesty: `SourceRecord` has no structured
  effective-from/to or evidence-status enum (dates/status live in notes
  verbatim) → citation fields expose None where unavailable, never
  invented. Overlapping APR-010 sources (SRC-013 + SRC-120) both
  returned; no silent supersession.

## 7. What-If verification

- Same-pack guarantee: `run_whatif_assessment(..., jurisdiction="IN-MH")`
  threads `pack.approval_compositions`, rules, dependencies, and evidence
  gaps into both baseline and alt branches.
- Non-mutation: `facts == before` → True (this task); API performs zero
  DB writes (in-memory only).
- Changed-result path: T3 live flip (F-PET-02→50000 changes APR-026)
  with project facts byte-identical afterwards; canonical suite asserts 4
  flips; e2e asserts APR-003 `does_not_apply→applies` flip.
- Demo line: change a petroleum quantity or built-up area live, show the
  `diff.status_changes`, then show the persisted project facts unchanged
  (re-fetch or state that What-If is explicitly stateless).

## 8. Readiness / handoff verification

- Backend-derived readiness: `overall_status=blocked_by_dependency`
  (canonical: APR-010's unobtained APR-008/009 correctly dominate the
  roll-up even though APR-006/019/029 are READY) — engine-correct, and an
  honest demo talking point (overall ≠ "everything blocked").
- Ready set: APR-006, APR-019, APR-029 (all `ready`, zero blockers).
  Each has a portal entry (`POR-001 PARIVESH`, `POR-005 Labour Dept`,
  `POR-008G MIDC GIS`).
- Gate: `is_ready_to_handoff` is a one-line `== "ready"` check; the API
  returns 409 for anything else. No override, no staff bypass, no
  auto-submit.
- Truthful bookkeeping: handoff records are applicant-reported
  (`user_reported`) until staff verifies; the UI labels portal vs
  reference links (`portal_kind`: "Open official portal" vs "Open
  official reference (portal link not verified in this dataset)");
  external status is reported, never polled from a government system
  (`handoff/service.py:1-6` — no HTTP/polling/scraping).

## 9. Demo claim audit (visible MH UI copy)

Scale: VERIFIED / BACKED BY CURRENT IMPLEMENTATION / NEEDS
QUALIFICATION / UNSUPPORTED. No UI copy was rewritten (none needed).

| Visible claim / copy | Where | Classification | Basis |
|---|---|---|---|
| "Approval Assessment (IN-MH pack)" + per-code authority + backend status chips | `MhAssessmentPanel.tsx` | VERIFIED | Pack projection + per-application orchestration; statuses rendered verbatim |
| Per-approval `applicability_result`/`status`, explanation, doc/dep readiness, blockers with `source_ref/evidence/action_required` | `OrchestrationPanel.tsx` | VERIFIED | Straight from `ApplicationOrchestration`; exact backend vocabulary |
| Jurisdiction/pack badges, `approval_code` + jurisdiction chips in headers | Project/detail pages, `ApplicationDetailShared` | VERIFIED | Server-stamped identity surfaced, nothing invented |
| "UdyamDwaar does not submit applications to the government…" + "Documents prepared here are not sent anywhere automatically" | `HandoffPanel.tsx:120-124` | VERIFIED | Explicit non-integration disclaimer; the strongest honesty asset in the UI |
| "Reported by applicant — unverified" vs "Staff verified" | `HandoffPanel.tsx` `VerificationBadge` | VERIFIED | Matches `verification=user_reported/staff_verified` backend values |
| "Open official portal" (portal) vs "Open official reference (portal link not verified in this dataset)" (reference) | `HandoffPanel.tsx` `PortalCta` | VERIFIED | `portal_kind` distinction honored; no MAITRI claim; no fake single-window |
| "No approval is currently READY for external handoff" (empty state) | `HandoffPanel.tsx:238-242` | VERIFIED | Accurate empty-state, not a silent zero |
| "Still to prepare here: {docs}" | `HandoffPanel.tsx:140-144` | BACKED BY CURRENT IMPLEMENTATION | Doc checklist from pack requirements; "prepare here" is local, not a portal claim |
| "Target: {n} business days … {n} days remaining/overdue" | `SLACard.tsx` | NEEDS QUALIFICATION | MH SLA rows are display metadata (`seed/mh/slas.py`: target/outer never merged, UNKNOWN preserved, no computation); business-days exclude weekends only (no Indian holiday calendar). Demo line: "indicative working-day count, not a statutory deadline." |
| Requirement level labels `mandatory/conditional` | `DocumentChecklist.tsx:140-142` (renders `req.requirement_level`) | BACKED BY CURRENT IMPLEMENTATION | Values come from the pack's verified document register (DOC-001/002/003→APR-010, DOC-008→APR-026); do not narrate as statutory "mandatory under Act X" beyond the shown source_ref |
| "required" (HTML form attribute) on login/project/MH-facts inputs | `LoginPage`, `ProjectCreatePage`, `MhFactsEditor`, `ProjectDetailPage` | VERIFIED (not a regulatory claim) | Browser-level input requiredness, unrelated to approval outcomes |
| "Approved" status labels (workflow `approved`, handoff `approved_external`) | `StatusBadge`, queue/detail pages, `HandoffPanel NEXT_STATES` | NEEDS QUALIFICATION | These are *workflow/external-tracking* states (internal decision or applicant-reported external outcome), not government-issued approvals. The handoff verification badge mitigates; the demo script should say "recorded as approved externally (applicant-reported)" when that state appears. |
| Authority names shown (e.g. "MoEFCC / PARIVESH", "MPCB ecMPCB", "PESO Online", "Maharashtra Labour Department", AUT-xxx strings) | `MhAssessmentPanel`, handoff ready-list (`r.authority`, `r.external_system`) | BACKED BY CURRENT IMPLEMENTATION | v5-transcribed authority strings / portal catalog entries; per-approval authority is shown where the backend returns it (handoff ready list) and not invented where the orchestration model lacks it (T3 §7 row "Approval detail: PASS") |
| Timelines / SLAs as statutory deadlines | SLA card, `sla_records` | NEEDS QUALIFICATION | See SLA row above. Never present the card as "the authority must decide in N days." |
| Approval status ("ready", "applies") as permission to construct/operate | Orchestration/readiness UI | NEEDS QUALIFICATION | "READY" means *ready to hand off / all local checks satisfied in this tool*, not a clearance. Demo line: "ready for external filing, not a substitute for the authority's decision." |
| Regulatory citations as legal advice | Explanation/citation UI | NEEDS QUALIFICATION | Citations are traceable evidence pointers with trust tiers (T1 vs T2/T3 qualifiers); INSUFFICIENT_DATA is never rewritten as "required/not required". Demo line: "pointers to the official text, not a legal determination." |
| Government integration / auto-submission | Any MH flow | UNSUPPORTED (correctly absent) | No such claim exists in code or copy; the UI affirmatively disclaims it. Keep it that way — do not ad-lib integration language in the demo narration. |
| "required"/"mandatory" as in *statute* mandates | Generated explanation text | VERIFIED ABSENT | Tested: no "must/shall/mandatory/deadline" in generated explanations (T5 §12). Blocker `action_required` is a next-step hint, not a statutory command. |

No incorrect existing claim was found that forces a copy rewrite. The
three NEEDS QUALIFICATION rows are narration discipline (SLA card,
"approved" states, readiness/citation framing), not code defects.

## 10. Known limitations (must be qualified in the demo, not fixed here)

1. Overall status `blocked_by_dependency` on the canonical project is
   correct engine behavior (APR-010's unobtained CTE/CTO dominate the
   roll-up) — present it as "three approvals ready, one blocked by
   priors, rest not applicable/insufficient" rather than "the project is
   blocked."
2. APR-001 is designed-`insufficient_data` (classification-only until
   the R-003-pattern consumer lands, T9) with an advisory UR-06 blocker —
   present as "needs the EC category decision, which the current pack
   deliberately does not automate."
3. R-087 limits (T4 §20): a 2025-registered boiler still composes to
   APPLIES (no defeat encoded — not invented); the BOE limb rides the
   registration triggers. Canonical path (no boiler) is unaffected.
4. R-030 stays TRIGGER per the STOP verdict (no live s.3(2) trigger
   encoded yet); APR-026 readiness is document-gated (DOC-008), which is
   exactly what the demo shows (upload DOC-008 to unblock).
5. Incentive panel still serves GJ GIP-2020 schemes on MH projects
   (pre-existing quarantine, T3 §9) — either skip that panel in the MH
   demo or label it "Gujarat schemes shown; MH pack out of scope."
6. `RegulatoryAssistant` free-text search path vs per-approval explain:
   per-approval/persisted-pack citations are wired (T5); if the demo
   touches free-text search, note it is pack-token search over
   title/authority/notes (no embeddings), GJ-DB-backed only for GJ.
7. SLA card: business days exclude weekends only (no Indian holiday
   calendar); MH rows are display metadata, not computed deadlines.
8. Staging migration 010 unexecuted (T6 BLOCKED, ops) — local/demo-DB
   behavior only; no production migration is part of this demo.
9. R-091 intentionally excluded (see §4 note): derivation visible
   (`F-PRC-03=False` + provenance), ApprovalRule deferred. If asked,
   say exactly that.
10. Canonical `mhFacts.ts` fill values duplicate `scenario.py` (drift
    risk if the fixture changes; submission still server-validated).

## 11. Final demo readiness assessment

The current Maharashtra implementation **can be demonstrated honestly
today** through the exact flow:

Login → create IN-MH project (explicit select) → fill canonical MH
facts ("Fill canonical demo values") → save → approval codes (20,
pack-driven) → create application per code → orchestration (exact
`applies/does_not_apply/conditional/insufficient_data` vocabulary) →
dependencies (APR-010 blocked by APR-008/009) → documents (APR-026
blocked by DOC-008) → readiness (backend `ready/blocked_by_dependency/
blocked_by_documents/insufficient_data/not_applicable`) → citations
(MH `SRC-xxx`, `IN-MH`, official URLs) → What-If (stateless flip,
persisted facts untouched) → handoff (READY APR-006 initiates to
PARIVESH reference; non-ready 409s) → verification state
(`user_reported` until staff verifies).

What must be qualified aloud (narration, not code): SLA card is an
indicative working-day count; "approved/ready" are tool/workflow states,
not government decisions; citations are evidence pointers, not legal
determinations; APR-001's insufficiency and the overall
`blocked_by_dependency` roll-up are designed fail-closed behavior;
incentives panel (if shown) is Gujarat data; R-091 is excluded by scope;
no government submission occurs in or behind the tool.

No genuine defect was found in this rehearsal. Per instructions, no
production code was changed (only this audit file is added). Nothing in
the above blocks the final SIH demo on a demo database; the single
ops-blocked item (T6 staging migration 010) does not affect demo
correctness.

## Appendix — files changed

- `docs/audits/audit_mh_canonical_demo.md` (this file) — new.
- No implementation, rule, migration, frontend, or test files touched.
  `git status` before: clean; after: only this file untracked.
