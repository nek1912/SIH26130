# Maharashtra Consent Category Chain Audit — R-013, R-014, R-015, R-017

Follow-up to `audit_mh_midc_lifecycle_tail.md`; the chain was explicitly
scoped out of that task. Jurisdiction: IN-MH (primary). IN-GJ is
regression-only. Date (UTC): 2026-09-29. Authoritative source: v5
regulatory registers (`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`).
Identity is additionally verified at test time by reading the CURRENT CSVs
(same pattern as `test_mh_cto_renewal.py`).

## 1. Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"`. Unchanged.
- Before: MH active 26, MH deferred 58, MH confirmation 26, GJ active 19,
  MH facts 128, suite 1809 passed.
- After: MH active 26, MH deferred **59** (+R-015 explicit entry), MH
  confirmation 26, GJ active 19, MH facts 128, suite **1869 passed**
  (1809 + 60 new). No builder, engine, fact, source, SLA, or pack change.
- Ruff clean (`app/`, `tests/`). Frontend `tsc --noEmit` clean.
- Pre-existing uncommitted work from earlier clusters left untouched; this
  task adds one deferral entry, two baseline-count updates in prior test
  files (58→59 cascade), one test file, this artifact, and minimal doc
  entries.

## 2. Candidate Identity Matrix

From CURRENT `rule_register_v5.csv` / `rules.csv` (prior hypotheses
confirmed, with sharpened detail):

| Rule | Title | Approval | Stage / lifecycle | Authority | Status |
|------|-------|----------|-------------------|-----------|--------|
| R-013 | Consent to Establish (Water & Air Acts) | APR-008 | PRE_ESTABLISHMENT / PRE_CONSTRUCTION, trigger "before establishing" | AUT-003 (MPCB, VERIFIED statewide) | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE; `CONSENT_REQUIRED := MPCB_CATEGORY IN {RED,ORANGE,GREEN}` over F-MPCB-01; T2 SRC-011 + T4 SRC-010; EXACT 2025-06-23 |
| R-014 | Consent to Establish (Water & Air Acts) | APR-008 | same | AUT-003 | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE; `SECTOR_CATEGORY := lookup(F-MPCB-01)` (register operator LOOKUP, CPCB table: 111.x organics→RED, 42.1 dyes→RED, 123.x pharma→RED/ORANGE, 117.x paints→RED/ORANGE, 143.x/144 resins→RED/GREEN, 76 HW recovery→RED); note "Only listed codes encoded; others → UNKNOWN" |
| R-015 | Consent to Establish (Water & Air Acts) | APR-008 | same | AUT-003 | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, rule_kind **GUARD_OR_ROUTING**; `UNIT_CATEGORY (multiple sector codes) := UNKNOWN`; T4 SRC-011 only; confidence HIGH *(that no rule found)*; note forbids maximum-category |
| R-017 | Consent to Operate (Water & Air Acts) | APR-009 | PRE_OPERATION, trigger "before commencing operation", precondition CTE | AUT-003 | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE; `CTO_REQUIRED := CONSENT_REQUIRED == TRUE` with required_inputs literally **R-013**; T1 SRC-004; effective 1974/1981 YEAR_ONLY |
| (context) R-016 | same title | APR-008 | same | AUT-003 | **DO_NOT_IMPLEMENT_YET** / DO_NOT_IMPLEMENT (deemed CTE, T1 text but UNKNOWN MH implementation; ET-072/073 never-granted) |

Approvals: APR-008 CTE (CONSENT/PRE_CONSTRUCTION, rules R-013–016, SAFE);
APR-009 CTO (CONSENT/PRE_OPERATION, rule R-017, SAFE; validity R-062-gated,
renewal UNK-001). Shared deps APR-001/APR-038, docs DOC-004/011, timelines
SLA-001/002/003/048/049/050 — none loaded in the pack.

## 3. R-013 Audit

R-013 answers (B)/(E): "which category is the project, and does that
trigger consent" — applicability *conditioned on a prior classification*.
`MPCB_CATEGORY` is R-014's output, not a project fact (no such fact in
facts.csv or the 128 code facts). Creating a direct CONSENT_REQUIRED=TRUE
rule would skip the classification the law requires; with classification
unresolved, consent fails closed. White explicitly exempt (ET-049:
codes=[]/White → FALSE); Blue is essential-services note, not consent.
UNKNOWN codes → UNKNOWN (ET-110). Deferred (pre-existing reason verified
accurate). No change.

## 4. R-014 Classification Lookup Audit

1. Table source: CPCB Directions 12-02-2025 categorisation + MPCB adoption
   circular 23-06-2025 (effective date for both).
2–4. Not fully digitized: register covers listed chemical codes only;
   **no mapping table exists anywhere in code** (verified: no sector-code
   map in `app/`; pack carries neither SRC-010/SRC-011 nor any APR-008
   rule). Unlisted sectors → UNKNOWN by register note.
