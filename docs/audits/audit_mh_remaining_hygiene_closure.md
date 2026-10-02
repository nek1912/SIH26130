# Maharashtra Remaining-Hygiene Closure Audit — R-059 / R-071 / R-072 / R-076

Terminal documentary closure for the last four inventory entries. Companion
to the parallel `test_mh_residual_hygiene.py`, which covers register
identity, non-approval targets, source sanity, consumer absence, and fact
linkage; this audit adds the disposition reasoning and the few structural
pins that suite lacks. Jurisdiction IN-MH (primary), IN-GJ regression-only.
Date (UTC): 2026-09-29. Source: v5 registers
(`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`).

## 1. Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"`. Unchanged.
- MH active 26, MH deferred 61, MH confirmation 26, MH DNI 3, MH UNKNOWN 3,
  MH facts 128, GJ active 19 — all unchanged by this task.
- Suite **2239 passed** (2228 prior-verified + 11 new closure tests), 0
  failed; ruff clean; frontend untouched (no tsc needed — zero UI/API
  surface change).
- Pre-existing + parallel uncommitted work preserved; this task's footprint:
  11-test supplementary file, this document, two one-line status entries.

## 2. R-059 audit — incentive hard-stop

`INCENTIVE_VALUE := NOT_COMPUTED` (INC-*, RULE_LOGIC, GUARD_OR_ROUTING,
no authority/jurisdiction/stage/inputs/thresholds, T3 SRC-073/074, "Hard
stop", ET-043 pins any→NOT_COMPUTED). Legal basis literally "PSI under
IISP 2025 not located" (pinned) — there are no criteria to compute, so no
incentive rule can become APPLIES/DOES_NOT_APPLY on this basis. Semantic
home: incentives assessment discipline, already structural —
`SchemeRelevance` carries no monetary fields (pinned field set), and the
engine computes relevance only. T3 portal evidence is sufficient for the
negative claim it actually makes (absence of a PSI 2025 instrument), never
for activation. Not approval applicability; no ApprovalRule encoding
possible (no approval target, no authority, no inputs).

## 3. R-071 audit — regime date gate

`MH_GW_ACT_IN_FORCE := TRUE from 01-06-2014` (CND-024, RULE_LOGIC, T1
SRC-131/132 s.1(3)/s.8, EXACT date, VERIFIED; deep-well branch evaluated by
deferred R-097; Rules 2018 DRAFT). TRUE-from date pinned; register "Do not
return FALSE" note pinned — the only dangerous reading (missing downstream
data negating the Act's force) is explicitly forbidden, and ET-111 keeps
Act-status-UNKNOWN separate from the CGWA branch. F-WAT-05 linkage is
orphan (gate is date-only; the fact belongs to CND-024's deciding facts),
spurious but harmless since the rule is unconsumed. No FALSE is ever
returned from missing data by construction (nothing evaluates it). Not an
ApprovalRule (CND-024 is a condition, not an approval); belongs as regime
context to R-097/groundwater logic when that work proceeds. R-097 itself
is untouched.

## 4. R-072 audit — assignment-triggered duty

`ENV_AUDIT := CONDITIONAL (only when assigned by authority or engaged by
proponent)` (CMP-014, RULE_LOGIC, T1 SRC-066 scope, effective 2025-08-29,
VERIFIED_CONDITIONAL). Source establishes NO blanket obligation (pinned
from SRC-066's does-not-prove). No project fact represents the assignment
trigger (only assign/engag-labelled fact is unrelated F-LAB-10; pinned).
Twin of CMP-014, already DO_NOT_IMPLEMENT_YET — the compliance layer owns
this decision. No assignment cases invented. Not an ApprovalRule.

## 5. R-076 audit — deadline facet

`EC_COMPLIANCE_DUE := 1 June and 1 December each year after EC` (CMP-006,
RULE_LOGIC, T1 SRC-001 para 10(ii), effective 2026-07-13, VERIFIED).
Attribution tension resolved: SRC-001's row disclaims para-9/10 extraction,
but UNK-017 (CLOSED_V3) and CMP-006.frequency_deadline corroborate the date
pair three ways (pinned) — content corroborated, locator attribution
unresolved, blocking nothing. "EC granted" trigger state is unmodeled
(pinned absent) and CMP-006 itself is LOW/requires-confirmation, so no
automation may consume the pair today; the fixed-date mechanics that could
serve it later exist but are unused for CMP-006. Deadline stays in
CMP-006.frequency_deadline — its existing, correct home. Not an
ApprovalRule. No edge tests exist for R-072/R-076 (pinned).

## 6. Cross-rule semantic ownership

Exactly one authoritative home each, no duplicates: R-059 → incentives
assessment (NOT_COMPUTED posture structural); R-071 → R-097/CND-024
groundwater context (date gate unconsumed); R-072 → CMP-014 (DNI twin);
R-076 → CMP-006.frequency_deadline (unexecuted deadline text). Four
distinct targets (INC-*/CND-024/CMP-014/CMP-006) and four distinct titles
(pinned); zero pack authorities/edges/documents, zero live approval
targets, zero frontend/orchestration references (verified by search; only
tests + the R-097 deferral reason mention CND-024, consistently).

## 7. Evidence status

Per-condition sources: T3 portal-absence (R-059, sufficient for its
negative claim), T1 Act text + commencement (R-071) with UNK-012 partial
(Rules 2018/GSDA role), T1 Audit Rules scope (R-072), T1 consolidated EIA
+ UNK-017 + compliance corroboration (R-076, locator tension noted).
Missing evidence that would matter only for other layers: PSI 2025
instrument (incentives), GSDA role (groundwater), assignment cases
(audit), EC-grant state (deadline automation). Nothing missing for the
closure decision itself.

## 8. Classification

- R-059: **DNI-as-ApprovalRule** (never modelable: no approval, authority,
  or inputs; hard stop already structural).
- R-071: **documented-hygiene** (date gate with regime home at R-097;
  FALSE forbidden by register note).
- R-072: **DNI-as-ApprovalRule** (twin of CMP-014 DNI; no trigger fact).
- R-076: **documented-hygiene** (deadline facet owned by CMP-006 text).
Documentary dispositions (register implementation_status SAFE describes
their RULE_LOGIC meaning, not ApprovalRule candidacy); no code status
entries added — forcing them into DEFERRED would imply future ApprovalRule
activation that must never happen, and into code-DNI would contradict the
register. Status sets intentionally unchanged.

## 9. Implementation decision

Zero pack/engine/fact changes. Supplementary tests only (11, all passing).
The inventory's UNTRIAGED set (R-059/071/072/076) is hereby declared
terminal documented-hygiene: "untriaged" means no code status entry, which
is the correct terminal state for non-ApprovalRule logic, with rationale
and pins now on record here and in both test files.

## 10. Regression results

New file 11 passed; parallel residual suite green; full backend 2239
passed; ruff clean. No production behavior change possible (no production
file touched): verified by suite + diff review.

## 11. Final untriaged inventory

R-059, R-071, R-072, R-076 — closed as terminal documented hygiene (this
document). Remaining register work is ordinary deferred/confirmation
lanes, not untriaged items. Counts: 26 active / 61 deferred / 26
confirmation / 3 DNI / 3 UNKNOWN / 128 facts / 19 GJ.

## 12. Exact next task

No further inventory-closure work exists. Recommended: R-044 domestic-
exemption migration (EXEMPTION inside the live APR-043 composition —
smallest scoped migration; triggers R-044/R-077 already named) with fresh
pins, per the R-043 audit's §14. R-002/APR-001 migration may proceed in
parallel per its open gate. No facts/evidence work required for either.
