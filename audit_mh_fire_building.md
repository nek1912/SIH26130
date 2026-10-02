# Maharashtra Regulatory Engine Audit — Fire Protection, Building Permissions & Local Authority Approvals

Cluster: R-037 (APR-032), R-041 (APR-038/APR-041), R-078 (APR-039/APR-040),
R-079 (APR-039/APR-040), R-080 (APR-038), R-082 (APR-038).
Jurisdiction: IN-MH (primary SIH jurisdiction). IN-GJ is regression-only.
Date (UTC): 2026-09-29. Authoritative source: v5 regulatory registers
(`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`).

## A. Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"` (`backend/app/seed/pack.py`). Unchanged.
- MH active rules: 26 (`load_mh_approval_rules()`; `MH_INCLUDED_RULE_IDS`).
  Batch-1 (19) + batch-2 (R-073/R-086/R-087) + location cluster
  (R-077/R-083/R-084/R-096). No cluster rule is active.
- MH deferred: 56 entries in working tree (`MH_DEFERRED_RULES`). This audit
  adds ZERO new deferred entries: R-041/R-078/R-079/R-080/R-082 were already
  deferred; R-037 was already in `MH_REQUIRES_CONFIRMATION_RULE_IDS`.
- GJ active rules: 19. Unchanged. No cluster ID leaks into GJ pack.
- MH facts: 128 (`MH_FACTS`). No new facts added. `construction` absent.
- Backend: 1692 passed (1553 working-tree baseline + 139 new in
  `test_mh_fire_building.py`), 0 failed. Ruff clean (`app/`, `tests/`).
  Frontend `tsc --noEmit` clean.
- Git state at audit start: uncommitted CTO/establishment work (ARCH/PRD/
  approvals + 3 untracked test files) plus untracked draft
  `test_mh_fire_building.py` (5 failing tests, fixed in this task).
  This task modifies only `test_mh_fire_building.py`, this artifact, and
  minimal doc entries. `approvals.py` pack logic untouched.

## B. Candidate Identity Matrix

Verified against `rule_register_v5.csv`, `rules.csv`, `approvals.csv`,
`authorities.csv`, `facts.csv`, `sources.csv`, `dependencies.csv`,
`requires_confirmation.csv`, `unknowns.csv`, `unresolved_items.csv`,
`sla.csv`, `edge_tests.csv`, `planning_fire_tree.csv`, `planning_steps.csv`.

| Rule | Title (register) | Approval (register) | Approval name | Record/lifecycle | Authority | Jurisdiction | Status / implementation |
|------|------------------|---------------------|---------------|------------------|-----------|--------------|-------------------------|
| R-035 (guard, reference) | MIDC plot allotment | APR-029 | MIDC plot / branch guard | APPROVAL / PRE_ESTABLISHMENT | AUT-010 (MIDC) | MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, ACTIVE |
| R-037 | MIDC occupancy certificate | APR-032 | MIDC occupancy certificate | APPROVAL / PRE_OPERATION | AUT-010 (MIDC) | MIDC | REQUIRES_OFFICIAL_CONFIRMATION / REQUIRES_CONFIRMATION, NOT active |
| R-041 | Building/development permission (non-MIDC planning authority) | APR-038;APR-041 | APR-038 building/development permission (PRE_CONSTRUCTION) + APR-041 occupancy non-MIDC (PRE_OPERATION) | APPROVAL / PRE_ESTABLISHMENT (rule) splitting PRE_CONSTRUCTION vs PRE_OPERATION | AUT-011 (planning authority, site-dependent) | NON_MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, DEFERRED |
| R-078 | Provisional fire NOC (non-MIDC) | APR-039;APR-040 | APR-039 provisional (PRE_CONSTRUCTION) + APR-040 final (PRE_OPERATION) | NOC / PRE_ESTABLISHMENT | AUT-012 (fire authority, site-dependent) | NON_MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, DEFERRED |
| R-079 | Provisional fire NOC (non-MIDC) | APR-039;APR-040 | same as R-078 | NOC / PRE_ESTABLISHMENT | AUT-012 | NON_MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, DEFERRED |
| R-080 | Building/development permission (non-MIDC planning authority) | APR-038 | Building/development permission | APPROVAL / PRE_ESTABLISHMENT | AUT-011 | NON_MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, DEFERRED |
| R-082 | Building/development permission (non-MIDC planning authority) | APR-038 | Building/development permission | APPROVAL / PRE_ESTABLISHMENT | AUT-011 | NON_MIDC | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, DEFERRED |

