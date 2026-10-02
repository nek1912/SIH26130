# Maharashtra R-054 Final SAFE Approval Audit — EC Expansion Exemption (APR-052)

Falsification audit with SAFE treated as unproven hypothesis. A parallel
session had drafted `test_mh_r054.py` proving partial encoding fails OPEN
but left explicit triage as follow-up pending the R-021 pin; this audit
independently verified every register claim, adopted that suite, and
completes the triage. Jurisdiction IN-MH (primary), IN-GJ regression-only.
Date (UTC): 2026-09-29. Source: v5 registers
(`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`).

## 1. Scope

Close the last SAFE-but-untriaged rule determinable in this session
(R-021 closure complete). Determine whether R-054 survives falsification;
if not, assign ACTIVE / DEFERRED / CONFIRMATION-GATED / DNI / UNKNOWN on
evidence. No coverage optimization; R-021 and all prior/parallel outcomes
preserved.

## 2. Current Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"`. Unchanged.
- Before: MH active 26, deferred 60, confirmation 26, DNI 3, UNKNOWN 3,
  GJ 19, facts 128, untriaged 5 (R-054/059/071/072/076).
- After: MH active 26, deferred **61** (+R-054), others identical,
  untriaged **4** (R-059/071/072/076), suite **2140 passed** (2077 baseline
  + 34 R-054 + 29 parallel residual-hygiene).
- Ruff clean. Frontend `tsc --noEmit` clean.
- Parallel inventory/EC-core/controlled-substance/hygiene files already
  anticipated this outcome (61-pins, UNTRIAGED-minus-R-054); required
  fallout only: count pins 60→61 and the adopted draft's triage test.

## 3. Identity Verification

`rule_register_v5.csv` + `rules.csv` (test-pinned): R-054, "EC for
expansion / no-increase-in-pollution-load exemption", APR-052, obligation
APPROVAL, authority AUT-001/AUT-002, jurisdiction CENTRAL, stage OPERATION,
rule_kind DETERMINISTIC, status VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE,
T1 SRC-001 para 7(ii)(b), effective "-" (UNKNOWN temporal), no deps/docs/
timeline. Predicate: `EC_EXPANSION_EXEMPT := F-EXP-01 AND item IN {2,3,4,5}
AND F-EXP-02 == FALSE AND empanelled-auditor certificate (Appendix XIII,
PARIVESH+SPCB) AND OCMS >=95% AND NOT (B2->A or B2->B1); else Form I under
7(ii)(a)`. Notes: "Applies to Sch items 2-5 per consolidated text".
APR-052: APPROVAL, OPERATION, ACTIVITY_DEPENDENT, AUT-001/AUT-002, EIA
7(ii)(b), CENTRAL, trigger expansion/product-mix of EC-holder, lifecycle
**EXPANSION** (unique), preconditions UNKNOWN, implement_status
**REQUIRES_OFFICIAL_CONFIRMATION** (rule claims SAFE — second blocker).

## 4. Semantic Reconstruction

Legal question: "is this EC-holding expansion exempt from fresh EC under
7(ii)(b), else Form I under 7(ii)(a)?" An exemption-with-routing rule, not
a plain approval predicate: TRUE means "exempt", FALSE-branch means
"NOT EXEMPT → Form I" (ET-068), UNKNOWN on OCMS-unknown (ET-069), full
house EXEMPT only with cert + B2→B2 (ET-067). Obligated party: expanding
EC-holder; stage OPERATION/EXPANSION; authority EAC-or-SEIAA by category.

## 5. Source Audit

SRC-001 T1 OFFICIAL_PRIMARY (EIA consolidated 13-07-2026): proves para
7(ii)(a)-(c) verbatim — provision-level support is genuine. Not-proves
(validity/monitoring, 5(f)+8(a) overlap, notified estates) are out of this
rule's scope. Source strength is the one non-blocking link; it does not
cure the missing conjunct facts.

## 6. Fact Ontology Audit

