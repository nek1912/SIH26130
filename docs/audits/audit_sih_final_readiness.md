# Audit: Final SIH Release Readiness (PS 26130)

Date: 2026-10-02. Baseline: HEAD `17196d1` (clean) + this task's
read-only findings. Type: READ/AUDIT/CONSISTENCY. No rule, role,
composition, FactSpec, GJ-behavior, default, fact, predicate, or
architecture changes were made for any finding below. Where the
working tree already contained the fix (README staleness), the
correction is recorded in §8.

## 1. PS 26130 coverage matrix

Scale: IMPLEMENTED / PARTIALLY IMPLEMENTED / EVIDENCE-BOUNDED /
DEFERRED / NOT IMPLEMENTED. "Evidence-bounded" means the capability
exists but its scope is fenced by verified evidence (fail-closed
outside the fence).

| PS requirement | Implementation evidence | Status | Limitation | Demo evidence |
|---|---|---|---|---|
| Project onboarding (applicant creates a project) | `POST /projects` (server-stamped jurisdiction), `ProjectCreatePage` with explicit IN-MH/IN-GJ select | IMPLEMENTED | Jurisdiction immutable after creation (by design) | T3 21/21 live: IN-MH project stamped |
| Project facts (structured profile + questions) | `POST .../facts` embedded-`facts_json` body, 128-fact MH registry, `MhFactsEditor` (37 curated fields + canonical fill), strict 422 validation | IMPLEMENTED | 37 of 128 facts have form fields; the rest submit via API only | 41 canonical facts persisted live |
| Approval applicability (applies / not / conditional / unknown) | Deterministic engine + 26 MH rules + compositions; exact 4-state vocabulary end to end | EVIDENCE-BOUNDED | 26 of 105 inventoried rules active; 61 deferred + 11 confirmation-gated fail closed | Canonical 20/20 match; APR-001 designed-insufficient |
| Dependencies (ordered prerequisites, blockers) | Dependency engine (DFS/Kahn/longest-path), DEP-009 ×2, readiness gating | EVIDENCE-BOUNDED | Only verified edges encoded (DEP-019 correctly refused) | APR-010 blocked by APR-008/009 |
| Documents (checklist, upload, validation) | Requirements seeded per pack; upload/MIME checks; deterministic extraction+validation; consistency engine | IMPLEMENTED | No OCR for image-only docs; checks run on demand | DOC-008 blocks APR-026; upload-clears path tested |
| Readiness (per-approval + overall, next action) | `orchestrate_application_full`; exact 7-state vocabulary; backend-computed only | IMPLEMENTED | MH SLA rows are display metadata, not statutory deadlines (narrate as indicative) | APR-006 ready; overall `blocked_by_dependency` correctly dominated by APR-010 |
| Citations (source-grounded answers) | T5 pack-backed citations, persisted-pack path, trust tiers, qualifiers; templates only | EVIDENCE-BOUNDED | 22-record MH corpus (166 deferred with their rules); no structured effective-date/status fields (None, never invented); DB stays GJ-only by design | APR-023→SRC-034/085 IN-MH; no `must/shall` in generated text (tested) |
| What-If (temporary scenario deltas) | Same-pack baseline+alt, stateless, custom-fact UI, backend-validated | IMPLEMENTED | Overrides limited to vocabulary the pack validates (422 otherwise) | F-PET-02→50000 flips APR-026; facts byte-identical |
| Handoff preparation (portal readiness, tracking) | Truthful bookkeeping: READY-only initiate (409 otherwise), portal/reference CTA split, applicant-reported vs staff-verified | IMPLEMENTED | No submission occurs; no MAITRI/single-window claim exists | APR-006 initiates; APR-010 409s; disclaimer rendered |
| Jurisdiction (MH primary, GJ legacy, no fallback) | Persisted `(jurisdiction, pack_version)`; `DEFAULT_JURISDICTION=IN-GJ`; cross-pair 422s; UI chips + explicit select | IMPLEMENTED | Migration 010 unexecuted on staging (T6 ops) | MH↔GJ rejection rehearsed; zero GJ leakage in MH payloads |
| Regulatory evidence (traceable, versioned) | 17 distinct source_refs cover all 26 active rules (missing=[]); advisory gaps (UR-06/UR-11/DOC-012) surface as blockers | EVIDENCE-BOUNDED | R-091 full closure needs M2/S1-TOX/spatial/currency evidence; 61 deferred stay dark by design | Gap blockers carry evidence_id/status/question |
| Government integration (portal submission, live data) | None exists; architecture treats integration as a future adapter boundary | NOT IMPLEMENTED (correctly absent) | Must never be claimed; UI affirmatively disclaims it | "UdyamDwaar does not submit applications to the government" |
| Auditability (append-only history, provenance) | Workflow events persisted; audit records on transitions; FactProvenance on derived facts; per-decision rule/source/timestamp trace | IMPLEMENTED | — | Provenance asserted in canonical/API tests |
| Explainability (why + source for every claim) | Per-approval `explanation` + blocker `source_ref/evidence/action_required` + citations; RAG never decides (no engine calls from retrieval) | IMPLEMENTED | Explanations are evidence pointers, not legal determinations (narrate accordingly) | All canonical approvals carry explanations |

## 2. Demo truth check

The demo can honestly say: deterministic rules decide; RAG retrieves;
templates explain; human/statutory authority decides. It must NOT imply:
LLM regulatory decisions (no LLM/model dependency exists in either
package); automatic government approval ("ready/applies/approved" are
tool/workflow states); handoff-equals-submission (disclaimed in UI and
copy); full Maharashtra coverage (26/105 active, stated in README §2);
resolved evidence (UR-06/UNK-035/CON-021-cell-gating/R-091-M2-M5-M8
remain open and visible). Preserved limitations: APR-001
insufficient-by-design; R-087 2025-registered/BOE limits; R-030
TRIGGER/document-gated; R-091 partial; GJ-only incentives panel;
indicative SLA card; T6 staging-blocked.

