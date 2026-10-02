# Maharashtra Controlled-Substance Cluster Audit — R-065 / R-066 / R-050

Evidence-first, falsification-oriented audit. Primary target R-065; R-066
and R-050 as dependency/context analysis only. Jurisdiction: IN-MH.
IN-GJ regression/reference only. Date (UTC): 2026-09-29. All identity
claims re-verified field-by-field from CURRENT registers and pinned by
`backend/tests/test_mh_controlled_substance_cluster.py` (48 tests).

Prior-work guard: R-001/R-002/R-064/R-074 (EC), R-013/14/15/17 (consent),
R-018/R-096 (HW) and all prior audit tests/reports are untouched. A
parallel MSIHC session deferred R-021 mid-audit (observed, untouched;
baseline below reflects it). Zero implementation changes.

## 1. Scope

R-065 (CWC declarations, APR-058) primary; R-066 (NCB Schedule A,
APR-057) and R-050 (Legal Metrology packer, APR-048) for relationship
analysis. Inputs: facts F-CWC-01/02/03, F-NDPS-01, F-OTH-01, F-LM-01/02;
sources SRC-062/095/098/099/108; edge tests ET-102–105; UNK-022;
CND-013/014; CMP-021; SLA-039; chem_specific_branches CWC/NDPS rows.
Out of scope: consent/EC/HW internals, any new primitive, fact, or rule.

## 2. Current Baseline

Code-executed at audit time: MH active **26**, MH deferred **60**
(59 + R-021 by the parallel MSIHC session), MH confirmation **26**,
MH facts **128**, GJ active **19**, DEFAULT_JURISDICTION IN-GJ. Cluster
code states: R-065/R-066/R-050 all ∈ deferred ∩ safe-allowlist, ∉
active, ∉ confirmation, ∉ DNI. None of the three has a builder, an
authority string, a loaded dependency, or a document requirement.

## 3. Identity Verification

| Field | R-065 | R-066 | R-050 |
|---|---|---|---|
| Title | CWC declarations (initial/annual) to NACWC | NCB registration – controlled substances (Schedule A) | Legal Metrology packer registration |
| Approval | APR-058 (COMPLIANCE_APPROVAL, RETURN, OPERATION, THRESHOLD_DEPENDENT) | APR-057 (REGISTRATION, PRE_OPERATION, ACTIVITY_DEPENDENT) | APR-048 (REGISTRATION, OPERATION, ACTIVITY_DEPENDENT; implement REQUIRES_OFFICIAL_CONFIRMATION, confidence LOW) |
| Authority | National Authority CWC (Cabinet Secretariat), CENTRAL — no AUT record | Narcotics Control Bureau, CENTRAL — no AUT record | AUT-019 (Controller LM Maharashtra; authority REQUIRES_CONFIRMATION, never defaulted) |
| Predicate | `CWC_DECL := F-CWC-01 > 200 OR F-CWC-02 > 30 OR Sch2A*>1 kg OR Sch2A>100 kg OR Sch2B>1 t OR Sch3>30 t (F-CWC-03)` | `NCB_REG := F-NDPS-01 contains any Schedule A substance` | `LM_PC_CHAPTER_II := F-OTH-01==TRUE AND NOT(F-LM-01 > 25 kg or 25 L) AND NOT(F-LM-02 IN {IND…} AND marked 'not for retail sale'); r.27 duty unextracted → CONDITIONAL` |
| Inputs | F-CWC-01;F-CWC-02;F-CWC-03 | F-NDPS-01 | F-OTH-01;F-LM-01;F-LM-02 |
| Register op | `>` | `IN` | `==` |
| Source / tier | SRC-098 / T2 | SRC-099 / T2 | SRC-095 / T2 + SRC-062 / T3 |
| Effective | `-` / UNKNOWN | 2013 / YEAR_ONLY | `-` / UNKNOWN |
| Status | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, DETERMINISTIC | same | same |
| Notes | "Strictly greater-than" | — (ET-105: acetic anhydride → TRUE) | positive duty LOW confidence |
| Timeline | SLA-039 (90 d ADPA / 60 d ADAA, LEGAL, VERIFIED — deadline layer, not in MH pack) | — | — |
| Deps / docs | none registered, none loaded | none | none |