F-EXP-01 BOOL strict (is_expansion_or_modernisation; no UNKNOWN token);
F-EXP-02 BOOL_OR_UNKNOWN (pollution_load_increase). Absent with no
substitute: item-scope (no F-ITEM-01; no sched+item label), auditor/
Appendix-XIII/PARIVESH certificate, OCMS/uptime telemetry, category-change
state, prior-EC-holder status (F-LOC-03 is estate coverage for R-005, not
project holder; no F-EC-01). No facts added. 128 unchanged. GJ mismatch
tested via suite isolation.

## 7. Predicate Falsification

Executed probe (throwaway, never pack): {expansion, no-load-increase} →
APPLIES while item scope, certificate, OCMS, category change, and holder
status are unchecked — **fails OPEN, proven**. Violated conjuncts invisible
(B2→A + no-cert + OCMS-40% still APPLIES). F-EXP-01 FALSE reads as
"expansion EC does not apply" when there is simply no expansion (vacuous
negative; else-branch is routing, not negation). Missing/UNKNOWN inputs
fail closed only for the two modeled conjuncts. R-065-partial-pattern
analogue confirmed: subset encoding over-claims.

## 8. UNKNOWN / Three-Valued Analysis

ET-069 (OCMS UNKNOWN → UNKNOWN) expressible only if OCMS were modeled —
it is not, so the probe cannot even reach the register's UNKNOWN state.
F-EXP-02 None/"UNKNOWN"/missing → INSUFFICIENT (tested). F-EXP-01 has no
UNKNOWN representation (strict BOOL). No legal default exists for the four
unmodeled conjuncts; nothing may default them to satisfied.

## 9. Threshold / Boundary Analysis

OCMS >=95% uptime (inclusive per ET-067 at exactly 95%) and B2→B1/A
exclusion are untestable without telemetry/category-change facts — no
BELOW/EXACT/ABOVE matrix executable. No numeric inference performed (< vs
<= taken from register text only).

## 10. Multi-Value / Aggregation Analysis

Per-expansion (single project change), no per-activity/substance/location
split in the predicate; no ANY/ALL/SUM/MAX/EXISTS semantics required or
assumed. No aggregation blocker — the blockers are missing conjunct facts
and else-branch routing.

## 11. Authority / Routing

AUT-001 (MoEFCC/EAC Cat A) and AUT-002 (SEIAA MH Cat B) both VERIFIED,
static, no quantity/location/lifecycle variance. The rule lists the pair
unresolved: an APPLIES verdict could not name its deciding authority.
Routing ≠ applicability; kept separate by deferral, not by encoding.

## 12. Lifecycle / Dependency Analysis

EXPANSION lifecycle (PRE-operation? register stage OPERATION): distinct
from establishment (R-041/APR-038) and prior-EC (R-002/APR-001, item 5(f)
new small units — different approval, item scope, and question; no
duplicate). Zero APR-052 rows in dependencies/compliance/SLA/conditional/
confirmation/unknowns/unresolved registers; zero loaded edges/docs. An
unresolved upstream cannot satisfy R-054 because no upstream exists in the
pack — containment verified (no live APR-052 rule: evaluate→[]).

## 13. Document / Portal Boundary

No DOC/SLA/portal rows for APR-052 anywhere: PORTAL-SERVICE-EXISTS ⇒
approval and DOCUMENT-REQUIRED ⇒ applies fallacies have no foothold.
Certificate/OCMS evidence (Appendix XIII, PARIVESH+SPCB, CPCB/SPCB
telemetry) is correctly treated as missing evidence, not as portal
workflow.

## 14. Engine Representability

AND + three-valued logic + effective dates suffice structurally; the
missing piece is five fact inputs plus else-branch (Form I) routing.
No lookup/aggregation/EXISTS/composition/GIS/date-arithmetic/workflow-state
needed for the deferral — plain missing facts. No primitive introduced.

## 15. Readiness / Downstream Analysis

APR-052 touches no loaded edge/document/SLA: APPLIES (unreachable),
DOES_NOT_APPLY, CONDITIONAL, and INSUFFICIENT_DATA all propagate to
nothing. UNKNOWN upstream cannot satisfy a nonexistent downstream.
GJ isolation verified (no R-054/APR-052 in GJ pack).

