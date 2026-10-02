# Maharashtra Hazardous Waste Authorization Content-Chain Audit — R-018 / R-096

Follow-up to `audit_mh_consent_category_chain.md` (R-013–R-017 untouched by
this task). Jurisdiction: IN-MH (primary). IN-GJ is regression-only. Date
(UTC): 2026-09-29. Authoritative source: v5 regulatory registers
(`UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`). Identity is
verified executably against the CURRENT CSVs at test time (same discipline
as `test_mh_cto_renewal.py` / `test_mh_consent_category_chain.py`).

## 1. Scope

First audit of ACTIVE rules: R-018 and R-096 (both APR-010, MPCB hazardous
waste authorisation). Burden of proof is on the implementation — the audit
tried to falsify it. Out of scope but inspected for separation:
R-013–R-017 (consent chain, deferred/DNI — not modified), R-056 (HW r.9
utilisation, active), DEP-009, DOC-001/002/003, SLA-004, CMP-008.

## 2. Current Baseline

- `DEFAULT_JURISDICTION = "IN-GJ"`. Unchanged.
- Before: MH active 26, MH deferred 59, MH confirmation 26, GJ active 19,
  MH facts 128, suite 1881 passed (incl. 12 parallel inventory pins).
- After: all counts identical; suite **1980 passed** (1881 + 63 new HW-chain
  + 36 parallel EC-core, landed independently in the working tree).
- Ruff clean (`app/`, `tests/`). Frontend `tsc --noEmit` clean.
- Pre-existing uncommitted work from earlier clusters plus parallel
  inventory/EC-core files left untouched.

## 3. Identity Verification

From CURRENT `rule_register_v5.csv` / `rules.csv` (test-pinned):

| | R-018 | R-096 |
|---|---|---|
| Title | Hazardous waste authorisation (Form 1 -> Form 2) | same |
| Approval | APR-010 | APR-010 |
| Authority / jurisdiction | AUT-003 (MPCB) / STATEWIDE | same |
| Lifecycle / stage | PRE_OPERATION | PRE_OPERATION |
| Predicate | `HW_AUTH := F-HW-01 == TRUE` (operator `==`) | `HW_SCH2_TEST` over F-HW-04 (register operator **ANY**): unlisted waste hazardous iff any Sch II characteristic met (A TCLP / B / C1 flash<60C / C2 pH / C3 reactive); without lab data → INSUFFICIENT_DATA |
| Inputs | F-HW-01 | F-HW-04 |
| Source / tier | SRC-013 r.6(1) / **T1** | SRC-120 Sch II / **T2** (DPCC-hosted copy) |
| Effective | 2016-04-04 EXACT, OPEN | same |
| Status | VERIFIED_CONDITIONAL / IMPLEMENTATION_SAFE, ACTIVE | same |
| Deps / docs / timeline | APR-008;APR-009 / DOC-001-003 / SLA-004 LEGAL | same |
| Notes | entry numbers from F-HW-02 supplied, never inferred | never infer a waste code; UNK-034 |

Live code matches exactly (single-leaf `eq True`; single-leaf `in`
11-token set; same dates/sources). APR-010: APPROVAL, ACTIVITY_DEPENDENT,
AUT-003, PRE_OPERATION, trigger generation/handling, precondition Consent,
rules R-018 (register lists R-018; R-096 verified via rules.csv +
builders). F-HW-01 BOOL_OR_UNKNOWN; F-HW-04 LIST_OR_UNKNOWN ("never coerced
to FALSE"); F-HW-02 LIST of {description, schedule, entry_no
(MPCB/consultant), qty_tpa}, entries supplied never inferred.

## 4. R-018 Semantic Reconstruction

