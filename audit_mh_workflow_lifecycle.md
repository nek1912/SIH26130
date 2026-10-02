# Maharashtra Regulatory Engine Audit — Workflow/Lifecycle Cluster (R-081, R-099, R-036)

Follow-up to `audit_mh_fire_building.md`, which named these three
SAFE-but-untriaged workflow/lifecycle candidates as the next audit.
Jurisdiction: IN-MH (primary). IN-GJ is regression-only.
Date (UTC): 2026-09-29. Authoritative source: v5 regulatory registers
(`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`).

## 1. Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"` (`backend/app/seed/pack.py`). Unchanged.
- Before: MH active 26, MH deferred 56, MH confirmation 26, GJ active 19,
  MH facts 128, suite 1692 passed.
- After: MH active 26 (unchanged), MH deferred **58** (+R-081, +R-099),
  MH confirmation 26 (unchanged; R-036 already gated), GJ active 19,
  MH facts 128 (unchanged), suite **1750 passed** (1692 + 58 new).
- Ruff clean (`app/`, `tests/`). Frontend `tsc --noEmit` clean.
- Pre-existing uncommitted work from earlier clusters (ARCH/PRD/RULES/
  approvals diffs + 4 untracked test files) left untouched; this task adds
  only 2 deferred entries, 1 test file, this artifact, and minimal doc
  entries.

## 2. Candidate identity matrix

From CURRENT `rule_register_v5.csv` / `rules.csv` ( register differs from no
old note; prompt labels verified below):

| Rule | Title (register) | Approval(s) | Stage / lifecycle | Authority | Jurisdiction | Status / implementation | Sources / effective |
|------|------------------|-------------|-------------------|-----------|--------------|-------------------------|---------------------|
| R-081 | Building/development permission (non-MIDC planning authority) | APR-038 (non-MIDC BP) | PRE_ESTABLISHMENT / PRE_CONSTRUCTION | AUT-011 (planning authority, site-dependent) | NON_MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE | SRC-123 T1 s.45(5)+provisos; 1966 YEAR_ONLY |
| R-099 | Final fire NOC (non-MIDC) | APR-040 (final fire NOC) | PRE_OPERATION | AUT-012 (fire authority, site-dependent) | NON_MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE | SRC-145 T2 (31-01-2025 paras 3,4,6 + 30-10-2014); EXACT 2023-05-30 |
| R-036 | MIDC combined building permission + provisional fire NOC | APR-030 (combined BP+fire, APPROVAL/PRE_CONSTRUCTION); APR-031 (plinth/commencement e-intimation, REGISTRATION/REPORT/CONSTRUCTION); APR-033 (MIDC final fire NOC, NOC/PRE_OPERATION) | PRE_ESTABLISHMENT (rule) spanning 3 stages | AUT-010 (MIDC) | MIDC | REQUIRES_OFFICIAL_CONFIRMATION / REQUIRES_CONFIRMATION | SRC-043/SRC-044 T3 portal; effective UNKNOWN |

Approvals (`approvals.csv`): APR-030 combined service (R-036, SAFE); APR-031
plinth/commencement REPORT (R-036, SAFE); APR-033 MIDC final fire NOC (R-036,
SAFE); APR-038 non-MIDC BP (R-041, REQUIRES_CONFIRMATION); APR-040 final fire
NOC non-MIDC (R-042;R-099, REQUIRES_CONFIRMATION; renewal NONE under Fire Act,
CONDITIONAL on other statutes; Form B is OPERATING_DUTY FR-04).
Authorities: AUT-010 VERIFIED (MIDC estates); AUT-011 / AUT-012
REQUIRES_CONFIRMATION, site-dependent, never defaulted.

Prompt labels confirmed with one emphasis: R-036 is not one permission but a
portal-bundled triple (BP + intimation + final fire) across three stages.

## 3. Per-rule audit

### R-081 — Deemed permission (E)

