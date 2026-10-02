# Maharashtra EC Core Audit — R-001, R-064, R-074

Evidence-first, falsification-oriented audit. Jurisdiction: IN-MH (primary).
IN-GJ is regression/reference only. Date (UTC): 2026-09-29. Authoritative
inputs: CURRENT working-tree code plus the v5 registers under
`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`. Every identity
claim below is re-verified field-by-field from the current CSVs (never from
prior prose) and pinned by `backend/tests/test_mh_ec_core.py` (36 tests).

Prior-cluster guard: R-013/R-014/R-015/R-017 (consent chain) were audited
elsewhere and are untouched here — predicates, deferral reasons, tests, and
confirmation status unchanged; only read as composition context. All other
prior audit work is preserved. This audit makes **zero implementation
changes**.

## 1. Scope

In scope: R-001, R-064, R-074, their shared approval APR-001, the live
exception facet R-002 (behavioral context only — no status change), and the
EC decision inputs (facts F-PRD-01/02/03, F-PRC-01/02/03, F-LOC-02/03/07,
F-BLD-01; source SRC-001; unknowns UNK-033/UNK-010/UNK-004; UR-06; deps
DEP-002/DEP-030; edge tests ET-008/009/010/015/016/058/059/060/065/066/070/
071/v5-25). Out of scope: consent-chain internals, boiler/GW/fire/MIDC
clusters, any new primitive, fact, or rule.

## 2. Current Baseline

Verified from the working tree at audit time (code-executed, not assumed):

- MH active **26**, MH deferred **59**, MH confirmation **26**, MH facts
  **128**, GJ active **19**, `DEFAULT_JURISDICTION = "IN-GJ"`.
- Active APR-001 rules: **exactly `["R-002"]`** (pack-executed).
- Code states: R-001 ∈ deferred (FORMULATION_ONLY reason), R-064 ∈
  deferred (truncation + UNK-033 reason), R-074 ∈ confirmation ∩ UNKNOWN,
  R-074 ∉ deferred, all three ∉ active. R-002 ∈ active.
- No baseline drift during this audit (re-checked after the parallel
  consent-chain session landed: counts identical).

## 3. Identity Verification

| Field | R-001 | R-064 | R-074 |
|---|---|---|---|
| Title (register) | Prior EC – Sch item 5(f) Synthetic organic chemicals (same title all three) | same | same |
| Approval | APR-001 | APR-001 | APR-001 |
| Obligation | APPROVAL | APPROVAL | APPROVAL |
| Authority | AUT-001 (Cat A) / AUT-002 (Cat B) | same | same |
| Jurisdiction | CENTRAL (state-level appraisal for B) | same | same |
| Stage | PRE_ESTABLISHMENT | PRE_ESTABLISHMENT | PRE_ESTABLISHMENT |
| Predicate | `EC_5F_REQUIRED := F-PRD-01 == TRUE AND F-PRD-03 IN {SYNTHESIS,MIXED}` | `EC_5F_SCOPE := product in '<5(f) col-2 list>'; drug formulation-only -> OUTSIDE 5(f); blending/formulation-only of non-drug produ…` (**truncated mid-token in the register**) | `EC_5F_AND_8A := UNKNOWN when EC_5F_REQUIRED==TRUE AND EC_8A==TRUE (text silent on combination)` |
| Required inputs | F-PRD-01;F-PRD-03 | F-PRD-01;F-PRD-02;F-PRD-03 | F-PRD-01;F-BLD-01 |
| Register operator | == | **scope** (no such ConditionNode op) | - (guard) |
| Source / tier | SRC-001 / T1 | SRC-001 / T1 | SRC-001 / T1 |
| Effective | 2006-09-14 EXACT, OPEN | 2014-06-25 EXACT, OPEN | - / UNKNOWN |
| Status / implementation | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE | UNKNOWN / REQUIRES_CONFIRMATION |
| Rule kind | DETERMINISTIC | DETERMINISTIC | GUARD_OR_ROUTING |
| Deps / docs / timeline | SC-NBWL / - / SLA-032 | same | same |
| Register note | `F-PRD-01 UNKNOWN -> UNKNOWN. FORMULATION_ONLY -> do not auto-FALSE; mark UNKNOWN pending appraisal view` | `UNK-033` | `UNK-010` + v5 official-source check (Vanashakti, 2007 circular, 2025 OM — none resolves) |
| Code state | deferred | deferred | confirmation-gated + UNKNOWN-gated |

