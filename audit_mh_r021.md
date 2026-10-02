# Maharashtra R-021 Closure Audit — MAH Derivation (APR-012)

Inventory-closure audit: R-021 was SAFE-listed but in no status set (one of
6 untriaged; 5 remain). Jurisdiction: IN-MH (primary). IN-GJ regression-
only. Date (UTC): 2026-09-29. Authoritative source: v5 registers
(`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`). Identity
verified executably against CURRENT CSVs at test time (discipline of
`test_mh_cto_renewal.py` / consent-chain / HW-chain suites). R-013–R-017,
R-018/R-096, EC-core, and all prior cluster outcomes untouched.

## 1. Scope

Close R-021 with exactly one disposition (ACTIVE / DEFERRED /
CONFIRMATION-GATED / DNI / UNKNOWN) on evidence, not coverage. No
activation to eliminate the untriaged count; no synthetic facts; no
threshold/authority invention; no new engine primitives.

## 2. Current Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"`. Unchanged.
- Before: MH active 26, deferred 59, confirmation 26, DNI 3, UNKNOWN 3,
  SAFE 76, GJ 19, facts 128, untriaged 6 (R-021/054/059/071/072/076).
- After: MH active 26, deferred **60** (+R-021), others identical, suite
  **2077 passed** (1980 baseline + 49 new R-021 + 48 parallel
  controlled-substance, landed independently).
- Ruff clean. Frontend `tsc --noEmit` clean.
- Pre-existing + parallel uncommitted work preserved; required fallout only:
  four deferred-count pins 59→60 (3 mine + HW-chain) and the parallel
  inventory's UNTRIAGED set minus R-021 (that file already anticipated the
  outcome).

## 3. Identity Verification

`rule_register_v5.csv` + `rules.csv` (test-pinned): R-021, "MSIHC -
notification of site / safety report / on-site emergency plan", APR-012,
obligation **REPORT**, jurisdiction "CENTRAL rules, state authority",
stage PRE_ESTABLISHMENT, rule_kind DETERMINISTIC, status
VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, T1 SRC-016, effective 2000
YEAR_ONLY. Condition: `MAH := EXISTS c: (industrial activity AND qty(c) >=
Sch3 col3(c)) OR (isolated storage AND qty(c) >= Sch2 col3(c))` with Part
II class TOTALs and Sch2/Sch3 note-(a)(b) 500m aggregation; `required_inputs`
/ `facts` literally **R-019** (a rule reference). Notes: MAH is DERIVED by
the msihc_mapping_steps pipeline, never user-asserted; FALSE only if every
chemical identity-/class-resolved and quantity-known with none reaching
col 3. APR-012: COMPLIANCE_APPROVAL / REPORT, PRE_OPERATION;OPERATION,
rules R-019;R-020;R-021, precondition MAH derivation (R-091), renewal
CMP-010, change CMP-020, 4-way Sch-5 authority (AUT-005/AUT-003/AUT-008/
Collector). Live code: SAFE-listed, now DEFERRED, never INCLUDED;
`_encode` rejects explicitly.

## 4. Semantic Reconstruction

Question answered: "is this site a MAJOR-ACCIDENT-HAZARD installation?"
Boolean-shaped (TRUE/FALSE/UNKNOWN with evidence chain) but **not**
encodable: it is a derived-classification consequence (REPORT obligation),
not a directly evaluable applicability predicate. Sibling duties stay
separate: DOC-009 site/safety report (occupier), CMP-010 audit/update,
CMP-020 change report, CMP-011 emergency plan. APR-012 is completely
unmodeled in the pack (no authority/docs/SLA/hints/edges/rules) — nothing
treats the MAH report as a decided approval.

## 5. Source Audit

SRC-016 T1 OFFICIAL_PRIMARY (MSIHC as amended to 2000): proves r.2/r.4–r.14
and Sch 2/3 notes; explicitly does NOT prove post-2000 amendments, Sch 1
Part I criteria, or any sum-of-ratios rule — three evidentiary ceilings.
Not in the 22-source loaded corpus (consistent with deferral). Currency:
UNK-035 OPEN (no post-2000 amendment found). Per-entry hazards stay
blocked, not averaged (S1-TOX signs, S2-18 '501', S3P1-111 50-vs-5t with
CON-023); partials open (UR-01/02/03); CON-021 resolved values recorded.

## 6. Fact Audit