- (A) Not applicability. Answers "has permission been deemed after 60 days
  without decision?" — a procedural consequence (`BP_DEEMED_POSSIBLE`),
  not "does APR-038 apply?". The condition text itself orders: "engine must
  never assert deemed permission as granted".
- (B) ConditionNode cannot represent it: needs DATE arithmetic (60 d from
  application or requisition-reply, whichever later), a DCR-conformance
  proviso (strict conformity to DCR and plans), and authoritative workflow
  timestamps. Operator in register is DATE; engine has eq/in/gte/lte/gt/lt
  + AND/OR/NOT/literal only. No new primitive justified.
- (C) Source is strong (SRC-123 T1, MRTP s.45(5), HIGH) and SLA-042 (60 d,
  LEGAL, VERIFIED_CONDITIONAL) exists — but strength of the *provision*
  does not cure the missing *inputs and state*. Deemed permission valid
  ONLY IF DCR-conformant, which the engine cannot verify.
- (D) Both required facts (application date; requisition reply date) are
  absent from the 128-fact registry. This is category 1: rule stays
  deferred; the dates belong to workflow/context (application case state),
  not project applicability facts. No fact added.
- (E) Lifecycle: PRE_CONSTRUCTION consequence layered on APR-038; must not
  merge with R-041 applicability. (F) Authority AUT-011 site-dependent;
  deferral defaults nothing.
- (G) Deemed permission: consequence, triggered by 60 d silence +
  conformance; elapsed time not computable (no authoritative dates/statuses
  in the decision path); system must never declare statutory grant.
  Deferred.

### R-099 — Fire renewal conditional (E)

- (A) Not applicability. `FINAL_FIRE_APPROVAL_RENEWAL` answers "is renewal
  due under some other statute?" TRUE yields CONDITIONAL (renewal per that
  Act/Rule), FALSE yields DOES_NOT_APPLY, UNKNOWN stays UNKNOWN — never
  APPLIES. Encoding as an APR-040 ApprovalRule would misrepresent a pointer
  to another statute as "final fire NOC applies".
- (B) Register operator is CASE; the three-valued input maps onto boolean
  logic, but the *outputs* (CONDITIONAL-as-renewal-pointer) have no
  ApprovalRule semantics. No new primitive; deferral instead.
- (C) Sources T2 circulars (SRC-144 2014 + SRC-145 2025, HIGH) + resolved
  CON-013 (both texts agree: no renewal under the Fire Act; s.3 proviso
  adds renewal-only-if-another-Act-requires). General principle FR-01
  (DOES_NOT_APPLY, VERIFIED) is settled; the chemical-sector exception
  FR-03 is not (CON-024 T2-vs-T1, UR-04 PARTIAL).
- (D) F-FIR-20 exists (boolean, unknown-allowed, used_in R-099) — input
  side modeled. ET-v4-01/02/03 + ET-v5-17 verified by engine tests:
  TRUE→(conditional semantic, deferred), FALSE→DOES_NOT_APPLY,
  UNKNOWN/missing→INSUFFICIENT_DATA never FALSE; PESO licence alone leaves
  F-FIR-20 UNKNOWN. Fact sufficient; conclusion unsafe.
- (E/H) Lifecycle RENEWAL vs applicability; "fire approval exists" (APR-040
  via R-042/R-079 chain) vs "renewal due" (R-099) kept distinct. No expiry
  computed (no approval-date + validity-period pair available; FR-07 portal
  renewal listing is PORTAL_LEGACY, never a trigger). Form B Jan/Jul is a
  separate OPERATION REPORT (FR-04, CMP-008 SAFE) evaluated independently.
- Deferred.

### R-036 — MIDC building permission (C, unchanged)