Broad generation trigger: one boolean answers "does the occupier generate
HW?" TRUE→APPLIES, FALSE→DOES_NOT_APPLY, UNKNOWN/missing→INSUFFICIENT_DATA
(ET-054). Generation without stream detail still APPLIES **by register
design** — stream detail (F-HW-02) is Form-1 content, correctly absent from
the predicate. T1 HOWM r.6(1), exact window (pre-2016-04-04 → not-in-force,
tested). No composition, no lookup, no aggregation. Falsification
attempted on all nine scenarios; no unsafe verdict found.

## 5. R-096 Semantic Reconstruction

Independent characteristic trigger, NOT a refinement of R-018 and NOT a
duplicate: disjoint inputs (F-HW-04 vs F-HW-01), disjoint evidence (lab
characteristics vs generation flag). Semantics: lab-concluded Schedule-II
characteristic ⇒ waste is hazardous ⇒ authorisation applies. The engine
represents the register ANY as list-overlap (`any()`), which is exact — no
MAX/ALL/EXISTS assumed or needed. The 11-token set = 5 characteristic
classes + 4 test-method variants + 2 lab-conclusion summaries
(HAZARDOUS/MEETS_SCHEDULE_II, valid only as lab-reported outcomes inside
F-HW-04; unlisted/missing/UNKNOWN inputs below prove no lab-free path to
APPLIES). The register's "without lab data → INSUFFICIENT_DATA" holds for
every no-evidence representation. Combination with R-018 is APPLIES-first
priority, verified fail-safe in both contradiction directions.

## 6. APR-010 Analysis

ACTIVITY_DEPENDENT PRE_OPERATION approval, AUT-003 static/VERIFIED,
precondition Consent, validity "as granted" (no validity computation in
rules). Pack wiring complete and consistent: authority string, DOC-001
(CTE copy) + DOC-002 (CTO copy) + DOC-003 (compliance report), SLA-004,
ecMPCB portal entry, zero evidence-gap hints. Integration-into-consent
(2026 amendment) noted UNKNOWN in the register — display-level, no rule
impact. No duplication (single approval, two trigger rules).

## 7. F-HW-04 Analysis

Type LIST, label `lab_results_for_Schedule_II_tests`, unknown_allowed True,
no allowed-values enumeration (any list accepted; scalars/mappings
rejected; None always valid). Per-stream capable: each element is one
stream's concluded result; multi-stream supported without identity
collision because only presence-of-positive matters for applicability.
Laboratory results represented as concluded characteristics (limits live in
the lab under SRC-120/SRC-013, not in the engine). Schedule-I category NOT
represented here — correctly so (that is F-HW-02 content). Applicant-
supplied lab outcomes; sufficient as deterministic *applicability* input
(positive ⇒ hazardous ⇒ applies) while saying nothing about *which*
Schedule-I entry governs the stream.

## 8. Schedule-I Evidence Audit

hw_streams.csv: 54 rows from T1 principal text, each trigger requiring
occupier-declared process AND waste facts, each flagged UNK-034. The table
is reference, not inference: nothing in code maps names→entries (verified
by search). SRC-013 T1 proves r.3/Sch I+II definitions and Form duties;
explicitly not post-2016 amendments and not per-unit mapping. Determination
stays with MPCB/consultant via supplied F-HW-02 entries.

## 9. UNK-014 Audit

"HW Schedule I/II entry mapping per waste stream" — PARTIALLY_RESOLVED,
REQUIRES_CONFIRMATION, related to F-HW-02 (content), resolvable only by
MPCB/consultant determination. **Does not touch either active predicate**
(R-018 needs only the generation flag; R-096 needs only lab conclusions).
No predicate change required; content gap stays in the document/consultant
layer where the register puts it.

## 10. UNK-034 Audit

"HOWM Schedule I/II amendments after 2016" — OPEN, UNKNOWN. Engine impact
assessment: the engine never computes limits (no TCLP/pH arithmetic), so
stale thresholds cannot corrupt a verdict; the risk is confined to (a) labs
testing against a superseded Schedule II, and (b) hw_streams reference
currency — both outside the decision path. Recorded as R-096's bounded
currency caveat (tested: SRC-120 tier T2 + does-not-prove text). Closure
needs the MoEFCC consolidated HOWM text; no code action until then.

