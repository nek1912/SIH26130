# Maharashtra MIDC Lifecycle Tail Audit — R-039, R-040, APR-031, DEP-019

Follow-up to `audit_mh_workflow_lifecycle.md`. Jurisdiction: IN-MH
(primary). IN-GJ is regression-only. Date (UTC): 2026-09-29. Authoritative
source: v5 regulatory registers
(`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`).

## 1. Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"`. Unchanged.
- Before: MH active 26, MH deferred 58, MH confirmation 26, GJ active 19,
  MH facts 128, suite 1750 passed.
- After: MH active 26, MH deferred 58, MH confirmation 26, GJ active 19,
  MH facts 128, suite **1809 passed** (1750 + 59 new). Zero pack-logic
  change beyond one strengthened deferral rationale (DEP-019).
- Ruff clean (`app/`, `tests/`). Frontend `tsc --noEmit` clean.
- Pre-existing uncommitted work from earlier clusters left untouched; this
  task adds one test file, this artifact, one rationale edit, and minimal
  doc entries.

## 2. Candidate Identity Matrix

From CURRENT registers (prompt labels verified field-by-field; one
correction: the tail is tree-felling + change-of-activity, not a building-
permission lifecycle tail):

| Candidate | Register identity | Stage / type | Authority | Jurisdiction | Status |
|-----------|-------------------|--------------|-----------|--------------|--------|
| R-039 | "MIDC tree felling permission", `TREE := F-SITE-01==TRUE AND (MIDC_BRANCH -> APR-036; NOT MIDC AND F-LOC-06==TRUE -> APR-042; else UNKNOWN)`, inputs F-SITE-01/F-LOC-01/F-LOC-06, legal basis "MIDC service; Trees Act 1975" | PRE_ESTABLISHMENT / APPROVAL, PRE_CONSTRUCTION | AUT-010 (MIDC branch) / AUT-022 (urban branch) | MIDC + NON_MIDC (dual) | REQUIRES_OFFICIAL_CONFIRMATION (T3 SRC-043/070, MEDIUM, effective UNKNOWN) |
| R-040 | "MIDC change in manufacturing activity", `MIDC_CHANGE := MIDC_BRANCH AND F-EXP-01==TRUE AND product/activity changes`, inputs F-LOC-01/F-EXP-01, legal basis "MIDC service" | OPERATION / APPROVAL, MODIFICATION lifecycle | AUT-010 | MIDC | REQUIRES_OFFICIAL_CONFIRMATION (T3 SRC-043, MEDIUM, effective UNKNOWN) |
| APR-031 | "MIDC plinth / commencement e-intimation", rule R-036, trigger "Construction in MIDC" | PRE_ESTABLISHMENT stage but **REGISTRATION record_class / REPORT record_type / CONSTRUCTION lifecycle** | AUT-010 (intimation recipient, no decision) | MIDC | approval-level SAFE, rule-level confirmation-gated |
| DEP-019 | APR-029 (plot allotment) -> APR-030 (building permission), LEGAL_PRECONDITION, "issued to plot holder" | workflow ordering | — | MIDC | VERIFIED_CONDITIONAL but **YES_INFERRED**, MEDIUM, T3 SRC-043 service list |

Approvals context: APR-036 (MIDC tree, APPROVAL/PRE_CONSTRUCTION, rule
R-039, SAFE); APR-037 (MIDC change, APPROVAL/OPERATION/MODIFICATION, rule
R-040, SAFE); APR-042 (urban tree, APPROVAL/PRE_CONSTRUCTION, AUT-022,
Trees Act 1975 provision, LOW, REQUIRES_CONFIRMATION). AUT-022 notes "Act
text not fetched in this pack"; routing unresolved (UR-17 OPEN). No edge
tests cover R-039/R-040. SLAs SLA-021 (45 d portal, CON-001 conflicted) and
SLA-022 (21 d portal, VERIFIED) exist but are display-only, unloaded.

## 3. R-039 Audit