Prompt-label verification: R-037 MIDC OC (APR-032) correct; R-041 non-MIDC
building permission dual APR-038/APR-041 correct; R-078 fire authority routing
(APR-039/APR-040) correct — it is routing, not applicability; R-079 fire Final
NOC applicability via Schedule-I (APR-039/APR-040) correct — it is a class
predicate needing a non-MIDC guard; R-080 building authority routing (APR-038)
correct; R-082 planning/DCR regime selection (APR-038) correct. No label
correction needed beyond emphasizing routing vs applicability vs regime.

Key register excerpts:

- R-037: `MIDC_OC := MIDC_BRANCH == TRUE`, inputs `F-LOC-01`, deps
  `APR-009;APR-016;APR-033`, docs `DOC-002;DOC-006;DOC-007`, timeline
  `SLA-016` (PORTAL), stage PRE_OPERATION, effective UNKNOWN, source
  `SRC-044` T3, confidence HIGH, note portal-only, MIDC DCR text not in
  source register. `rules.csv` legal basis `MIDC DCR`, regime `REG-MIDC`.
- R-041: `NONMIDC_BP := F-LOC-01 == FALSE AND construction == TRUE ;
  authority := R-080(F-LOC-05) ; DCR := R-082(F-LOC-05) ;
  UNKNOWN if F-LOC-05 UNKNOWN`, inputs `F-LOC-01;F-LOC-05`, deps
  `APR-009;APR-016;APR-040`, timeline `SLA-042;SLA-043` (LEGAL), stage
  PRE_ESTABLISHMENT, effective 2025-07-24 EXACT, sources
  `SRC-123;SRC-124;SRC-067` (T1;T2), confidence MEDIUM, legal basis MRTP
  s.18/s.44/s.45/s.46 + UDCPR Reg.2.1.1, regime `REG-BLD`.
- R-078: `FIRE_AUTHORITY := IF F-LOC-01 THEN 'MIDC Fire Services (R-036)'
  ELSE IF F-PA-02 == TRUE THEN 'Chief Fire Officer of ' + F-LOC-05
  ELSE IF F-PA-02 == FALSE OR outside limits THEN 'Director, MFS'
  ELSE UNKNOWN`, inputs `F-LOC-01;F-LOC-05;F-PA-02`, operator CASE, deps
  `Provisional Fire Safety Approval` (non-approval endpoint), timeline
  `SLA-025` (PORTAL), effective 2006 YEAR_ONLY, source `SRC-121` T1
  (MFPLSM s.3(1)), note never default authority, regime `REG-FIRE`.
- R-079: `FIRE_APPROVAL_APPLICABLE := F-BLD-10 IN {G-1,G-2,G-3,H,J} ;
  F-BLD-10 UNKNOWN -> UNKNOWN ; minimum installations := Schedule-I row by
  class and aggregate floor area`, inputs `F-BLD-10;F-BLD-11`, operator IN,
  deps `Provisional Fire Safety Approval`, timeline `SLA-025`, effective 2006
  YEAR_ONLY, source `SRC-121` Schedule-I, confidence MEDIUM, note hazard class
  is input fact, regime `REG-FIRE`.
- R-080: `BP_AUTHORITY := CASE F-LOC-05: MIDC→MIDC(SPA); MC/Council/Panchayat→
  that body; other SPA/NTDA→that SPA; RP outside PA→Collector(s.18);
  gaothan→panchayat(s.18); UNKNOWN→UNKNOWN`, inputs `F-LOC-05`, operator
  CASE, timeline `SLA-042;SLA-043`, effective 1966 YEAR_ONLY, source `SRC-123`
  s.18(1);s.44(1) T1, note answer depends on particular authority.
- R-082: `UDCPR_APPLIES := F-LOC-05 NOT IN {MCGM+PAs/SPAs/DAs in MCGM,
  MIDC, NAINA, JNPT, Hill Station MCs, Chikhaldara, ESZ, Lonavala MC} ;
  else own DCR (UNKNOWN which)`, inputs `F-LOC-05`, operator NOT IN,
  timeline `SLA-042;SLA-043`, effective 2020-12-03 EXACT, source `SRC-124`
  Reg.1.1 T2 (compilation 30-01-2024; later amendments not checked).