## 4. R-065 Semantic Reconstruction

**Threshold-triggered compliance RETURN duty** (not a licence, not a
project-stage approval in the industrial sense): OPERATION-lifecycle
annual declarations to NACWC. Six-limb OR over two scalar OCPF limbs
(unscheduled DOC synthesised >200 t/yr prev year; PSF chemical >30 t/yr)
plus four schedule-quantity limbs over listed chemicals (Sch 2A* >1 kg;
Sch 2A >100 kg; Sch 2B >1 t; Sch 3 >30 t). Substance identity matters
(DOC vs PSF vs schedule class); per-limb units differ (t/yr vs kg vs t);
intended use does not enter (production/processing/consumption all
covered by the branch trigger); storage-vs-manufacture is not
distinguished; location does not enter (CENTRAL, plant-site scope
baked into the facts); authority is single (NACWC, no routing);
lifecycle OPERATION with annual recurrence (CMP-021 ADPA/ADAA).

## 5. R-066 Semantic Reconstruction

**Independent REGISTRATION duty** (not a refinement of R-065):
manufacture/possession/sale/consumption — plus purchase/storage per
SRC-108 — of any Schedule A controlled substance requires NCB
registration *before handling* (PRE_OPERATION). Disjoint statute
(NDPS/RCS Order 2013 vs CWC Act 2000), disjoint authority (NCB vs
NACWC), disjoint stage (PRE_OPERATION vs OPERATION), disjoint inputs
(F-NDPS-01 vs F-CWC-*), disjoint regime (REG-NDPS vs REG-CWC). No
refinement, no document/content role, no lifecycle continuation, no
routing — and no composition: R-066 never consumes R-065 output.

## 6. R-050 Semantic Reconstruction

**Independent packaging-law duty, not a controlled-substance rule.**
LM(PC) Rules 2011 Chapter II applicability screen (exclusions) for
packers of pre-packaged commodities: F-OTH-01==TRUE minus the >25 kg/L
exclusion minus the industrial/institutional-marked exclusion. Regime
REG-OTH, STATEWIDE, AUT-019. It does not belong in the
controlled-substance chain — the inventory's grouping was
"chemical-adjacent duties", and even that overstates it: no shared
statute, input, authority, or lifecycle event with R-065/R-066. The
register itself caps it: the positive registration duty (r.27) is
unextracted, so the rule can only ever yield CONDITIONAL.

## 7. Evidence Audit

- **SRC-098** (R-065): T2 OFFICIAL_GUIDANCE, NACWC Cabinet Secretariat,
  n.d./n.d. Proves all six thresholds + ADPA/ADAA deadlines. Does NOT
  prove CWC Act section numbers, nor whether a specific product is a
  DOC/PSF (applicant-supplied classification). T2, not T1 statute —
  sufficient for thresholds as guidance, insufficient alone for a
  statutory-determination claim without the Act text.
- **SRC-099** (R-066): T2 OFFICIAL_LIST (CBN, RCS Order 2013, n.d.).
  Proves the closed 7-substance Schedule A + B/C export/import lists.
  Does NOT prove registration procedure (lives on the NCB portal,
  SRC-108 T3) or **later amendments** ("not checked" — APR-057 notes).
  chem_specific_branches calls the same research T3; the T2/T3
  characterisation tension is noted, not resolved.
- **SRC-108**: T3 OFFICIAL_PORTAL (NCB precursor guidelines). Proves
  registration mandatory incl. purchase/storage; does not prove
  timelines. Never a determinism-critical source — fine as context.