- Not pure applicability: the `F-SITE-01==TRUE` conjunct is a predicate,
  but the parenthesised fork routes to two different approvals under two
  authorities — approval routing embedded in the rule. ConditionNode has no
  rule-reference/routing primitive; a single ApprovalRule cannot span
  AUT-010/AUT-022 across MIDC/NON_MIDC.
- MIDC branch: T3 portal-only (same UR-19 gap as R-036/R-037).
- Non-MIDC branch: cites Trees Act 1975, but the Act text was never
  fetched; confidence LOW; urban-area + Tree-Officer routing unresolved;
  SRC-070 is a MAITRI integration listing proving tied claims only.
- Facts exist with correct UNKNOWN semantics (F-SITE-01/F-LOC-01/F-LOC-06
  all BOOL_OR_UNKNOWN; engine-verified three-valued), but evidence and
  routing block encoding. Effective UNKNOWN → temporal queries fail closed.
- Confirmation gate (already in `MH_REQUIRES_CONFIRMATION_RULE_IDS`, not
  SAFE-listed, `_encode` rejects) is correct. No change.

## 4. R-040 Audit

- A MODIFICATION-lifecycle change event (the only one in the MIDC chain):
  OPERATION stage, trigger UNKNOWN, precondition UNKNOWN. Change events are
  workflow state, not project applicability.
- Core conjunct `product/activity changes` has no fact: F-EXP-01 means
  expansion/modernisation for EC 7(ii)/MPCB and is BOOL *without* UNKNOWN,
  so unknown changes cannot even be represented (validation rejects the
  UNKNOWN token — tested). Reusing F-EXP-01 would corrupt EC/MPCB semantics.
- Sole source T3 SRC-043 ("MIDC service"/"MIDC lease/service", no statutory
  provision). Effective UNKNOWN. No edge tests.
- Confirmation gate already held; `_encode` rejects. No change.

## 5. APR-031 Report-vs-Approval Audit

1. Not legally an approval: record_class REGISTRATION.
2. It is a report/submission (record_type REPORT, e-intimation).
3. Generated after APR-030 (commencement follows permission; DEP-004 bundles
   the BP+fire decision separately).
4. Does not independently authorize proceeding.
5. No authority decision (intimation recipient only).
6. No separate applicability condition (sole rule R-036, shared bundle).
7. Readiness/workflow artifact of the CONSTRUCTION lifecycle.
8. Correctly unmodeled: zero references in `backend/app`, frontend,
   orchestration, readiness, or tests; loaded pack carries no APR-031
   authority entry, edge, SLA record, or source.
9. No rule equates it with APR-030/032/038/041.
10. Registry vocabulary (REPORT/REGISTRATION) is preserved as-is; no code
    change needed or made.
Final classification: **REPORT** (registration/intimation artifact).

## 6. DEP-019 Audit

1–2. Not primary, not regulatory text: T3 service-list page.
3–5. Inferred from portal navigation/service ordering (YES_INFERRED).
6. At most a readiness/workflow ordering note ("issued to plot holder").
- Stays deferred; rationale strengthened to record YES_INFERRED + MEDIUM +
  T3-only basis so uncertainty is preserved in the codebase, not just in
  this report. Never elevated to statutory dependency.
- Impact of absence: none — APR-030 has no active rule; APR-029's active
  R-035 is a location guard needing no BP input; loaded pack deps remain
  exactly DEP-009 ×2. Sibling MIDC edges DEP-003/DEP-004 likewise absent.

## 7. Cross-Rule Architecture Analysis

```
APPLICABILITY (deferred/gated predicates): R-039? no — routing fork;
  R-040? no — change event; R-041 (non-MIDC BP, deferred)
APPROVAL IDENTITY: APR-036/APR-037 (MIDC tree/change, gated rules);
  APR-042 (urban tree, gated); APR-030/032/033 (SAFE approvals, gated rules)
DEPENDENCY/READINESS: DEP-009 ×2 loaded; DEP-003/004/019 triaged out
WORKFLOW/SUBMISSION: APR-031 e-intimation (REPORT, unmodeled)
STATUTORY DECISION: none active in tail (R-035 guard only)
POST-APPROVAL/RENEWAL: APR-037 MODIFICATION (gated); R-099 (deferred)
```