- (A/I) Portal/workflow bundle, not statutory applicability: T3
  SRC-043/044 prove service existence + portal timelines only (source
  `does_not_prove` fields; UR-19 OPEN: MIDC DCR gazette missing).
  Condition needs absent `construction` fact (same gap as R-041).
  Triple target spans APPROVAL + REPORT + NOC across PRE_CONSTRUCTION /
  CONSTRUCTION / PRE_OPERATION — duplicate-concept hazard vs R-037 (MIDC
  OC), R-041 (non-MIDC BP), R-080 (BP authority), R-082 (DCR regime).
- Already confirmation-gated (`MH_REQUIRES_CONFIRMATION_RULE_IDS`,
  `_encode` rejects as not-safe — same precedent as R-037). ET-v5-28 expects
  REQUIRES_CONFIRMATION. No change; no portal-to-statutory inference.
- MIDC BP dependencies (DEP-003 CTE-for-BP, DEP-004 bundled BP+fire,
  DEP-019 plot-holder precondition) remain correctly triaged out of the
  pack (out-of-scope / non-approval / inferred).

## 4. Applicability vs workflow/lifecycle classification

| Candidate | Answers | Class |
|-----------|---------|-------|
| R-081 | "is permission deemed after 60 d silence?" (consequence) | workflow/lifecycle |
| R-099 | "is renewal due under another statute?" (renewal pointer) | lifecycle/renewal |
| R-036 | "which MIDC portal services exist for constructor plot-holders?" | portal workflow + confirmation gate |
| (reference) R-041 | "does non-MIDC BP apply?" | applicability (deferred, missing fact) |
| (reference) R-079 | "is the building Schedule-I?" | applicability fragment (deferred, needs guard) |

SLA-042/043 (60 d deemed clock; 40 d appeal) and SLA-015/017/023/024 (MIDC
portal timelines, several confirmation-gated under CON-001) stay display
metadata; none enters applicability.

## 5. Fact analysis

- Present with correct UNKNOWN semantics: F-LOC-01, F-LOC-05, F-PA-02,
  F-BLD-10/11 (prior audit), F-FIR-20 (this cluster; boolean/unknown-allowed).
- Absent and correctly NOT added: `construction` (R-036/R-041 core
  conjunct), application date, requisition-reply date. These belong to
  workflow/case state or future researched facts, not convenience additions.
- F-FIR-20 validated: TRUE/FALSE/UNKNOWN + missing all behave
  three-valued; invalid values rejected; `None` always valid; IN-GJ lookup
  raises JURISDICTION_MISMATCH (`code` asserted).
- Count: 128 before/after.

## 6. Evidence analysis

- T1: SRC-123 (MRTP s.44/s.45 deemed-60d-if-conformant/appeal; does NOT
  prove authority identity), SRC-121 (fire approval + Schedule-I; does NOT
  prove site CFO or building class).
- T2: SRC-145 (no renewal under Fire Act + s.3 proviso; does NOT list which
  other Acts require renewal for chemical units), SRC-144 (2014 twin).
- T3 portal: SRC-043/044/045/047/048 prove tied claims only; MIDC DCR text
  missing (UR-19 OPEN); portal timelines conflicted (CON-001/001B/001C
  resolved as display-all; RTS legal limits separate).
- Resolved: CON-013 (not a conflict). Unresolved: CON-024 + UR-04 (FR-03
  annual-renewal claim vs T1 PESO texts showing licence validity only).
- Loaded pack carries 22/188 sources (SRC-043/044 in; SRC-123/145 out) and
  10 SLA rows (none of SLA-015/017/023/024/042/043) — consistent with
  deferring all three candidates.

## 7. Cross-rule/dependency analysis

```
R-035 (active guard) → MIDC branch: R-036 (confirmation-gated bundle)
  DEP-003/004/019 triaged out; APR-030→APR-008 CTE need noted, not encoded
R-035 → non-MIDC: F-LOC-05 → R-080/R-082 (deferred) → R-041 (deferred)
  → APR-038 → R-081 deemed clock (deferred; SLA-042 display only)
F-BLD-10 → R-079 (deferred) → R-042 (confirmation: F-LOC-01==FALSE AND
  R-079, authority R-078, renewal R-099) → APR-040 → R-099 (deferred)
  → F-FIR-20 (modeled) + FR-03 (unresolved); Form B via CMP-008 separate
```