- **SRC-095** (R-050): T2 OFFICIAL_CONSOLIDATED_RULES (DoCA), r.3
  current text w.e.f. 01-01-2018. Proves exclusions (r.2(bb)/(bc), r.3,
  r.26). Does NOT prove the r.27 registration duty or timelines —
  the exact text the duty depends on.
- **SRC-062** (R-050): T3 OFFICIAL_PORTAL (MH LM). Bounded
  ("only claims tied to stated locators"); proves no duty text.
- Currency: no amendment/repeal instrument is registered for any of the
  three regimes beyond the noted gaps (RCS post-2013, LM post-2018
  consolidation). UNK-022 is CLOSED_V3 (branches classified) — no open
  unknown covers this cluster except the amendment-currency notes above.

## 8. Fact Ontology Audit

| Fact | Type | Assessment |
|---|---|---|
| F-CWC-01 unscheduled DOC synthesised t/yr | number, t/yr | correct; synthesis + prev-year qualifiers baked into the label; applicant-supplied |
| F-CWC-02 PSF synthesised t/yr | number, t/yr | correct; same caveats |
| F-CWC-03 scheduled chemicals | LIST of `{schedule, qty}` | **blocking shape**: elements carry no unit field, so per-element qty cannot be compared against kg/t thresholds without a unit assumption the registers never supply |
| F-NDPS-01 controlled substances handled | bare LIST, no element contract | under-specified: ET-105 suggests name strings, nothing pins strings vs objects; "handled" vs trigger verbs (manufacture/possession/sale/consumption/purchase/storage) unmapped |
| F-OTH-01 sells prepackaged | boolean | correct |
| F-LM-01 max package size | number, unit `kg_or_L` | **conflated**: one number for mass-or-volume; r.3 exclusion is package-type-dependent |
| F-LM-02 buyer type | enum incl. MIXED | coarse: exclusion is per-package (marked), fact is per-project buyer mix |
| package-marking ("not for retail sale") | — | **absent**: no F-LM-03, no marking-labelled fact exists |

No fact conflates multiple legal concepts except F-LM-01 (kg/L) and
F-LM-02 (project mix vs package marking). No new facts created.

## 9. Threshold/Boundary Analysis

Authoritative boundaries (all strict, pinned): CWC limbs strictly `>`
(ET-104: DOC 200 → FALSE, 200.1 → TRUE; register "Strictly
greater-than"); LM r.3 exclusion strictly `>` 25 (ET-102: 25 kg retail
→ Chapter II applies; 25.1 → does not); industrial-marked exclusion
(ET-103 → does not apply); Schedule A membership (ET-105:
acetic anhydride → TRUE). Scope of application: per-limb, per-schedule-
class — the register never states per-chemical vs aggregate for the
Schedule limbs, and no CWC per-vs-aggregate rule is evidenced in-repo
(see §10). Zero quantities evaluate FALSE on scalar limbs (no
zero-special rule evidenced). Missing/None/UNKNOWN on any scalar limb →
that limb unevaluable (None), never FALSE.

## 10. Multi-Substance/Aggregation Analysis

R-065's schedule limbs (`Sch2A*>1 kg` etc.) range over the F-CWC-03
object list: each requires per-element schedule match + quantity
comparison against a per-class threshold — i.e. list quantifiers with
grouped thresholds. No MAX/ANY/ALL/SUM/EXISTS semantic is assumed:
**none is implemented because none is evidenced**. Whether the 1 kg
Sch2A* threshold applies per chemical or summed across Sch2A*
chemicals is unspecified in SRC-098's proved claims and the register —
an evidence gap independent of the engine gap (no external CWC
interpretation imported). R-066 needs only ANY-match (membership), the
R-096-proven shape — but currency/shape caveats (§5/§8) keep it out.
R-050 needs no aggregation (single max-package scalar + buyer enum).

## 11. UNKNOWN/Fail-Closed Analysis