5–7. Sub-activities partially listed (e.g. 123.1 vs 123.3, 117.1-3 vs
   117.4, 143.1 vs 144); hazardous-process modifiers not separately
   modeled; multi-activity handled only by the R-015 UNKNOWN guard.
8–10. Version 2025-06-23 (MPCB adoption); amendment currency beyond the
   T4 mirror unverified; categories Red/Orange/Green/White/Blue per notes.
11–15. Chemical-domain codes verified Red (111.x organics — known
   informally but unusable deterministically); state-vs-central: CPCB table
   adopted by MPCB circular (joint application); no MPCB-vs-CPCB conflict
   recorded for the listed codes. The table must be treated as versioned
   regulatory data, not code constants — and it is absent.
Conclusion: knowing category *names* is not a classification mapping.
Deferred (pre-existing reason verified). No change.

## 5. R-015 Multi-Activity/Aggregation Audit

Single activity: R-014 lookup (deferred). Multiple activities: register
mandates UNKNOWN — UNK-002 ("no official aggregation rule found; engine
returns UNKNOWN"), ET-048 ("Convention flagged, not rule"), R-015 note
("maximum category convention must NOT be implemented", HIGH confidence
that no rule exists). No precedence, quantity-weighting, per-plant, or
per-source rule exists in the sources. ConditionNode has no aggregation
primitive (ApplicabilityOp is exactly eq/in/gte/lte/gt/lt — tested), and
none is introduced: the register *forbids* the only intuitive algorithm.
F-MPCB-01 is a per-activity LIST, so multi-code input is structurally
possible — precisely why the guard matters. New explicit deferral entry
(this audit's only pack-logic change); `_encode` now rejects with the
substantive reason instead of the generic UNKNOWN-guard message.

## 6. R-017 CTO Gate Audit

`CTO_REQUIRED := CONSENT_REQUIRED` with required_inputs `R-013` is a
register-level rule reference: legally plausible staging, architecturally
unrepresentable (no composition primitive). CTE (PRE_CONSTRUCTION,
"before establishing") and CTO (PRE_OPERATION, "before commencing
operation", precondition CTE) are distinct gates; CTO is not a corollary
of CTE — White-exempt units never enter the path, and operation-stage
state (production started, control systems in place) is workflow data the
decision path does not possess. "CTO exists as a type" (APR-009 SAFE) vs
"applicable now" vs "due" vs "renewable" (R-062/R-063/CMP-007, separately
gated) stay separated; no renewal logic imported (verified by assertion).
Dependency-engine proof: with CTE/CTO INSUFFICIENT_DATA and unobtained,
downstream APR-010 is BLOCKED on both — unknown consent propagates as a
blocker, never satisfaction. Deferred (pre-existing reason verified). No
change.

## 7. Fact Ontology Analysis

- F-MPCB-01 `cpcb_sector_codes`: LIST, per-activity, unknown_allowed False.
  Missing (None) always valid and fails closed; scalars/mappings rejected.
  LIST imposes no element check — element discipline would come from the
  undigitized table (documented in-test).
- Missing and NOT added: MPCB_CATEGORY (lookup output), sector table,
  scalar industry-type (no such label/key exists — verified), aggregation
  state. A scalar industry label is insufficient: the register keys on
  per-activity sector *codes* (111.1 vs 123.3 vs 117.4), and multi-activity
  needs a list + guard, which exists as input (F-MPCB-01) with R-015 as the
  guard.
- R-016 context facts (F-INC-01 derived, F-LOC-10) exist but R-016 is DNI.
- No GJ leakage (per-fact JURISDICTION_MISMATCH tested). Count 128
  before/after.

## 8. Evidence / Source Analysis

- T1: SRC-004 (consent guidelines; proves tied claims only), SRC-006
  (GSR 62/63 Gazette via MPCB; proves validity-fee text, not category
  mapping or MH implementation).
- T2: SRC-010 (MPCB adoption circular — scanned/OCR transcription risk),
  SRC-008 (working-day timelines; explicitly not category mapping).
- T4: SRC-011 (CPCB table mirror — lowest tier; determinism-critical
  lookup cannot rest on a mirror).
- Conflicts recorded, none silently chosen: UNK-031 (timeline columns),
  UNK-001/UNK-032 + CON-006 + UR-05 (validity/renewal/legacy CTOs),
  UNK-002 (aggregation), UNK-003 (deemed CTE), UR-18 (clock start/scope).
- Loaded pack contains zero consent sources, SLA rows, documents, or
  evidence hints for APR-008/009 (verified) — consistent with deferral.

## 9. Chain Architecture

PROJECT ACTIVITIES (F-MPCB-01 list) → R-014 lookup (E: no table/operator)
→ R-015 aggregation (D: mandated UNKNOWN, MAX forbidden) → R-013
applicability (D: needs both) → CTE stage → R-017 (D: needs R-013 output)
→ CTO stage. Direction confirmed (establish→operate; precondition CTE;
DEP-009 CTE/CTO→APR-010 loaded pair behaves correctly). Statutory links:
Water s.25/Air s.21 + CPCB/MPCB instruments. Rule-derived: none encodable
(no composition). Workflow: CTE-before-CTO staging, DEP-002 EC practice
(correctly UNKNOWN/inferred-out), DEP-008 BP-before-CTE (triaged-out).
Unsupported: lookup, aggregation, composition. The engine stops at the
first unsupported link by construction (all four deferred).

## 10. Approval Semantics

APR-008 vs APR-009: distinct stages/triggers/preconditions/validity (table
in §2). Renewal (CMP-007/CON-006), amendment (R-055/APR-053), expansion
limits (R-063/SLA-036), validity regime (R-062), integrated single-step
consent (GSR-02 confirmation item), deemed CTE (R-016 DNI, ET-072/073
never-granted — same discipline as R-081) all stay separate items. No
duplication of APR-008/009 (no active rules target them). No new approval
created.

## 11. Implementation Classification

- R-013: **D** — missing MPCB_CATEGORY fact + undigitized lookup +
  unrepresentable composition.
- R-014: **E** — LOOKUP architecture not representable (operator + T4
  table absent).
- R-015: **D** — aggregation capability missing *and* the intuitive
  algorithm explicitly forbidden.
- R-017: **D** — composition with R-013 unrepresentable; lifecycle gate
  without stage state.

## 12. Rules Implemented

Zero ApprovalRules. Only change: R-015 explicit deferral entry (fail-closed
message upgrade; loaded pack identical).

## 13. Rules Deferred / Confirmation-Gated

- Deferred 59: R-013/R-014/R-017 (pre-existing, reasons verified verbatim)
  + R-015 (new, guard character + MAX prohibition + UNK-002).
- R-016 stays DNI; GSR-02/CMP-007/R-062/R-063/UNK-001/UNK-031/UNK-032 stay
  in their confirmation/unknown lanes.
- Sets remain disjoint (tested).

## 14. Tests and Validation

`backend/tests/test_mh_consent_category_chain.py` — 60 tests: baseline,
CSV-read identity matrix (register, rules, approvals, sources, edge,
unknowns, requires_confirmation), R-013 classification-dependence,
R-014 table audit (T4 tier, OCR, partial codes, operator set, informal-
knowledge-must-fail-closed), R-015 guard (register text, UNK-002, ET-048,
reason content, LIST input shape, no scalar type, deferred-over-UNKNOWN
priority), R-017 gate (rule-reference input, lifecycle split, White path,
dependency-engine BLOCKED proof, no renewal import), fact ontology,
approval semantics (incl. ET-072 never-granted), isolation,
classification. One draft assertion fixed to actual LIST validator
behavior (no element check — documented as further R-014 evidence); two
prior baseline pins updated 58→59. Full suite 1869 passed; ruff clean;
tsc clean.

## 15. Jurisdiction Isolation

DEFAULT IN-GJ; GJ 19 approvals untouched (no chain IDs/approvals); MH 26
active untouched; F-MPCB-01 GJ-rejected; no GJ sources in MH logic.

## 16. Remaining Evidence Gaps

Digitized versioned CPCB/MPCB table (T1/T2, post-2025-06-23 currency);
official multi-activity aggregation rule (UNK-002 OPEN, MPCB
clarification); MPCB_CATEGORY derivation path; CTE↔CTO lifecycle state
model; legacy-CTO/fee treatment (UNK-001/UNK-032, UR-05, CON-006); timeline
columns (UNK-031) and clock start (UR-18); deemed-CTE operability
(UNK-003); integrated-consent portal wiring (GSR-02). Engine still lacks
lookup, aggregation, composition, and grant primitives — by design.

## 17. Architecture Implications

The chain proves the engine's lawful stopping points: leaf/AND/OR/NOT +
three-valued logic can *hold* uncertainty (INSUFFICIENT_DATA, mandated
UNKNOWN) but cannot *resolve* classification, aggregation, or composition.
Any future consent engine needs, in order: (1) a versioned classification
dataset (not code constants), (2) an explicit aggregation decision point
defaulting to UNKNOWN, (3) a composition mechanism that preserves
provenance per link — each gated on primary evidence. Nothing in this
audit contradicts the current architecture; it validates the deferral
mechanism as the correct boundary enforcer.

## 18. Next Cluster Recommendation

From CURRENT registers: HW authorisation content chain — R-018 is active
but its Schedule-I entry mapping per waste stream is only PARTIALLY
resolved (UNK-014: unit-level mapping needs process facts; post-2016
amendments UNK-034), with R-096 (Schedule-II characteristics) active and
DEP-009 CTE/CTO-gated. Auditing what R-018 actually decides per stream
vs what it assumes would test an *active* rule against evidence — the
first such audit. Do not cut over DEFAULT_JURISDICTION; do not digitize
tables without a demo-driven need.