## 16. Attack Matrix

15 scenarios executed or register-pinned: canonical EXEMPT house (ET-067),
B2→A NOT-EXEMPT→Form I (ET-068), OCMS-UNKNOWN→UNKNOWN (ET-069),
probe-APPLIES-on-2-conjuncts (UNSAFE, proven), violated-conjuncts-invisible
(UNSAFE, proven), vacuous negative (UNSAFE reading, proven), missing/
UNKNOWN modeled inputs (safe INSUFFICIENT), no-expansion, wrong approval
(R-002 separation), wrong jurisdiction (CENTRAL noted; GJ absent),
empty-collection n/a (no list inputs), T1-source strength (non-blocking).
Fail-open defect: partial encoding reports EXEMPT without item/cert/OCMS/
category/holder checks. Fail-closed verified: full-predicate evaluation is
impossible, so no verdict is reachable; default absence + explicit deferral
both refuse.

## 17. Classification

**D** — new fact/ontology required (five missing conjunct inputs), earliest
blocking condition. Not A/B (unrepresentable), not C (source T1 suffices;
nothing external unlocks), not F (predicate faithfully transcribed), not G
(obligation real, VERIFIED_CONDITIONAL), not UNKNOWN (identity complete).

## 18. Implementation Decision

One deferral entry (substantive: 6-conjunct scope, unmodeled five,
fail-OPEN proof, inversion warning, Form-I erasure, UNKNOWN temporal).
Zero activations, facts, primitives, donor changes. Midc-tail HW-chain pins
updated 60→61 as required cascade; parallel inventory/EC-core already
converged.

## 19. Evidence Gaps

Item-scope fact (EIA Sch items 2-5 per project); Appendix-XIII certificate
registry/PARIVESH+SPCB evidence path; OCMS ≥95% telemetry feed + category-
change state; prior-EC-holder project fact; effective-date research ("-"
temporal UNKNOWN); AUT-001-vs-002 resolution data; APR-052 precondition/
validity research (all UNKNOWN in register).

## 20. Recommended Next Audit

Remaining untriaged R-059/071/072/076 (four; controlled-substance R-065/
066/050 already in parallel flight — coordinate, do not duplicate). Then
the R-002 small-unit exception as the first ACTIVE EIA rule under the same
falsification lens used here for R-018.

## 21. Test Results

- Adopted + extended `test_mh_r054.py`: **34 tests** (CSV identity incl.
  approval ROC/EXPANSION + edge-house ET-067/68/69, fact-linkage absences,
  probe falsification, inversion, containment, closure class: deferral
  substance, R-002 separation, authority verification, F-EXP strictness,
  temporal UNKNOWN, untriaged arithmetic, R-021 preserved).
- Full backend: **2140 passed** (2077 + 34 + 29 parallel hygiene), 0 failed.
- Ruff clean. Frontend `tsc --noEmit` clean.

## 22. Files Changed

- `backend/app/seed/mh/approvals.py` — R-054 deferral entry (only
  pack-logic change).
- `backend/tests/test_mh_r054.py` — adopted parallel draft: header +
  baseline + triage test updated, `_encode` import, closure class added.
- Count cascades 60→61: consent/workflow/tail/HW-chain(×2)/r021 pins +
  parallel inventory arithmetic (already converged) + EC-core (already
  converged).
- `audit_mh_r054.md` — new (this file).

## 23. Final Determination

R-054 is **not safe** under current evidence and engine semantics: a
facts-only encoding reports EXEMPT while blind to item scope, auditor
certificate, OCMS telemetry, category change, and holder status, and an
approval-level APPLIES would invert exemption into approval while erasing
Form-I routing. Earliest blocking point: **four unmodeled conjuncts of a
six-conjunct AND with no representation path** (plus presupposed holder
status). Minimum closure: five evidenced facts + else-branch routing
preservation + effective-date research. Disposition **DEFERRED (D)**;
untriaged 6→4 (R-059/071/072/076 remain).