Scalar limbs: missing/None/"UNKNOWN" → limb None → single-limb rule
INSUFFICIENT_DATA; in a multi-tree OR, a None limb + FALSE limb →
CONDITIONAL (pinned) — the disjunction can never collapse to a clean
FALSE while any input is unknown. List limbs: unrepresentable, so they
can never contribute TRUE *or* FALSE — any verdict that requires their
falsity is unreachable. F-CWC-03 `[]` carries no register completeness
rule ("none handled" vs "not yet inventoried"), so emptiness cannot
close the schedule limbs either. Net: with current facts+engine, R-065
could at most emit APPLIES (scalar limb TRUE, monotonic and safe) or
INSUFFICIENT_DATA/CONDITIONAL — never a safe DOES_NOT_APPLY. A rule
that cannot safely return one of its verdicts is a one-directional
screen, a role the engine does not have (same lesson as the EC
exception-facet audit). No legal default (e.g. "undeclared means
undeclared") is evidenced; none assumed.

## 12. Authority/Routing Analysis

R-065: single CENTRAL authority (NACWC) — no quantity/class/location
routing; stage OPERATION matches the annual-duty lifecycle. R-066:
single CENTRAL authority (NCB) — no routing; PRE_OPERATION matches
"registration before handling". R-050: AUT-019 STATE, explicitly
REQUIRES_CONFIRMATION / never-defaulted — the authority itself is
unresolved for a concrete unit. Neither NACWC nor NCB has an AUT-xxx
record (free-text approval authority_ids, zero active rules there) —
display-metadata gap, not an applicability blocker, recorded for the
future authority-completeness pass. No dynamic routing anywhere in
this cluster; nothing to (mis)encode as applicability.

## 13. Engine Representability

Falsification result for "closest-to-encodable": **falsified**.
Scalar DOC/PSF limbs fit Leaf+AND/OR+`>`+UNKNOWN+effective-omission
(the YEAR_ONLY/UNKNOWN omission policy covers R-065's datelessness, as
it does R-030/R-035). But the registered predicate is a 6-way OR and
the engine cannot narrow a disjunction: omitting the four schedule
limbs turns Sch-only triggering activity into DOES_NOT_APPLY (proven
executable with a probe that never enters the pack). The schedule
limbs need per-element schedule classification + numeric comparison +
per-class thresholds over unit-less `{schedule, qty}` objects —
EXISTS-with-conjunction, absent by design. R-096's precedent does not
transfer: its ANY reduced exactly to token-overlap on lab-conclusion
strings, while R-065 needs numeric per-element thresholds with mixed
kg/t units the fact does not even carry. Minimum missing capabilities:
(1) list quantifiers with per-element predicates; (2) per-element unit
handling; (3) a closable-disjunction or one-directional-screen role.
None introduced.

## 14. Attack Matrix

Probes only (never `_encode`, never the pack); register-mandated
outcome vs probe outcome:

| # | Input | Register-mandated | Probe result | Safe? |
|---|---|---|---|---|
| 1 | DOC 200.1 / PSF 5 | APPLIES | applies | n/a (limbs alone) |
| 2 | DOC exactly 200 | limb FALSE (strict >) | does_not_apply (limbs) | n/a |
| 3 | DOC 50, PSF 5, Sch2A* 5 kg | APPLIES | **does_not_apply** | **NO — fail-OPEN proof** |
| 4 | Missing qty ({} / None) | INSUFFICIENT_DATA | insufficient/conditional | YES |
| 5 | Unknown substance in F-CWC-03 | limb unevaluable | unrepresentable | YES (vacuous — nothing pretends) |
| 6 | Known substance, unknown schedule tag | unevaluable | unrepresentable | YES (vacuous) |
| 7 | Multiple substances/classes | per-class evaluation | unrepresentable | YES (vacuous) |
| 8 | Multiple quantities, mixed kg/t | per-element + unit norm | unrepresentable (no unit field) | YES (vacuous) |
| 9 | Exemption condition | none registered for CWC | n/a | n/a |
| 10 | Greenfield, no prev-year production | scalars FALSE; schedule limbs still live | partial FALSE | NO if read as duty verdict (same trap as #3) |
| 11 | Toluene in F-NDPS-01 (R-066 probe) | FALSE (if Schedule A closed) | does_not_apply | CONDITIONAL on amendment currency |
| 12 | Acetic anhydride (ET-105) | TRUE | applies (probe) | mechanics only; currency assumed |
| 13 | F-NDPS-01 [] | no register rule | does_not_apply (probe) | unpinned — emptiness semantics unevidenced |
| 14 | UNKNOWN embedded in list | INSUFFICIENT_DATA | insufficient/conditional (tree fix) | YES |
| 15 | Toluene + UNKNOWN | INSUFFICIENT_DATA | insufficient/conditional | YES |

Legal expectations are taken only from register cells/edge tests
(ET-102–105); cells 5–8/13 assert "no verdict possible", not invented
outcomes.

## 15. Downstream Dependency Analysis

Containment is total: zero loaded edges and zero document requirements
touch APR-048/057/058 (pinned); SLA-039 lives in the deadline layer,
unloaded in the MH pack. CMP-021's trigger reads "APR-058 thresholds
met" — threshold facts, not any rule output — so R-065 UNKNOWN cannot
ready anything and R-065 APPLIES would not bypass any prerequisite
(there are none). A future R-065 activation changes no graph behavior.

## 16. Implementation Classification

- **R-065: E + C.** E primary: schedule-quantity limbs need list
  quantifiers + per-element units (earliest structural block; partial
  encoding proven fail-OPEN). C secondary: T2-only guidance without Act
  section numbers; DOC/PSF classification applicant-supplied;
  per-vs-aggregate unspecified; datelessness acceptable only via the
  omission policy. RETURN record-class does not alone disqualify
  (R-093/R-094 precedent), but it cannot rescue unrepresentable limbs.
- **R-066: B/C boundary → C.** Structurally list-overlap-shaped (the
  R-096 pattern), but Schedule A currency is explicitly unchecked,
  element shape unpinned, and handled-vs-trigger-verb mapping unmapped.
  Evidence closure first; then bounded.
- **R-050: C + D.** C: r.27 positive-duty text unextracted (register
  caps output at CONDITIONAL), LOW duty confidence, AUT-019 and APR-048
  confirmation-gated. D: package-marking fact absent; F-LM-01 kg/L
  conflation. Independent packaging-law chain — not controlled
  substances.

## 17. Implementation Decision

**ZERO changes.** R-065 fails the Phase-14 conjunction at "no
unsupported aggregation" (and units/closure/membership-shape). R-066
and R-050 are classification-only per the task constraint, and each
fails independently anyway. All three stay deferred under their
existing, verified-accurate reasons. No regression tests for new
behavior are owed; the 48 new tests pin identity, evidence bounds,
falsification probes, and containment.

## 18. Evidence Gaps

1. CWC Act 2000 section text (thresholds currently guidance-only).
2. DOC/PSF product-classification authority (applicant-supplied today).
3. Per-vs-aggregate reading of Schedule thresholds (unspecified).
4. Unit contract for F-CWC-03 qty elements (absent).
5. RCS Order post-2013 amendment sweep (Schedule A currency).
6. F-NDPS-01 element-shape + handled-vs-trigger-verb mapping.
7. LM(PC) r.27 duty text + timelines (CONDITIONAL ceiling until then).
8. Package-marking fact + F-LM-01 unit split (D-class).
9. AUT records for NACWC/NCB (metadata completeness).
10. T2/T3 characterisation tension for NACWC guidance (branch file says
    T3, sources.csv says T2 — harmless but unreconciled).

## 19. Remaining Risks

- The "closest-to-encodable" reading dies hard: scalar limbs are
  necessary but nowhere near sufficient; reviewers must not re-propose
  partial encoding without answering §13.
- R-066's overlap mechanics will tempt a quick activation; the
  currency/shape gaps (§5/§8) are the guardrail — membership FALSE on
  a post-2013-listed substance is a fail-OPEN false negative.
- F-CWC-03's unit-less qty is a latent trap for any future quantifier
  work: units must be fixed in the fact before the engine, not assumed
  in code.
- APR-048's LOW-confidence duty + confirmation-gated authority make
  R-050 a double-gated no-go; its exclusion limbs (ET-102/103) are
  correct but legally insufficient for any verdict.

## 20. Recommended Next Cluster

1. **R-054** (EC expansion exemption, APR-052): last IMPLEMENTATION_SAFE
   approval-rule without a focused audit or explicit code triage;
   evidence-shaped (auditor-certificate workflow facts + UNKNOWN
   effective date), pairs with the consent-chain landing.
2. **R-021 follow-up read** (parallel MSIHC session's triage): verify
   the new deferral reason against ET-081/SRC-016 when that session
   lands — no action now.
3. **R-059/R-071/R-072/R-076 hygiene**: one-line explicit code-triage
   notes for intentionally-unmodeled guards (no audit sessions).
4. Do not next: R-066 activation (currency first), GIS/MAITRI items,
   incentive layer.

## 21. Test Results

- Focused: `backend/tests/test_mh_controlled_substance_cluster.py` —
  **48/48 pass**. My prior files re-verified alongside: EC-core 36/36
  (after a 59→60 baseline maintenance edit forced by the parallel
  R-021 triage), inventory 12/12 — 96/96 total, ruff clean on all
  three files.
- Full backend suite: **2074 passed, 3 failed** — all 3 failures are
  stale deferred-count pins (`== 59`) invalidated by the parallel
  MSIHC session's legitimate R-021 deferral: 1 in my EC-core file
  (fixed, see above) and 2 in the parallel session's own
  `test_mh_hazardous_waste_authorization_chain.py`, left for its
  owning session per the do-not-modify-unrelated-tests rule. No
  failure touches cluster semantics; every non-count assertion in
  the suite passes.
- Ruff: this audit's files clean. Full `ruff check app/ tests/`
  reports one I001 error in the parallel HW session's new test file
  (untouched, same ownership as above).
- Frontend `tsc --noEmit`: clean (no output).

## 22. Files Changed

Exact list (this audit only):

- `audit_mh_controlled_substance_cluster.md` (new — this report).
- `backend/tests/test_mh_controlled_substance_cluster.py` (new — 48 tests).
- `backend/tests/test_mh_remaining_inventory.py` (baseline maintenance
  on my own prior artifact: deferred 59→60, untriaged set minus R-021,
  following the parallel MSIHC session's legitimate R-021 triage).
- `audit_mh_remaining_inventory.md` (dated addendum noting the same).

Not changed: `backend/app/seed/mh/approvals.py` (R-065/R-066/R-050
reasons verified verbatim), R-001/R-002/R-064/R-074 and EC tests,
R-013/14/15/17 and consent tests, R-018/R-096 and HW tests,
`applicability.py`, all other pack/engine/fact code and tests,
ARCHITECTURE.md / PRD.md / RULES.md (no new architectural fact or
product-scope change owned by this audit).

## 23. Final Determination

The inventory's "closest-to-encodable" hypothesis for R-065 is
**falsified**: two scalar limbs are encodable, but the registered
predicate is a six-way disjunction whose four schedule-quantity limbs
need list quantifiers over unit-less `{schedule, qty}` objects, with
per-vs-aggregate semantics unspecified and guidance-only (T2) evidence
behind Act-unnumbered thresholds. Partial encoding is proven fail-OPEN;
the disjunction cannot be closed to a safe DOES_NOT_APPLY. R-065 stays
deferred (E + C). R-066 is an independent registration duty,
overlap-shaped but currency/shape-ungrounded (C). R-050 is a different
legal regime entirely (C + D). Zero implementation changes; the deferred
set grows by no entry from this cluster.