F-HAZ-01 inventory LIST {chemical, cas, max_qty_t, storage_type} and
F-HAZ-02 mapping LIST {chemical, schedule, col3_t, col4_t} ("sourced from
Sch 2/3") exist, VERIFIED — but both `unknown_allowed=False`, so the
register's "UNKNOWN qty/mapping → UNKNOWN" is expressible only as
missing/None (documented supply discipline). F-PRC-03 (is_MAH) is DERIVED,
never supplied. The existing partial pipeline (`derive_mah_status`: exact-
string col-3 join, TRUE dominates, all-resolved FALSE, else None — never
FALSE for unmapped, ET-081 spirit) covers none of: Sch2-vs-Sch3 storage
branching, Part II class TOTALs, 500m aggregation, Sch-5 routing. No MAH-
scalar supplied fact exists; none added. GJ namespace rejects all three
(JURISDICTION_MISMATCH, tested). 128 facts unchanged.

## 7. Engine Representability

Requires EXISTS quantification, schedule-table lookup, per-class TOTAL
aggregation, 500m geospatial aggregation, composition with deferred R-019,
and 4-way dynamic routing. Engine offers eq/in/gte/lte/gt/lt + AND/OR/NOT
+ literals (op set asserted exact) — none of the six. YEAR_ONLY window
noted. No primitive introduced; blockers documented.

## 8. Falsification Findings

Attempted defeaters: wrong approval (APR-012 correct, REPORT class
confirmed), single authority (actually four — any default misroutes 3/4),
wrong lifecycle (PRE_OPERATION;OPERATION confirmed), wrong jurisdiction
(central/state confirmed), supersession (UNK-035 open, not assumed),
threshold ambiguity (per-entry blocks kept, CON-021 resolved recorded),
unmapped→FALSE shortcut (ET-081 forbids; derivation returns None),
hazardous-alone triggers (ET-022 49-vs-50t requires quantity), sum-of-
ratios invention (source lacks it). No finding supports activation; every
finding supports deferral.

## 9. Dependency Analysis

DEP-010/011 (TIME_LEAD r.7/r.10) and DEP-026 (LEGAL_PRECONDITION r.7(1)
HIGH, non-inferred) target "Commencement of industrial activity" — an
activity endpoint, correctly triaged out with explicit reasons; zero
APR-012 edges in the pack. F-HAZ-01/02 feed no active predicate (only the
R-091 derivation). R-019/R-020/R-091 donors all deferred (untouched).

## 10. Status Decision

**DEFERRED — class D** (missing composition/aggregation/lookup/derived-
pipeline; donor R-019 deferred; routing unmodelable). Not ACTIVE (six
unrepresentable requirements), not CONFIRMATION-GATED (nothing external
would unlock it — the gaps are structural, not informational), not DNI
(the REPORT obligation is real and VERIFIED_CONDITIONAL), not UNKNOWN
(identity fully established).

## 11. Evidence Gaps

MoEFCC consolidated MSIHC text (UNK-035/UR-03); S.O.2882 gazette for col-4
values (UR-01); ethyleneimine clarification (UR-02/CON-023); Sch-5
authority mapping data; per-site 500m installation graph; Part II class
aggregation rule confirmation. Engine needs (in order): versioned MSIHC
dataset, EXISTS/aggregation evaluation, composition with provenance —
none built here.

## 12. Implementation Decision

One deferral entry (explicit reason: composition + partial pipeline +
ET-081 + SRC-016). Zero rules activated, zero facts/primitives/sources
added, zero donor modifications. The inventory arithmetic now closes:
105 = 26 + 60 + 26 + 3 + 3 + 5 remaining untriaged.

## 13. Tests

`backend/tests/test_mh_r021.py` — **49 tests**, all passing: baseline,
CSV-read identity (register/rules/approvals/facts/documents/compliance/
sources/unknowns/unresolved/conflicts/edge), semantics (REPORT split,
pack-unmodeled proof), sources (T1 + three ceilings + UNK-035), facts
(strict LISTs, derivation TRUE/FALSE/None matrix, no supplied MAH scalar,
GJ mismatch), engine (op set, donor deferred, no rule-reference, YEAR_ONLY),
falsification (8 attempted defeaters), dependencies (triaged reasons +
pack absence + no active MSIHc-fact use), isolation, decision (class D,
zero activation, untriaged→5, consent chain untouched). Full suite 2077
passed; ruff clean; tsc clean.

## 14. Files Changed

- `backend/app/seed/mh/approvals.py` — R-021 deferral entry (only
  pack-logic change).
- `backend/tests/test_mh_r021.py` — new (49 tests).
- `backend/tests/test_mh_{consent_category_chain,workflow_lifecycle,
  midc_lifecycle_tail}.py` — deferred pins 59→60 (required cascade).
- `backend/tests/test_mh_hazardous_waste_authorization_chain.py` — pins
  59→60 (required cascade).
- `backend/tests/test_mh_remaining_inventory.py` — UNTRIAGED set minus
  R-021 + baseline docstring (parallel file, minimal required edits;
  its arithmetic already anticipated this outcome).
- `audit_mh_r021.md` — new (this file).

## 15. Final Determination

**R-021 is safely triaged as DEFERRED (class D).** The determining
condition is conjunctive: (1) required input is rule R-019 (deferred for
EXISTS/aggregation/routing), AND (2) the MAH derivation needs schedule
lookup + class TOTALs + 500m aggregation no primitive expresses, AND (3)
Sch-5 routing is 4-way dynamic. Any one alone forces deferral; all three
hold. Unmapped chemicals stay UNKNOWN (ET-081); hazardous-alone triggers
nothing (ET-022); no sum-of-ratios (source-lacking). The remaining P2
sequence (R-054/059/071/072/076, then controlled-substance R-065/066/050 —
already underway in parallel) proceeds unchanged.