Approvals: APR-032 MIDC OC (AUT-010, PRE_OPERATION, LOCATION_DEPENDENT,
`implement_status: SAFE` but rule R-037 REQUIRES_CONFIRMATION, note SLA
conflict CON-001); APR-038 non-MIDC building permission (AUT-011,
PRE_CONSTRUCTION, `REQUIRES_OFFICIAL_CONFIRMATION`, authority site-specific,
trigger s.44, precondition title/DP-RP conformity); APR-039 provisional fire
NOC non-MIDC (AUT-012, PRE_CONSTRUCTION, `REQUIRES_OFFICIAL_CONFIRMATION`,
rule_ids `R-042` — not R-078/R-079 — trigger before construction of
Schedule-I building); APR-040 final fire NOC non-MIDC (AUT-012,
PRE_OPERATION, `REQUIRES_OFFICIAL_CONFIRMATION`, rules `R-042;R-099`,
precondition installations + Form A, validity final, renewal CON-013);
APR-041 non-MIDC OC (AUT-011, PRE_OPERATION, `REQUIRES_OFFICIAL_CONFIRMATION`,
no official source for sequencing).

Authorities: AUT-010 MIDC (VERIFIED, MIDC estates only, plot/BP/OC/MIDC fire/
water/drainage); AUT-011 planning authority (REQUIRES_CONFIRMATION,
LOCATION_DEPENDENT, identity never defaulted, MPCB rejects local-body NOC as
BP per SRC-067); AUT-012 fire authority (REQUIRES_CONFIRMATION,
LOCATION_DEPENDENT, which-directorate-vs-brigade UNKNOWN).

Sources: SRC-044 MIDC planning page T3 (proves only tied claims, not beyond
locators); SRC-121 MFPLSM Act 2006 T1 STATE_ACT (proves CFO-or-Director +
Schedule-I classes/installations; does NOT prove which CFO covers a site or
the hazard class of a given building); SRC-123 MRTP Act 1966 T1 (proves
s.44/s.45 deemed-60d-if-conformant/appeal; does NOT prove authority identity);
SRC-124 UDCPR T2 (proves extent exclusions + permission mandatory; does NOT
prove post-30-01-2024 amendments or industrial-zone/fire provisions); SRC-067
MPCB circular 24-07-2025 T2 (proves BP verification before CTE; local-body
NOC invalid as BP); SRC-048 e-Fire T3 (provisional timeline only).

Dependencies: DEP-005 (APR-033→APR-032 fire NOC for OC), DEP-006
(APR-009→APR-032 CTO for OC), DEP-007 (APR-016→APR-032 factory registration
if applicable) — all OFFICIAL_WORKFLOW, these are readiness edges, not R-037
applicability conditions. DEP-008 (APR-038→APR-008 BP verified before CTE,
SRC-067, VERIFIED_CONDITIONAL) — non-MIDC BP as CTE precondition.
DEP-023/024/025 (APR-009/APR-040/APR-016→APR-041 non-MIDC OC) are UNKNOWN /
inferred / LOW — correctly excluded from pack. DEP-031 (Provisional→APR-040
final, SEQUENCE, SRC-121) has a non-approval prerequisite and is excluded.

Requires-confirmation: R-037 (portal-only, MIDC DCR text missing); APR-041
(no official sequencing source); R-042 (APR-039/APR-040 guard, T3, needs
R-078/R-079/R-099); FR-03 (chemical-sector renewal exception, no rule text).

Conflicts: CON-001 (APR-032 SLA 10 vs 8/8/15 days; RTS legal limit in
midc_sla, display all); CON-013 (fire renewal 2014 vs 2025 circulars —
RESOLVED not-a-conflict: no renewal under Fire Act, CONDITIONAL on other
statutes via R-099); CON-024 (annual fire renewal for petroleum/gas holders —
T2 statement vs T1 text showing no such rule; keep UNKNOWN, do not
implement).

Unknowns: UNK-018 (which fire authority covers a site — CLOSED_V3 via
jurisdiction-aware R-078 returning UNKNOWN); UNK-020 (fire NOC building
thresholds — CLOSED_V3 via R-079). Unresolved: UR-19 (MIDC BP/OC legal basis
R-036/R-037 — OPEN, needs MIDC DCPR gazette; engine REQUIRES_CONFIRMATION).