Context R-002: `SMALL_UNIT := F-PRC-01 < 25 AND F-PRC-02 < 25 AND
F-PRC-03 == FALSE` (water m³/day; fuel TPD; not MAH per MSIHC 1989),
effective 2014-06-25 EXACT, SRC-001 T1 (Item 5(f) col 5, S.O.1223(E)
27-03-2020 fn 76), active, builder effective date matches register.
APR-001 (`approvals.csv`): APPROVAL/PRE_ESTABLISHMENT,
ACTIVITY+LOCATION-dependent, AUT-001/AUT-002, legal basis EIA 2006 Sch
5(f) + para 2 + GC + SC, `rule_ids = R-001;R-002;R-003;R-004;R-005` —
**R-064/R-074/R-075 are not members of the approval's own rule list**.
Trigger summary encodes the full tree: 5(f) product → A if outside a
notified estate (unless small-unit exception) → B if inside or small →
GC escalates B→A. Confidence: HIGH (rule) / product-scope needs expert
input; implement_status SAFE (logic) with "product scope fact must be
supplied, never inferred".

## 4. EC Rule Chain Reconstruction

R-001/R-064/R-074 are **not three independent boolean applicability
rules**. Their semantic roles:

- **R-001 — EC trigger (applicability core).** Answers "is this a 5(f)
  project?" over product-scope (F-PRD-01) × process-mode (F-PRD-03).
  Affirmative trigger; says nothing about category.
- **R-064 — scope gate (item/sub-item classification).** Answers "does
  this product fall inside the 5(f) col-2 description, with the
  formulation-only carve-outs?" Three output branches are visible even in
  the truncated text: listed product → inside; drug formulation-only →
  OUTSIDE (FALSE); non-drug blending/formulation-only → UNKNOWN
  (UNK-033). It is the rule that gives FORMULATION_ONLY its meaning.
- **R-074 — combination guard (routing, not applicability).**
  Answers "5(f) EC holder that also trips 8(a): one EC or two?" with a
  hard UNKNOWN (text silent). Consumes R-001's and R-007's *outputs*,
  not project facts alone.
- **R-002 — small-unit facet (threshold + MAH exclusion).** Answers
  "Cat-B small-unit path?" — per APR-001's trigger summary, smallness is
  an exception to *Category A*, not an exemption from EC (R-003 sends
  small units to B). Live and rule-level correct.