R-035 stays the sole active MIDC router; R-039's embedded fork adds no
parallel routing. Fire chain (R-078/R-079/R-042/R-099) untouched — APR-042
(tree) shares only numbering adjacency with APR-040 (final fire NOC).
Consent chain R-013/014/015 explicitly out of scope (next cluster).

## 8. Fact Ontology

- F-SITE-01 `trees_to_fell` (bool, unknown): correct.
- F-LOC-06 `urban_area` (bool, unknown): correct.
- F-EXP-01 `is_expansion_or_modernisation` (bool, NO unknown): correct for
  EC/MPCB use; must not be repurposed for product changes.
- F-LOC-01 (bool, unknown): branch fact, correct.
- No workflow timestamps added to the 128 regulatory facts (R-040 change
  events belong to application/case state when such a subsystem exists).
- No GJ leakage (JURISDICTION_MISMATCH enforced, tested per fact).

## 9. Evidence Status

- T3 portal (SRC-043/044/045/047): service existence + portal timelines
  only; MIDC DCR text missing (UR-19 OPEN, shared with R-036/R-037).
- T3 MAITRI (SRC-070): integration listing only; not in loaded pack.
- Trees Act 1975: cited but unfetched → LOW, UR-17 routing OPEN.
- No primary provision for R-040 (lease/service listing only).
- Conflicts preserved, not silently chosen: CON-001 (SLA-021 45 vs 60 d),
  CON-001B/C (MIDC BP/fire timelines). SLA-021/022 unloaded; no deadline
  computed; SLA expiry never treated as permission.

## 10. Implementation Classification

- R-039: **C** — evidence incomplete / confirmation-gated (routing fork +
  portal-only MIDC branch + unfetched Act on urban branch).
- R-040: **C** — evidence incomplete / confirmation-gated (portal-only +
  unmodeled change fact + modification-event semantics).
- APR-031: **REPORT** — correctly unmodeled; no action.
- DEP-019: **inferred ordering** — deferred with strengthened rationale.

## 11. Rules Implemented

Zero. Only change: DEP-019 rationale text (no semantic effect; loaded
edges still DEP-009 ×2).

## 12. Rules Deferred / Confirmation-Gated

- R-039, R-040: confirmation-gated (pre-existing, verified correct).
- DEP-019 (+DEP-003/004): deferred (rationale now evidence-explicit).
- Active/deferred/confirmation sets remain disjoint.

## 13. Tests and Validation

`backend/tests/test_mh_midc_lifecycle_tail.py` — 59 tests: identity,
branch-vs-predicate, triple-target, REPORT boundary (incl. zero code
modeling), DEP-019 inferred status + zero impact, UNKNOWN/missing/invalid
per fact (incl. F-EXP-01 UNKNOWN rejection), no portal-to-statutory
inference, cross-rule separation, isolation, classification. Full suite
1809 passed; ruff clean; tsc clean.

## 14. Jurisdiction Isolation

DEFAULT IN-GJ; GJ 19 approvals untouched (no tail IDs); MH 26 active
untouched; tail facts GJ-rejected per fact; no GJ sources in MH logic.

## 15. Remaining Evidence Gaps

UR-19 (MIDC DCR text for R-036/R-037, also covering R-039 MIDC branch and
APR-031 legal footing); Trees Act 1975 text + Tree Authority mapping
(UR-17); product/activity-change fact definition + modification-event state
model; APR-037 lease/service provision; UDCPR currency (prior audit).
Engine still deliberately lacks composition, dynamic authority, regime,
DATE, and grant primitives.

## 16. Next Cluster Recommendation

From CURRENT registers: the R-013/R-014/R-015 consent-category chain
(sector lookup table + UNKNOWN cardinality guard) gating CTO applicability
R-017 — the largest remaining composition block, explicitly scoped out of
this task. Do not cut over DEFAULT_JURISDICTION; do not digitize GIS/lookup
tables without a demo-driven need.