SLA: SLA-016 APR-032 10 DAYS PORTAL (REQUIRES_CONFIRMATION, CON-001);
SLA-025 APR-039 7 WORKING_DAYS PORTAL (VERIFIED); SLA-042 APR-038 60 DAYS
LEGAL deemed-if-conformant (R-081); SLA-043 APR-038 40 DAYS appeal window.
No SLA is encoded as an applicability rule.

Compliance/conditional: no APR-032/038/039/040/041 compliance rows imposing
applicability; fire renewal is R-099/CON-013, not this cluster.

Edge tests: ET-044/045/046 (R-035 MIDC/non-MIDC/UNKNOWN branches);
ET-117 (R-078 F-PA-02 UNKNOWN→UNKNOWN, never Director default);
ET-118 (R-080 RP_AREA_COLLECTOR→Collector s.18(1)); ET-119 (R-082
F-LOC-05=MIDC→UDCPR FALSE→MIDC DCR); ET-v4-15 (PS-01 authority UNKNOWN→
UNKNOWN, no default). No ET asserts R-037 APPLIES (correct — T3 only).

Planning/fire tree: PF-01 (F-LOC-01 MIDC?→MIDC branch else PF-02, UNKNOWN
stops); PF-02 (F-LOC-05→PF-03, UNKNOWN stops, output BP_AUTHORITY R-080);
PF-03 (UDCPR exclusion?→own DCR else UDCPR R-082, output DCR identity);
PF-04 (APR-038 s.44/s.45/deemed-60d/appeal-40d); PF-05 (APR-041 per DCR,
REQUIRES_CONFIRMATION); PF-06 (F-BLD-10 Schedule-I?→APR-039/040 R-079,
UNKNOWN→UNKNOWN); PF-07 (F-PA-02 CFO?→CFO else Director, UNKNOWN→UNKNOWN,
output R-078). Planning steps PS-01..PS-08 confirm authority UNKNOWN→UNKNOWN
and fire provisional-before-CC / final-before-occupation sequencing.

## C. R-037 Audit

APR-032 is PRE_OPERATION (occupancy), not pre-establishment. Condition is
pure location (`MIDC_OC := MIDC_BRANCH == TRUE`, sole input F-LOC-01).
It answers "MIDC branch?" — not "construction complete?", "plan approved?",
"fire cleared?", or "utilities ready?". Those are DEP-005/006/007 readiness
edges (APR-033 fire, APR-009 CTO, APR-016 factory-if-applicable), correctly
separate from applicability per invariant 11.

Mandatory? The register says REQUIRES_OFFICIAL_CONFIRMATION: portal
(SRC-044 T3) proves the service exists; the cited `MIDC DCR` regulation text
is not in the source register (UR-19 OPEN). No statutory provision, no
effective date, SLA in conflict (CON-001). Encoding `F-LOC-01==True →
APPLIES` would present a portal listing as a statutory determination.
Deferred (confirmation-gated) fail-closed. Correct.

Lifecycle: PRE_OPERATION. Tied to completion workflow, but the rule itself
contains no completion/construction/plan/fire/utility conjunct. Do not
conflate "does OC apply (MIDC?)" with "how does OC workflow proceed
(deps/docs/SLA)?".

MIDC-only: jurisdiction MIDC, authority AUT-010. Distinct from APR-041
non-MIDC OC (AUT-011, no sequencing source). F-LOC-01 is the branch fact
(BOOL_OR_UNKNOWN, UNKNOWN never coerced).

Authority static (AUT-010) but activation gated by confirmation. No dynamic
routing needed.

Facts: F-LOC-01 exists (boolean, unknown-allowed). No construction/lifecycle
fact is in the condition, and none should be invented to "strengthen" it.

## D. R-041 Audit

Dual target APR-038 (PRE_CONSTRUCTION building permission) vs APR-041
(PRE_OPERATION non-MIDC OC) is confirmed in `rules.csv`/`rule_register_v5`
(`APR-038;APR-041`) while `approvals.csv` maps APR-038→R-041 and
APR-041→R-041 with APR-041 itself REQUIRES_CONFIRMATION and no sequencing
source. One ApprovalRule cannot span two lifecycle stages. Deferred.