## 11. Per-Stream / Multi-Stream Analysis

Multiple streams/categories/routes/quantities: representable as F-HW-04
element lists (mixed clean + positive → APPLIES, tested; all-clean →
DOES_NOT_APPLY, tested). No element identity needed for the applicability
verdict; no aggregation across streams (ANY is the register's own
operator, not an invention). MAX explicitly not assumed. Quantities,
routes, storage characteristics: content layer (F-HW-02 objects, DOC-001–
003, Forms 3/4/10), correctly unmodeled in predicates.

## 12. Applicability vs Content Boundary

| Question | Layer | Status |
|---|---|---|
| Authorisation required? | R-018 / R-096 predicates | ACTIVE, verified |
| Which streams / Schedule-I entry? | F-HW-02 + MPCB/consultant (UNK-014) | content, unmodeled |
| Which documents/tests? | DOC-001/002/003, Forms 1–4/10 | document layer, loaded |
| Authority / stage / validity? | AUT-003 / PRE_OPERATION / as-granted | static display |
| Renewal? | as-granted (no renewal rule encoded) | correctly absent |

No content requirement is encoded as applicability; no document gates a
verdict; entry numbers are never inferred (register note + code omission
both verified).

## 13. Source Quality and Version Control

- SRC-013 T1 OFFICIAL_PRIMARY 2016-04-04 (in 22-source corpus): proves
  definitions, Sch I/II tests, Form duties; not amendments, not per-unit
  mapping. Currency caveat recorded, verdict-safe (see §10).
- SRC-120 T2 CENTRAL_RULES DPCC copy (in corpus): proves Sch II limits;
  not amendments, not per-waste exceedance. Acceptable as limit reference
  because the engine consumes lab conclusions, not raw measurements; a
  primary MoEFCC consolidated text remains the closure item — recorded,
  not blocking.
- No mirror-as-determinism issue (contrast R-014/T4): the determinism-
  critical facts here are occupier-supplied inputs, not table lookups.
- No browsing performed; REPOSITORY EVIDENCE only. No EXTERNAL
  VERIFICATION section required (no external claims made).

## 14. Active Rule Safety Assessment

Falsification matrix (all executed against live rules): known generation,
denied generation, unknown/missing flag, known characteristic (all 11
tokens), clean results, empty list, missing/None/scalar-UNKNOWN lab data,
unlisted waste without lab data, mixed lists, contradiction both ways,
pre-window dates. One genuine corner defect found and fixed (see §15);
everything else held. No missing-fact, missing-source, predicate, lifecycle,
authority, or classification defect. Determination: the pair is safe as
implemented within the documented bounds.

## 15. Fail-Closed / UNKNOWN Behavior

- R-018: TRUE→APPLIES / FALSE→DNA / None+missing→INSUFFICIENT (ET-054).
- R-096: positive→APPLIES / clean→DNA / empty→DNA (supply discipline:
  untested waste must be missing/UNKNOWN, ET-129) / None+missing+scalar-
  UNKNOWN→INSUFFICIENT.
- **Found and fixed**: list-embedded `["UNKNOWN"]` evaluated FALSE,
  contradicting the register ("never coerced to FALSE") and the
  evaluator's own docstring. Surgical fix in `_evaluate_leaf` (`in`
  branch): established overlap still TRUE (fail-safe); pure-unknown-
  no-match now INSUFFICIENT (fail-closed); all other paths byte-identical
  (verified matrix). Blast radius: R-096 is the sole active list-`in`
  rule; full suite green with zero other changes.
- Approval level (`summarize_by_approval`, APPLIES > DNA > CONDITIONAL >
  INSUFFICIENT_DATA): both-missing→INSUFFICIENT; FALSE+missing→DNA (sound:
  no generation ⇒ no authorisation); contradiction→APPLIES (fail-safe);
  unknown-generation+empty-lab→DNA via recorded negative (supply
  discipline documented).