R-042 is the composition hub: it references two deferred rules (R-078,
R-079) and one deferred renewal (R-099) — triple composition the engine
cannot express, so its confirmation gate is correctly held. No candidate
independently establishes applicability; none provides mere readiness for an
active rule; no regime selection beyond already-deferred R-082.

## 8. Implementation classification

- R-081: **E** — routing/workflow/regime/lifecycle, not applicability.
- R-099: **E** — renewal/lifecycle, not applicability.
- R-036: **C** — evidence incomplete / confirmation-gated (unchanged).

## 9. Rules implemented

Zero ApprovalRules. Only change: R-081 + R-099 added to `MH_DEFERRED_RULES`
with substantive fail-closed reasons (both SAFE-listed, so the deferred
check fires first in `_encode`). No builder, no engine change, no new fact,
no new primitive.

## 10. Rules deferred/confirmation-gated

- Deferred (58): +R-081 (deemed-consequence + DATE + conformance + no-grant),
  +R-099 (renewal-pointer + FR-01/CON-013 + FR-03/UR-04 + Form B split).
  Both reject via `_encode` with explicit messages (tested).
- Confirmation-gated (26, unchanged): R-036 (portal-only, UR-19, ET-v5-28).
- Active/deferred/confirmation sets remain disjoint as required.

## 11. Tests and validation

`backend/tests/test_mh_workflow_lifecycle.py` — 58 tests: baseline counts,
per-candidate identity, R-081 deemed analysis (incl. absent date facts,
SLA-042 display-only, SRC-123 deferred, no false deemed), R-099 renewal
analysis (incl. F-FIR-20 engine TRUE/FALSE/UNKNOWN/missing, ET-v4-01/02/03,
ET-v5-17, SRC-145 deferred, no false renewal), R-036 portal analysis (gate
preserved, construction gap, service-only sources, no duplicates, deps
triage), cross-rule (R-042 hub, APR-038/APR-040 chains, R-035 active, no
rule-reference primitive), fact/evidence discipline, jurisdiction isolation,
classification. Two draft assertions fixed (reason substring; error-code
attribute). Full suite 1750 passed; ruff clean; tsc clean.

## 12. Jurisdiction isolation

DEFAULT IN-GJ; GJ 19 rules/approvals untouched (no APR-030/031/033/038/040);
MH 26 active untouched; MH↔GJ fact namespaces enforced
(JURISDICTION_MISMATCH); no GJ sources in MH logic.

## 13. Remaining evidence gaps

UR-19 (MIDC DCR gazette for R-036/R-037); `construction` fact definition;
application/requisition timestamps + DCR-conformance verification path for
any future deemed-workflow display (never a grant); FR-03/CON-024/UR-04
(sector renewal citation); post-30-01-2024 UDCPR currency (prior audit);
APR-041 sequencing source; R-042 guard resolution. Engine deliberately
lacks rule-composition, dynamic-authority, regime-selector, DATE-arithmetic
and grant-declaration primitives.

## 14. Recommended next cluster

From CURRENT registers: the MIDC lifecycle tail still un-audited as a
cluster — R-039/R-040 (MIDC tree felling, confirmation-gated T3), APR-031
intimation semantics vs APR-030 permission (REPORT vs APPROVAL boundary),
and DEP-019 inferred plot-holder precondition (LEGAL_PRECONDITION,
YES_INFERRED — the only inferred dependency in the MIDC chain). After that,
the R-013/R-014/R-015 consent-category lookup chain (sector table + UNKNOWN
cardinality guard) gates CTO applicability R-017 and is the largest
remaining composition block. Do not cut over DEFAULT_JURISDICTION; do not
digitize GIS/lookup tables without a demo-driven need.