Applicability vs workflow: the `NONMIDC_BP` conjunct (`F-LOC-01==FALSE AND
construction==TRUE`) is applicability, but `authority := R-080(...)` and
`DCR := R-082(...)` are routing/regime derivations requiring rule
composition. The engine has no rule-reference primitive. Deferred.

Construction: `construction == TRUE` has no fact in `facts.csv` (only
F-WAT-08 dewatering and F-LAB-05 workers match "construction" textually) and
no key in `MH_FACTS`. `F-LOC-01==False` alone therefore never implies
APPLIES. Operational chemical unit without new construction must not trigger
via this rule. UNKNOWN construction stays INSUFFICIENT_DATA, never FALSE.

Branch: MIDC/non-MIDC (F-LOC-01) is the primary split (R-035 active), but
non-MIDC alone is insufficient without construction + authority + regime.

Authority/regime: R-041 explicitly delegates to deferred R-080 and R-082.
Both donors deferred → composition impossible. Correct to defer.

APR-038 vs APR-041 must remain separate approval identities (different
stages, triggers s.44 vs completion, preconditions, validity). No single-rule
encoding.

UNKNOWN: F-LOC-01 UNKNOWN → branch unknown; F-LOC-05 UNKNOWN → explicitly
UNKNOWN per condition. Never DOES_NOT_APPLY.

## E. R-078 Audit

R-078 is authority routing, not applicability/jurisdiction-selector/workflow.
It computes a string (`FIRE_AUTHORITY`: MIDC Fire Services / CFO of named
body / Director MFS / UNKNOWN) via CASE over F-LOC-01/F-LOC-05/F-PA-02.
There is no boolean trigger. Mirrors deferred R-047 precedent. Deferred;
never an active ApprovalRule.

Hierarchy from evidence only: MIDC site → MIDC Fire Services (R-036);
non-MIDC + authority-has-CFO → that CFO; non-MIDC + no-CFO or outside limits
→ Director MFS; else UNKNOWN (ET-117). No municipal-corporation vs council
vs panchayat vs SPA vs Collector distinction is in R-078 — that is R-080's
domain. Director vs Directorate naming follows register (`Director,
Maharashtra Fire Services`); do not invent Collector or other fire
authorities.

Missing F-PA-02 (BOOL_OR_UNKNOWN) → UNKNOWN, never Director default.
Missing F-LOC-05 → UNKNOWN. No static authority may be encoded; dynamic
resolution does not exist in the engine. Deferral preserves
`authority routing != applicability`.

## F. R-079 Audit

Purpose: Schedule-I building-class predicate (`F-BLD-10 IN {G-1,G-2,G-3,H,J}`)
with UNKNOWN propagation and Schedule-I row/minimum-installation lookup by
class + F-BLD-11 largest-building area. Sources T1 (SRC-121 Schedule-I).
Lifecycle: spans provisional (APR-039 PRE_CONSTRUCTION, before building) and
final (APR-040 PRE_OPERATION, before occupation) — same predicate, two
stages. Mandatory vs conditional: VERIFIED_CONDITIONAL; the predicate alone
does not assert which stage fires without lifecycle context.

Relation to R-078: R-079 says *which buildings* need fire approval; R-078
says *who* issues it. Both target APR-039/APR-040. R-079 has no F-LOC-01
conjunct, so standalone encoding under non-MIDC APR-039 would match MIDC
sites (e.g. F-LOC-01=True + F-BLD-10=J → false APR-039 hit; MIDC fire is
APR-030/R-036). Requires non-MIDC guard composition + R-078 composition +
R-042 guard (R-042 itself REQUIRES_CONFIRMATION). Engine cannot compose.
Deferred fail-closed. Correct.

MIDC vs non-MIDC: register jurisdiction NON_MIDC, but condition lacks the
guard — the hazard the deferral prevents. Verified by test
(midc + J matches class but is-MIDC → APR-039 must not apply).

Schedule-I/building facts exist (F-BLD-10 ENUM_OR_UNKNOWN with G-1/G-2/G-3/
H/J; F-BLD-11 NUMBER_OR_UNKNOWN m2). Facts are sufficient; composition is
not. Applicability vs clearance-state: R-079 is a genuine predicate, but
unsafe standalone — it is a fragment of a two-rule decision (class +
branch/authority), not an independent approval rule in this engine.