## 16. Dependency Propagation

DEP-009 (CTE/CTO→APR-010, HOWM r.6, loaded pair): APR-010 APPLIES with
unknown unobtained consent → BLOCKED on both (re-proven); INSUFFICIENT own
verdict → PENDING_EVALUATION (never READY); obtained + applies-state
prereqs → READY; obtained does NOT cure unknown prereqs (fail-closed,
tested). Unknown HW need can never become satisfied via another approval's
readiness. Orchestration/document layers preserve the split (docs gate
readiness, never verdicts).

## 17. Implementation Classification

- R-018: **A** — safe as currently implemented.
- R-096: **B** — safe with bounded limitations (UNK-034 currency outside
  decision path; [] supply discipline; lab-conclusion token discipline).
- Both stay ACTIVE. No deferral, no split, no deactivation.

## 18. Required Evidence Closure

1. MoEFCC consolidated HOWM text (closes UNK-034; refresh hw_streams +
   re-confirm SRC-120).
2. MPCB/consultant per-stream mapping path for F-HW-02 (closes UNK-014;
   content layer, not predicates).
3. Supplier contract for F-HW-04: missing/UNKNOWN when untested, never []
   (documents the §15 boundary).
4. No engine work required beyond the shipped UNKNOWN fix; list-aware
   UNKNOWN handling is now covered by pins.

## 19. Recommended Next Audit

Boiler lifecycle chain (R-028 active definition + R-086/R-087 registration
+ R-073 operation): definition/registration/operation split across three
active rules sharing F-BLR facts — the same trigger-vs-content-vs-lifecycle
separation tested here, plus the DEP-015 UNKNOWN-activity edge and the
PORTAL_LEGACY service citations (CON-004/CON-028). DEFAULT_JURISDICTION
stays IN-GJ; no table digitization without a demo-driven need.

## 20. Test Results

- New: `test_mh_hazardous_waste_authorization_chain.py`, **63 tests**,
  all passing (identity incl. CSV reads, chain reconstruction, R-018/R-096
  safety incl. effective windows, per-stream ANY, approval-level matrix,
  dependency propagation incl. obtained-does-not-cure-unknown,
  documents-as-content, fact discipline incl. consent-chain untouched,
  isolation, classification).
- Full backend suite: **1980 passed** (1881 baseline + 63 new + 36 parallel
  EC-core), 0 failed. Ruff clean. Frontend `tsc --noEmit` clean.
- One input-correctness fix in prior consent test (lowercase engine
  contract values; same BLOCKED conclusion, now genuinely exercised).

## 21. Files Changed

- `backend/app/rules/applicability.py` — list-embedded UNKNOWN fails
  closed in `in` branch (surgical fix + contract-docstring already
  promised it).
- `backend/tests/test_mh_hazardous_waste_authorization_chain.py` — new.
- `backend/tests/test_mh_consent_category_chain.py` — engine-contract
  input case (no conclusion change).
- `audit_mh_hazardous_waste_authorization_chain.md` — new (this file).

## 22. Final Determination

**Can the current system safely determine HW Authorization applicability
and the relevant per-stream Schedule-I content from current evidence and
engine semantics?**

Applicability: **YES** — R-018 (generation flag, T1) and R-096 (lab
characteristics, T2) are independent, bounded, fail-closed triggers whose
combination priority is fail-safe in all nine tested scenarios; the single
corner defect found (list-embedded UNKNOWN → FALSE) is fixed and pinned.

Per-stream Schedule-I content: **NO — and correctly not attempted.** Entry
mapping needs MPCB/consultant determination (UNK-014) against a reference
table whose post-2016 currency is open (UNK-034); the system carries
streams as supplied content (F-HW-02), never infers entries, and gates
readiness on CTE/CTO without inventing them. Earliest failure point for
content automation is the absence of a versioned, digitized Schedule-I
dataset — which must arrive as evidence, not as code constants.