- **R-003 — category assignment (requires composition).**
  `CAT_BASE := A/B` over F-LOC-02 **and R-002's output** (`facts =
  F-LOC-02;R-002`, operator CASE). A rule consuming another rule's
  output — unrepresentable without composition. Deferred, correctly.
- **R-004 — General Condition escalation (category modifier).**
  `CAT A IF CAT_BASE==B AND ANY(F-LOC-07 sub-facts)` — needs the
  `ANY` quantifier over an OBJECT fact plus CAT_BASE. Deferred.
- **R-005 — estate-coverage gate (confirmation).** `F-LOC-03 == TRUE`
  exempts nothing by itself ("do not auto-exempt"; scope read from the
  estate EC). Confirmation-gated (UNK-004 per-estate evidence).
- **R-008 — 8(a) GC meta-rule** (`NOT_APPLICABLE`, deferred);
  **R-075 — EC validity lifecycle** (DATE arithmetic over an unmodeled
  grant date, deferred).

APR-001 after these rules are considered together is a **five-node
decision tree** (trigger → scope → category → escalation → estate
coverage, plus validity/renewal downstream) of which exactly one node —
the small-unit threshold facet — is live. The live system therefore
cannot determine EC requirement; §8 proves what it reports instead.

## 5. R-001 Audit

Structurally encodable (boolean AND + `in`, EXACT dates, T1 source) but
**unsafe to encode**: with F-PRD-03 = FORMULATION_ONLY (or BLENDING_ONLY)
the `in {SYNTHESIS,MIXED}` leaf evaluates FALSE, so the rule reports
DOES_NOT_APPLY — while the register mandates UNKNOWN pending appraisal
view (note) and ET-016 mandates "never FALSE by default". Executable
proof of the fail-open direction is pinned in-test via a bare probe
condition (never `_encode`, which correctly refuses R-001). TRUE is also
insufficient: EC_5F_REQUIRED==TRUE still needs scope (R-064) and category
(R-003) before any EC verdict. F-PRD-01 is an expert/appraisal
classification ("never inferred from name"), so TRUE carries an
authoritative-input assumption the intake path does not verify. Verdict:
stays deferred; reason accurate and complete.

## 6. R-064 Audit

Three independent blocks, any one fatal: (1) the predicate is **truncated
mid-token in the register itself** (300-char cell ending "…of non-drug
produ"; pinned) — the full scope text must be re-extracted from SRC-001
before any encoding; (2) UNK-033 is OPEN — the non-drug
blending/formulation branch has no authoritative answer (ET-071 expects
UNKNOWN); only the drug-formulation-only → FALSE branch is settled
(ET-070); (3) the register operator is `scope` — a product-membership
test over a col-2 description list with carve-outs — which no
ConditionNode implements (`eq/in/gte/lte/gt/lt` only); F-PRD-02's enum-set
(PESTICIDE_TECHNICAL/BULK_DRUG/…) is the adjacent input but the register
binds R-064 to free product description, not to that set. Verdict: stays
deferred; reason ("condition text truncated in register; UNK-033 open")
verified verbatim against the code entry.

## 7. R-074 Audit

Correctly held out on two independent grounds: (1) evidence — UNK-010
OPEN + UR-06 OPEN (no MoEFCC/SEIAA statement on 5(f)+8(a); the v5 check of
Vanashakti 05-08-2025, the 2007 committee-routing circular, and the
Dec-2025 SAF/4(a) OM correctly refused secondary "same category" reports
as evidence); ET-066 and ET-v5-25 pin UNKNOWN as a hard block;
(2) architecture — the predicate consumes EC_5F_REQUIRED (R-001's output)
and EC_8A (R-007's output): cross-rule composition with no primitive, and
GUARD_OR_ROUTING kind (never APPLIES by design). R-074 is also correctly
absent from APR-001's `rule_ids` (it is not an applicability input).
Verdict: confirmation + UNKNOWN gates hold; no change.

## 8. APR-001 Exception-Facet Analysis

Live behavior (pack-executed proof): the approval's only active rule is
the R-002 exception facet, and `summarize_by_approval` prioritizes
APPLIES > DOES_NOT_APPLY > CONDITIONAL > INSUFFICIENT_DATA, a priority
designed for trigger rules, not exception facets. Consequences:

- Small unit (facts complete) → R-002 APPLIES → APR-001 "applies".
  Directionally toward EC (Cat-B path) but the category is never
  computed (R-003 deferred) and product mode is never consulted — a
  formulation-only small unit also reports "applies" although the
  register requires UNKNOWN (non-drug) or OUTSIDE (drug-only).
- **Not-small unit (facts complete) → R-002 DOES_NOT_APPLY → APR-001
  "does_not_apply".** For a large greenfield synthetic-organic unit
  outside a notified estate — the textbook Category-A EC case, where
  R-001 would fire TRUE and R-003 would assign A — the system reports
  **"EC does not apply".** This is a fail-OPEN false negative on the
  domain's primary clearance, proven executable (probe: F-PRD-01=True,
  SYNTHESIS, water 500, fuel 200 → `does_not_apply`).
- Missing F-PRC facts → INSUFFICIENT_DATA (fail-closed, correct; already
  pinned by batch-1 tests).

So yes: "exception does not apply" is currently aggregated into "EC does
not apply", and "exception applies" is aggregated into "EC applies"
without determining category. R-002 is rule-level correct (facet B);
**the approval-level composition "R-002 ≡ APR-001" is unsafe (F)**.
No status change is made: deactivating R-002 would erase verified
batch-1 work and break its pinned tests (including the missing-inputs
fail-closed pin and the derivation-wiring R-002 proof), while the real
repair — exception-role-aware aggregation or an encodeable guarded R-001
core — is a design decision beyond audit scope. Recorded as the P0
follow-up in §21.

## 9. FORMULATION_ONLY Analysis

1. It is the `F-PRD-03` (process_mode) enum value for units that only
   formulate, plus sibling `BLENDING_ONLY`; the register's R-001
   predicate admits only SYNTHESIS/MIXED.
2. Represented in `app/rules/facts.py:159` (allowed values) and in the
   R-001/R-064 register notes; in no rule logic (R-001 deferred).
3. Created by EIA 2006 Sch 5(f) col 2 as transcribed in R-064
   ("excluding drug formulations" / formulation-only carve-outs),
   sourced to SRC-001 T1.
4. It is a **product/process classification with exception-branch
   force**: drug-formulation-only → OUTSIDE 5(f) (FALSE, settled);
   non-drug blending/formulation-only → UNKNOWN (unsettled, UNK-033).
5. The ontology carries the value (enum present, validation accepts it).
6. It must **not** be derived — F-PRD-03 is applicant-supplied; no
   derivation exists and none is warranted.
7. Deriving it from product names would be inference without
   authoritative evidence (the register: scope "needs expert input",
   "never inferred").
8. No: drug-formulation-only is outside 5(f); non-drug
   blending/formulation-only awaits appraisal (UNKNOWN, never FALSE).
9. Yes — §8: the live facet ignores F-PRD-03 entirely, so it both misses
   the settled exclusion and fabricates verdicts where UNKNOWN is
   mandated. Nothing here is resolved by assumption; UNKNOWN/
   INSUFFICIENT_DATA preserved throughout.

## 10. UNK-033 Analysis

Exact question: "Does blending/formulation-only of non-drug synthetic
organic products fall in 5(f)?" Affects R-064 (scope branch) and, through
it, R-001 (trigger falsification ban). Approval APR-001. Currently cited
source: SRC-001 (T1, OFFICIAL_PRIMARY, MoEFCC PARIVESH consolidated text
as on 13-07-2026, accessed 2026-09-26, VERIFIED) — which is current and
proves the col-2 list and the drug-formulation carve-out but is
explicitly bounded ("does not state…", and the R-064 cell itself is
truncated). Needed: the complete 5(f) col-2 provision plus any
MoEFCC/SEIAA clarification on non-drug blending/formulation; status
OPEN, final UNKNOWN. It affects **applicability** (whether the trigger
may fire) and the **exception branch** (FALSE vs UNKNOWN), not category,
escalation, or routing. Severity: **BLOCKING** for R-064 activation and
for any R-001 encoding that must handle non-SYNTHESIS modes.

## 11. Category Coupling Analysis

R-001's trigger needs no category input itself — the coupling is that a
TRUE trigger is **legally inactionable without** R-003 (A/B assignment)
and R-004 (GC escalation), and R-003 in turn needs R-002's output:

| Required input | Maps to | Status |
|---|---|---|
| Product in 5(f) scope | F-PRD-01 (expert boolean) | fact present; applicant-supplied, unverified |
| Process mode | F-PRD-03 enum | fact present; FORMULATION_ONLY trap (§9) |
| Notified-estate situs | F-LOC-02 boolean | fact present; per-estate evidence OPEN (UNK-004) |
| Small-unit exception output | R-002 rule output | **lookup output — no composition primitive** |
| Category base | R-003 CASE output | deferred; needs R-002 + F-LOC-02 |
| GC escalation | R-004 ANY over F-LOC-07 object sub-facts | deferred; `ANY` unsupported; object sub-fact addressing unsupported; GIS-adjacent |
| Estate coverage | F-LOC-03 (R-005) | fact present; confirmation-gated (per-estate EC scope) |
| Production capacity / built-up area | no 5(f) capacity threshold exists (APR-001: "No capacity threshold"); built-up is 8(a) business (F-BLD-01, R-007/R-074) | not required for 5(f); must not be conflated |
| Chemical/process classification | MSIHC schedules (F-HAZ-01/02 → F-PRC-03 derivation) | derived fact present; feeds only R-002's MAH limb |

Net: every leaf input exists, but the two composition joints (R-002→R-003,
CAT_BASE→R-004) and the GC quantifier have no engine representation.

## 12. Category A/B Analysis

The system **cannot distinguish Category A from B** (nor B1/B2, which no
register row invokes). Category is not stored (no F-CAT fact; only
F-MPCB-01 sector codes, a different classification), not derived, and not
looked up (R-014 is the consent-chain lookup, unrelated to EIA
categories). Per APR-001's trigger summary, category assignment is
**required before the EC verdict is actionable** (it selects AUT-001 vs
AUT-002, public-consultation preconditions, and the small-unit meaning).
No category lookup is invented; R-003 stays deferred.

## 13. General Condition Analysis

R-004's trigger: CAT_BASE==B AND any F-LOC-07 sub-fact TRUE (within 5 km
of PA/CPA/ESA/inter-state/international boundary) → escalate to A; any
GC sub-fact UNKNOWN while CAT_BASE==B → CAT UNKNOWN. F-LOC-07 exists as
an OBJECT fact ("four sub-facts") but the engine has no `ANY`/EXISTS
quantifier and no object-sub-fact addressing; the situs inputs are
inherently geographic (5-km proximity), i.e. a **GIS/evidence dependency**,
not a boolean the engine may proxy. It is category escalation, not
applicability — encoding it as a boolean would corrupt the A/B
determination. Correctly deferred; edge tests ET-015/065 pin the UNKNOWN
and small-unit-B behaviors at register level.

## 14. Source and Version Audit

SRC-001 (sole source for all three rules): T1 OFFICIAL_PRIMARY, MoEFCC
PARIVESH, "EIA Notification 2006 – consolidated as on 13-07-2026",
effective 2006-09-14, accessed 2026-09-26, final VERIFIED. Proves verbatim
5(b)/5(e)/5(f)/5(h)/7(c)/8(a)/8(b), GC, SC, para 7(ii); footnote 98
records the Vanashakti quashing of 8(a) Note 1 (relied on by R-007).
Explicitly does not prove paras 9–10 (validity/monitoring — hence R-075
deferred), the 5(f)+8(a) combination (hence R-074 gated), or notified
estates (hence R-003/R-005 held). Currency is sound for the audited
claims. One evidence question flagged, not resolved: R-002's legal_basis
"as amended 25-06-2014" with effective 2014-06-25 sits beside a locator
citing insertion by S.O.1223(E) 27-03-2020 (fn 76) — whether the col-5
small-unit text was operative from 2014 or only from 2020 cannot be
decided from the available cells; the encoded EXACT 2014-06-25 window
stands on the register's authority and no behavior is changed. No mirror
sources are relied on anywhere in this cluster (all T1).

## 15. Fact Ontology Audit

| Fact | Type | Role in EC chain | Assessment |
|---|---|---|---|
| F-PRD-01 product_in_5f_scope | boolean, UNKNOWN allowed | R-001/R-064 gate | correct but authoritative-weight: expert/appraisal input, never inferred; intake does not verify authority |
| F-PRD-02 product_type_special | enum_set | R-064 adjacent (5(b)/5(h)/conditional regs) | too coarse for R-064's free-text col-2 scope; must not be substituted for it |
| F-PRD-03 process_mode | enum incl. FORMULATION_ONLY/BLENDING_ONLY | R-001 mode limb | correct and necessary; the trap is in rule semantics, not the fact |
| F-PRC-01/02 | number (m³/day; TPD) | R-002 thresholds | correct; strict `<` pinned (25 exactly NOT small) |
| F-PRC-03 is_MAH | derived boolean | R-002 MAH limb | correct; UNKNOWN-token fail-closed verified in-test |
| F-LOC-02 notified estate | boolean, UNKNOWN allowed | R-003 | correct; MIDC≠auto-notified pinned in description; per-estate evidence OPEN |
| F-LOC-03 estate EC coverage | boolean, UNKNOWN allowed | R-005 | correct; gated pending estate-EC scope evidence |
| F-LOC-07 GC 5km | OBJECT, four sub-facts | R-004 | structurally insufficient for the engine (no sub-fact addressing, no ANY); fact itself is the right shape for a future quantifier |
| F-BLD-01 built-up m² | number | R-074's 8(a) limb (via R-007) | correct; 8(a) range logic lives in active R-007, combination gated by UNK-010 |

No fact is added, removed, retyped, or derived by this audit. Two conflate
risks are explicitly refused: F-PRD-02 standing in for R-064 scope, and
F-PRD-01==TRUE standing in for EC verdict.

## 16. Engine Capability Audit

Representable today: boolean AND/OR/NOT, `eq/in/gte/lte/gt/lt` leaves,
three-valued logic, UNKNOWN/None fail-closed, LiteralNode sentinels,
effective windows. R-002 is fully inside this envelope (and tested).
Missing for the EC core, each load-bearing:

1. **Non-falsing set-membership** (R-001): a mode value outside the
   admitted set must yield UNKNOWN, not FALSE. Minimum: a guard semantic
   (value-dependent UNKNOWN injection for designated enum leaves) or a
   pre-evaluation scope gate. Not introduced here.
2. **Scope-membership operator** (R-064): `scope` over a description list
   with carve-outs. Minimum: either a digitized scope table + lookup, or
   an expert-attested boolean input replacing free-text scope. Not
   introduced here.
3. **Rule-reference composition** (R-003 consuming R-002; R-074 consuming
   R-001/R-007). Minimum: a composition primitive with three-valued
   propagation. Not introduced here.
4. **Quantifier + object traversal** (R-004 ANY over F-LOC-07). Minimum:
   EXISTS/ANY with UNKNOWN semantics (any-TRUE wins; all-FALSE false;
   else UNKNOWN). Not introduced here.
5. **Exception-role aggregation** (§8 defect): minimum a rule-role flag
   distinguishing trigger rules from exception facets at
   `summarize_by_approval` time. Design decision, not introduced here.
6. Not needed and not requested: GIS (GC proximity stays an evidence
   input), DATE arithmetic (validity is R-075's, deferred), lookups
   beyond the above, external data, LLM/embedding involvement of any kind.

## 17. Fail-Closed Scenario Matrix

Current-system result vs justified result (orchestration shares the same
`summarize_by_approval`, so rule-level outcomes propagate unchanged):

| # | Scenario | Current | Justified? |
|---|---|---|---|
| 1 | Clearly applicable: large SYNTHESIS unit, outside notified estate, non-MAH | DOES_NOT_APPLY | NO — fail-OPEN defect (§8) |
| 2 | Clearly non-applicable: drug-formulation-only | small→APPLIES / not-small→DOES_NOT_APPLY (both via R-002, ignoring product mode) | NO — right label possible for the wrong reason; no justified EC determination exists |
| 3 | Formulation-only, non-drug (UNK-033) | small→APPLIES / else DOES_NOT_APPLY | NO — register mandates UNKNOWN |
| 4 | Threshold boundary (24.99 vs 25; MAH TRUE/FALSE) | rule-level correct in all limbs (pinned) | Rule-level YES; approval-level verdict NO (same defect as #1 for the not-small limb) |
| 5 | Category unknown | category never computed | N/A — correctly absent rather than fabricated |
| 6 | Location/GC fact unknown (F-LOC-02/07) | unused by active rules; no verdict depends on them | YES (vacuous — nothing pretends otherwise) |
| 7 | General Condition unknown | GC never evaluated | YES (vacuous; R-004 deferred) |
| 8 | Exception known true (small) | APPLIES | PARTIAL — correct facet direction, wrong completeness (category unevaluated) |
| 9 | Exception known false (not small) | DOES_NOT_APPLY | NO — same defect as #1 |
| 10 | Multiple activities/product values | same as #1/#9 (product ignored) | NO |
| 11 | Missing critical EC input | INSUFFICIENT_DATA | YES — fail-closed verified (pinned) |

No expected legal outcome is fabricated: where the register is silent
(category, GC, combination), the system is silent too — except the two
fail-OPEN cells (#1/#9, plus #2/#3/#8 overstatements), which are the §8
defect.

## 18. Dependency Propagation

EC uncertainty is **contained**: no loaded edge consumes APR-001 (loaded
graph is exactly DEP-009 ×2: APR-008/APR-009 → APR-010; pinned). DEP-002
(APR-001 → APR-008, "EC required", PRACTICE_EXPECTED) is
YES_INFERRED/UNKNOWN and correctly unloaded — EC INSUFFICIENT_DATA can
never satisfy it, and a false EC DOES_NOT_APPLY (§8) can never *block*
CTE through the loaded graph either (APR-008 has no active rule and no
loaded incoming edge). DEP-030 (SC-NBWL → APR-001, EXPLICIT_LEGAL,
conditional on ESZ/10-km situs) is registered but unloaded; NBWL risk is
therefore neither satisfied nor denied by the system — correctly absent.
Downstream consequence of the §8 defect is bounded to the APR-001 verdict
itself (user-facing misreport), not to graph corruption.

## 19. Implementation Classification

- **R-001: C + E.** Evidence closure (FORMULATION_ONLY appraisal view;
  F-PRD-01 authority currency) AND new engine semantics (non-falsing
  set-membership). Unsafe to encode now; falsification proven executable.
- **R-064: C + E.** Evidence closure (re-extract complete predicate from
  SRC-001; UNK-033 clarification) AND new semantics (`scope` operator or
  digitized scope table + lookup).
- **R-074: C + E.** Evidence closure (UNK-010/UR-06 authoritative
  statement) AND new semantics (cross-rule composition).
- **R-002 (context, active): B** as a bounded facet — rule-level
  semantics correct and pinned. The approval-level composition
  "R-002 ≡ APR-001" is **F** (fail-OPEN false negative proven). No
  status change made (§8 rationale); the F is carried as documented
  technical debt with a P0 follow-up (§21), not as a silent repair.

## 20. Evidence Required for Closure

Minimum, in dependency order — nothing here is engine work except item 4:

1. **Complete R-064 predicate**: re-extract the full 5(f) col-2 scope
   text with carve-outs from SRC-001 (consolidated 13-07-2026); the
   register cell is truncated and cannot be encoded from.
2. **UNK-033 clarification**: MoEFCC/SEIAA statement on non-drug
   blending/formulation-only scope (or a confirmed "no statement
   exists, keep UNKNOWN" ruling with review date).
3. **FORMULATION_ONLY appraisal rule**: authoritative basis for mapping
   non-admitted modes to UNKNOWN (register note cites "appraisal view"
   without a source instrument — the instrument is the missing evidence).
4. **Non-falsing membership semantic** (minimal engine addition, separate
   design task): designated enum leaves yield UNKNOWN on unlisted
   values instead of FALSE.
5. **Category pipeline**: per-estate notified-status evidence (UNK-004)
   + composition primitive for R-003 (needs R-002 output) — only after
   1–4, since category without a safe trigger is moot.
6. **UNK-010 statement** (MoEFCC/SEIAA on 5(f)+8(a)): only for R-074;
   independent of 1–5.
7. **Exception-role aggregation design**: fixes the §8 approval-level
   defect regardless of 1–6 (even today: an exception facet must never
   aggregate to an approval DOES_NOT_APPLY).

Items 1–3 are the earliest blocking chain (§24).

## 21. Recommended Next Cluster

1. **P0 follow-up (design, not audit): APR-001 defect disposition.**
   Options: (a) exception-role flag in aggregation (small, principled —
   also protects future exception facets); (b) gate R-002 with a
   user-visible "partial EC signal" caveat; (c) leave documented until
   the R-001 core lands. Requires a rule-semantics decision, then a
   targeted implementation task that moves the pinned
   `test_large_unit_reports_does_not_apply` expectation deliberately.
2. **Next audit cluster (inventory P2 unchanged): R-021 + R-065/R-066/
   R-050** controlled-substance/legal-metrology duties — R-065 remains
   the closest-to-encodable rule in the pack.
3. **After consent-chain landing**: re-verify DEP-009 unblocking
   (APR-008/APR-009 rules activate → R-018/R-096 readiness unblocks);
   no EC action needed.
4. **Do not next**: R-075/R-081 DATE arithmetic, GIS-dependent R-051/
   R-097, incentive layer — all blocked on evidence/primitives this
   audit re-confirmed as unjustified.

## 22. Test Results

- Focused: `backend/tests/test_mh_ec_core.py` — **36/36 pass** (also
  re-verified 12/12 inventory pins alongside: 48/48).
- Full backend suite: **1980 passed, 0 failed** (1881 prior working-tree
  baseline + 36 this audit + ~63 from the parallel hazardous-waste
  session's new test file; no skips in this run).
- Ruff: this audit's files clean. `ruff check app/ tests/` reports one
  error in `tests/test_mh_hazardous_waste_authorization_chain.py`
  (I001 import sorting) — a parallel session's new file, deliberately
  untouched.
- Frontend `tsc --noEmit`: clean (no output).

## 23. Files Changed

Exact list (this audit only):

- `audit_mh_ec_core.md` (new — this report).
- `backend/tests/test_mh_ec_core.py` (new — 36 tests).
- `audit_mh_remaining_inventory.md` (one-sentence correction: the 26
  R-xxx-keyed `requires_confirmation` rows match the code gates exactly;
  the sweep's earlier "no rule-level entries" phrasing was wrong).

Not changed: `backend/app/seed/mh/approvals.py` (R-001/R-064 reasons
verified verbatim; R-074 gates verified), R-013/R-014/R-015/R-017 and
their tests, `applicability.py` (parallel session's live edit observed,
not touched), all other pack/engine/fact code, all other tests,
ARCHITECTURE.md / PRD.md / RULES.md (no new architectural fact or
product-scope change owned by this audit).

## 24. Final Determination

R-001, R-064, and R-074 are correctly held out of the active pack, for
the exact reasons coded — each verified against current registers,
sources, facts, engine semantics, and edge tests, with the FORMULATION
trap and the approval-level defect proven executable rather than
asserted. The audit's falsification burden is met in both directions:
nothing that is live is defended beyond its facet, and nothing deferred
is promoted on structural plausibility alone.