## G. R-080 Audit

R-080 is authority routing (`BP_AUTHORITY` CASE over F-LOC-05), not
applicability. Inputs: F-LOC-05 only. Outputs: MIDC(SPA) / named
MC/Council/Panchayat / named SPA / Collector (RP outside PA, s.18) /
panchayat (gaothan, s.18) / UNKNOWN. No boolean. Mirrors R-047. Deferred.

MIDC behavior: F-LOC-05=MIDC → MIDC (SPA). Non-MIDC: named-body routing.
RP_AREA_COLLECTOR → Collector (ET-118, MRTP s.18(1)). Gaothan →
panchayat. UNKNOWN → UNKNOWN (ET-v4-15, never default).

No static authority is safe (AUT-011 itself is REQUIRES_CONFIRMATION,
site-dependent). Dynamic resolver does not exist. Encoding routing as
`F-LOC-05==X → APR-038 APPLIES` would be a category error. Deferral
preserves `applicability != authority routing`.

## H. R-082 Audit

R-082 selects planning regime (`UDCPR_APPLIES := F-LOC-05 NOT IN {MCGM…,
MIDC, NAINA, JNPT, hill-station MCs, Chikhaldara, ESZ, Lonavala MC};
else own DCR UNKNOWN which)`), not approval applicability. Source SRC-124 T2
(Reg.1.1, compilation 30-01-2024; later amendments unchecked). Deferred.

Critical inversion prevented: MCGM/NAINA/MIDC exclusion from UDCPR ≠
building-permission DOES_NOT_APPLY. MCGM has DCPR 2034, NAINA its own DCR,
MIDC its DCR — permission remains mandatory under the applicable regime.
ET-119 (MIDC→UDCPR FALSE→MIDC DCR) is regime selection, not negation.

Belongs in planning context / input derivation / routing, never in
ApprovalRule.applicability_conditions. No planning-regime selector exists in
the architecture; document the limitation instead of abusing ApprovalRule.
F-LOC-05 UNKNOWN → regime UNKNOWN, never default UDCPR.

## I. Cross-Rule / Architecture Analysis

Verified decision graph (from `planning_fire_tree.csv` + register
conditions):

```
F-LOC-01 (R-035 active guard)
 ├─ True  → MIDC branch: MIDC DCR, MIDC fire (APR-029..037, DEP-005/006/007)
 └─ False → F-LOC-05 (planning authority identity, fact)
             ├─ R-082 regime selection (DEFERRED: UDCPR vs own DCR)
             ├─ R-080 authority routing (DEFERRED: BP_AUTHORITY)
             ├─ R-041 applicability (DEFERRED: needs construction + R-080 + R-082)
             │    └─ DEP-008: APR-038 verified before APR-008 CTE
             ├─ F-PA-02 → R-078 fire authority routing (DEFERRED)
             └─ F-BLD-10/11 → R-079 class predicate (DEFERRED: needs non-MIDC guard + R-078)
                  └─ APR-039 provisional → APR-040 final (DEP-031 sequence)
R-037 MIDC OC (CONFIRMATION-GATED): F-LOC-01==True only; deps APR-009/016/033
are readiness edges, not conditions.
```

No guessed graph is implemented. Dependent rules (R-041 on R-080/R-082;
R-079 on non-MIDC guard + R-078 + R-042) stay deferred because the engine
has no rule-composition primitive (ConditionNode: leaf/AND/OR/NOT/Literal
only; no rule-reference operator). Applicability, routing, regime,
workflow, lifecycle, and compliance remain separate per invariant 11.

## J. Fact Ontology

- F-LOC-01 `site_in_midc_estate`: BOOL_OR_UNKNOWN, TRUE/FALSE/UNKNOWN,
  VERIFIED, used for MIDC branch + R-041 + R-078. Code: boolean,
  unknown-allowed. UNKNOWN never coerced.
- F-LOC-05 `planning_authority`: ENUM
  (MIDC/MUNICIPAL_CORP:<name>/MUNICIPAL_COUNCIL:<name>/
  NAGAR_PANCHAYAT:<name>/SPA:<name>/RP_AREA_COLLECTOR/GAOTHAN_PANCHAYAT/
  UNKNOWN), VERIFIED, required for R-041/R-078/R-080/R-082. Code: enum with
  MIDC + RP_AREA_COLLECTOR + GAOTHAN_PANCHAYAT present, unknown-allowed via
  UNKNOWN token.