## 3. R-091 final status

Evidence gap closed, implementation intentionally not expanded
(`audit_mh_r091_derivation.md`, 9 pins in `test_mh_r091.py`). Never
"fully implemented": proven M3/M4/M7/M9 subset live; M2 external
identity, S1-TOX resolution, M8 spatial/installation semantics,
APR-012 lifecycle prerequisites, runtime threshold versioning, and
UNK-035 currency remain documented gaps. Reopens only on new primary
evidence. Sole live consumer is informational R-002.

## 4. T6 final status

BLOCKED — no staging database/environment exists anywhere in the
repository (config, env examples, docs, ARCHITECTURE §§40/44 all
local-only). Migration 010 statically validated, never executed;
`gaia_dev` is reference-only and was never substituted. Local 010
objects present on `gaia_dev` are reference state, not staging proof.

## 5. Architecture claims (all verified true)

No LLM in the decision path (zero model/vector dependencies in either
package); no vector database (tsvector + token-overlap only);
deterministic applicability engine; explicit UNKNOWN/INSUFFICIENT_DATA
handling (never coerced to FALSE); jurisdiction isolation (19/0 GJ vs
26/3 MH, cross-pair 422s); evidence traceability (rule/source/
timestamp/provenance per decision); RAG retrieval+templates only;
human/statutory authority final (no auto-approval path exists).

## 6. Security / engineering claims

`git diff HEAD~1` reviewed in full (T7's 4 files only): no secrets,
debug code, fake URLs, fake integrations, or dependency additions.
Secret scan over the complete pending diff: clean (only benign
"token-overlap" code tokens). Default GJ behavior preserved
(untouched paths + green GJ suites). MH explicitly selected/persisted
everywhere. No undocumented production dependency.

## 7. Test / verification baseline (post-commit where noted)

- Backend: 2476 passed, 0 failed (pre-existing; tree code-identical
  since — only docs changed after).
- Ruff: 20 × E501, all pre-existing on untouched lines.
- TypeScript 0 errors; oxlint no errors; `vite build` success.
- `verify_local_db.py`: 9/9 (incl. 013 `portal_kind`).
- Canonical MH rehearsal: 20/20 assessments + 12/12 closure checks
  (R-087 paths, R-043/R-044 defeat, R-030 doc-blocked, MH citations,
  What-If scoping, isolation).
- T3 live journey: 21/21 (HTTP+SQL+engines, rows cleaned).
- OpenAPI: 53 paths; all key routes present; generation clean.
- Isolation: cross-jurisdiction rejection rehearsed.

## 8. Claim corrections applied with this audit (README.md)

The README contradicted the implementation and was fixed (no PPT or
external report exists in-repo to update): "authoritative /
single-window assistant" → handoff-preparation assistant that issues
no approvals and performs no submission; 50→61 deferred; 12→13
migrations; active-rule list rewritten to the true 26 (CTE/CTO sector
triggers explicitly excluded from the claim); readiness vocabulary
corrected to the exact 7 states; 6 non-existent API routes replaced
with real ones (`/whatif/simulate`, `/consistency/check`,
`/documents/extract`, `/regulatory/search`, `/handoffs/{id}` never
existed); "Generate single-window portal handoff package" →
manual-progress recording with no submission; test/lint counts updated
to measured values. Remaining marketing adjectives
("ultra-responsive", "high-performance") are puffery, not regulatory
claims — left alone.

## 9. Claims safe for PPT/demo

- "Maharashtra-focused deterministic approval orchestration"
- "Evidence-backed applicability assessment (26 verified rules; the rest fail closed, visibly)"
- "Fail-closed handling of missing regulatory evidence (no guessing, ever)"
- "Traceable regulatory sources on every non-trivial result"
- "Preparation for government handoff — the tool files nothing itself"

## 10. Claims that must NOT be made

- Complete Maharashtra coverage (26/105; say the fence, not the field)
- Live government submission / MAITRI integration / single-window filing
- Automatic approval or "deemed clearance" from a READY/APPLIES state
- Guaranteed SLA or statutory deadlines (SLA card is indicative)
- Real-time government synchronization (no polling exists by design)
- Legal determinations ("required by law" language; say "the cited source states…")
- 100% accuracy / zero-error / authoritative interpretation
- R-091 as fully implemented; staging migration as executed

## 11. Blocker taxonomy

- DEMO BLOCKER: none.
- SUBMISSION CLAIM RISK: the 10 "must NOT" claims above — mitigated by
  the §9 safe framings; highest-risk surfaces are the SLA card and
  "approved/ready" wording (narration discipline, already qualified
  in-repo).
- PRODUCTION DEPLOYMENT BLOCKER: T6 staging migration (ops).
- OPERATIONAL BLOCKER: T6 (no staging target, credentials, backup, or
  window).
- FUTURE ENHANCEMENT: T7 consent chain, T8 R-091 (on new evidence), T9
  APR-001 consumer, MH incentive pack, OCR, holiday calendar.

## 12. Files changed by this task

- `docs/audits/audit_sih_final_readiness.md` (this file) — new.
- `README.md` — factual corrections listed in §8 (counts, routes,
  vocabulary, framing; no behavior change).
- `docs/audits/audit_mh_canonical_demo.md` — committed here as the
  documentation-only closure change (§13 instruction).

Next action: present the SIH demo from §9 safe claims with §10
qualifications spoken aloud; schedule T6 ops independently.