- F-PA-02 `planning_or_local_authority_has_CFO`: BOOL_OR_UNKNOWN, VERIFIED,
  required for R-078. Code: boolean, unknown-allowed.
- F-BLD-10 `MFPLSM_Schedule_I_building_class`: ENUM_OR_UNKNOWN
  (G-1/G-2/G-3/H/J/other/UNKNOWN), VERIFIED, required for R-079. Code:
  enum with G-1/G-2/G-3/H/J present, unknown-allowed.
- F-BLD-11 `aggregate_floor_area_largest_building_m2`: NUMBER_OR_UNKNOWN
  (m2), VERIFIED, required for R-079. Code: number, unknown-allowed.
- `construction`: NO fact in `facts.csv` or `MH_FACTS` (only F-WAT-08
  dewatering and F-LAB-05 workers match textually). R-041's core conjunct
  is therefore unevaluable. Documented gap, not invented.
- Provenance: all five facts VERIFIED/ACTIVE in `facts.csv`; code specs in
  `facts.py` match types and UNKNOWN semantics. No applicant-vs-GIS ruling
  is in the registers beyond F-LOC-01's MIDC-GIS note; no new facts added.
- Jurisdiction: IN-MH only. IN-GJ lookups of MH keys raise
  JURISDICTION_MISMATCH. No GJ leakage either direction.

## K. Implementation Classification

- R-037: C. EVIDENCE INCOMPLETE (T3 portal-only, MIDC DCR text missing,
  UR-19 OPEN, SLA CON-001). Gated by `MH_REQUIRES_CONFIRMATION_RULE_IDS`.
- R-041: D. ENGINE LIMITATION (absent `construction` fact; needs R-080 +
  R-082 composition) + E. CONFLICTING/MISCLASSIFIED (dual APR-038/APR-041
  lifecycle split). In `MH_DEFERRED_RULES`.
- R-078: E. MISCLASSIFIED (authority routing string, mirrors R-047; CASE
  operator inexpressible as boolean predicate). Deferred.
- R-079: D. ENGINE LIMITATION (needs non-MIDC guard + R-078 + R-042
  composition; standalone over-applies to MIDC). Deferred. Facts exist;
  composition does not.
- R-080: E. MISCLASSIFIED (authority routing CASE, mirrors R-047).
  Deferred.
- R-082: E. MISCLASSIFIED (regime selector, NOT IN exclusion; encoding as
  applicability would falsely negate MCGM/NAINA/MIDC permission). Deferred.

For each: not applicability-safe standalone; routing/regime/lifecycle kept
separate; composition or dynamic resolution required but absent; GIS/local
data not digitized beyond fact enums; ConditionNode cannot express CASE /
rule-reference / NOT-IN-exclusion-as-applicability safely; UNKNOWN stays
INSUFFICIENT_DATA, never FALSE. No new engine abstraction justified
(anti-overengineering gate: no MVP requirement forces it).

## L. Rules Implemented

ZERO. No `approvals.py` change. Active pack remains the 26 verified rules.
`_encode()` continues to reject all six fail-closed (R-041/078/079/080/082
via deferred; R-037 via not-safe/confirmation).

## M. Rules Deferred

- R-041, R-078, R-079, R-080, R-082: in `MH_DEFERRED_RULES` with substantive
  rationales (construction absence; FIRE_AUTHORITY/BP_AUTHORITY routing;
  Schedule-I + non-MIDC guard + R-042 composition; regime selector with
  falsely-negate warning). All reject via `_encode()` with explicit
  messages. Verified by parametrized tests.
- R-037: NOT in deferred dict by design; blocked via
  `MH_REQUIRES_CONFIRMATION_RULE_IDS` (T3-only). `_encode()` rejects
  (not-safe path precedes confirmation path — both fail-closed).
- Deferred/confirmation sets and active set remain disjoint.

## N. Tests and Validation

`backend/tests/test_mh_fire_building.py` (139 tests, all passing):

- Baseline (6): MH 26, GJ 19, DEFAULT IN-GJ, disjoint, cluster absent from
  active + included IDs.
- Identity matrix (17): per-rule approval/authority/status/jurisdiction,
  dual-target, routing-vs-applicability, regime-vs-applicability, fact
  presence, Schedule-I classes, T1/T2 source tiers (asserted from register;
  fire/building sources correctly deferred from 22-source loaded pack).
- R-037 (8), R-041 (10), R-078 (10), R-079 (10), R-080 (8), R-082 (8):
  positive/negative/UNKNOWN/missing-fact cases, invalid values, MIDC
  separation, routing/regime separation, composition limits, ET-117/118/119
  and ET-v4-15 semantics.
- Cross-rule (5), fact ontology (8), classification (7), implemented (2),
  deferred (12), edge cases (10+), jurisdiction isolation (7), evidence gaps
  (6), regression (4): MIDC≠auto-BP, non-MIDC≠auto-BP, UNKNOWN construction
  stays insufficient, routing never exposed as applicability, R-082 never
  negates permission, R-079 never over-applies standalone, jurisdiction
  mismatch, GJ leakage, disjointness, batch-1/batch-2/location regression,
  GJ 19 unchanged.

Validation: `test_mh_fire_building.py` 139 passed; full suite 1692 passed;
`ruff check app/ tests/` clean; `tsc --noEmit` clean. Five draft-test
failures fixed in-task (source-pack inclusion → deferred-source assertions;
`result.value` → string `result`; R-037 match → actual not-safe message)
plus 4 ruff fixes. No pack-logic change.

## O. Jurisdiction Isolation

- DEFAULT_JURISDICTION IN-GJ preserved.
- GJ 19 rules, zero cluster IDs, zero cluster approval IDs (APR-032/038/
  039/040/041 absent from GJ rules).
- MH 26 active, zero cluster rules active.
- MH 128 facts; `construction` absent; F-BLD-10/11 and F-PA-02 GJ lookups
  raise JURISDICTION_MISMATCH.
- Active/deferred disjoint. No GJ facts in MH, no MH facts in GJ.
- Fire/building sources (SRC-121/123/124/067) verified in v5 register but
  correctly deferred from the 22-source loaded MH pack (166/188 deferred).

## P. Remaining Evidence Gaps

- UR-19 OPEN: MIDC DCR gazette text for R-037 (and R-036). Closes only with
  official MIDC DCPR.
- `construction` fact: no v5 definition, type, or allowed values. R-041
  needs a researched construction/structural-alteration fact before any
  encoding.
- F-LOC-05 granularity: named-body values (`<name>`) and SPA/NTDA mappings
  unmodeled beyond enum tokens; R-080/R-082 need site-specific authority
  tables.
- F-PA-02 coverage: which authorities have CFOs (UNK-018 closed via
  UNKNOWN, but positive data still sparse).
- F-BLD-10 classification: who assigns G-1/G-2/G-3/H/J to a given building
  (register: input fact, not derived).
- UDCPR currency: post-30-01-2024 amendments unchecked (SRC-124 note).
- APR-041 sequencing: no official source (requires-confirmation).
- R-042/FR-03: fire guard + chemical-sector renewal exception need official
  rule text before R-079 can compose.
- SLA CON-001: RTS legal limit vs portal values (display all; no
  applicability impact).
- Engine: no rule-composition, dynamic-authority, or regime-selector
  primitives (by design; do not add without measured MVP need).

## Q. Next Cluster Recommendation

Inspect the CURRENT `rule_register_v5.csv` implementation/status columns
after this audit (do not reuse an old recommendation blindly):

- Remaining un-audited IMPLEMENTATION_SAFE candidates not yet in
  active/deferred sets (e.g. boiler-lifecycle R-081 deemed-permission
  workflow, fire renewal R-099 conditional lifecycle, and any
  not-yet-triaged R-036 MIDC building-permission portal rule) are the
  natural next audit — each is workflow/lifecycle, not plain applicability,
  and will likely defer on the same architectural boundary.
- In parallel, the source-pack phase (166/188 deferred sources including
  SRC-121/123/124/067) should be scoped before any routing/regime rule is
  revisited: without loaded sources, citations cannot be served even if
  logic were encodable.
- Do not cut over DEFAULT_JURISDICTION and do not digitize sector lookup
  (R-014) or GIS layers until a demo scenario explicitly requires them.
