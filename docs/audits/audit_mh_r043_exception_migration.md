# Audit — R-043 EXEMPTION Migration (First Production Pilot)

Controlled migration audit of R-043 (CGWA MSE exemption, APR-043) after the
P0 exception-semantics implementation. R-002/CLASSIFICATION,
R-030/R-044/R-087/R-035/R-077, R-054, R-001/R-064/R-074, facts, and evidence
are untouched by this audit (verified). No redesign of the contract.

## 1. Baseline

- Verified before auditing: DEFAULT_JURISDICTION IN-GJ; MH active 26;
  MH deferred 61; MH confirmation 26; MH facts 128; GJ active 19;
  R-043 role EXEMPTION; R-002 active CLASSIFICATION; R-054/R-001/R-064
  deferred; full backend 2225 passed.
- After: all counts identical; suite **2228 passed** (2225 + 3 new
  dependency-footprint tests), 0 failed; ruff clean; frontend untouched
  (no tsc needed — no UI/API-shape change).
- Pre-existing + parallel uncommitted work preserved; required fallout of
  this audit only: 3 added tests, this document, two one-line status
  entries.

## 2. R-043 identity

`rule_register_v5.csv` + `rules.csv` (re-verified, matching the
implementation record): R-043, "CGWA NOC - groundwater abstraction",
APR-043 (NOC, ACTIVITY_DEPENDENT;LOCATION_DEPENDENT, PRE_ESTABLISHMENT/
PRE_CONSTRUCTION, trigger abstraction, precondition none), AUT-013,
CENTRAL, `GW_EXEMPT_MSE := F-INC-01 IN {MICRO,SMALL} AND F-WAT-05 < 10`
(threshold 10 m³/day strict lt; Medium explicitly NOT covered),
T1 SRC-052 Exemptions list, EXACT 2020-09-24, VERIFIED_CONDITIONAL /
IMPLEMENTATION_SAFE, no dependencies, DOC-012, SLA-031 LEGAL. Live code:
`role=EXEMPTION` explicit argument; facts/refs/effective identical to the
pre-migration builder (rule-level pins stand unmodified). Role is genuinely
EXEMPTION, not nominal: the predicate relieves the NOC duty for the
matched scope, and the register itself phrases the duty as
NOC-required-unless-exempt (DEP-022, condition "Not exempt" — that edge
targets an activity and stays triaged out, corroborating rather than
executing the role).

## 3. Regulatory semantics

From stored evidence (no general-knowledge substitution): TRUE =
micro/small abstracting <10 m³/day holds the exemption (duty defeated for
this limb); FALSE = no exemption information (duty posture unchanged —
large abstractors, Medium enterprises, ≥10 volumes are simply not covered
by this limb); UNKNOWN (missing class or volume) = unresolved defeater
that must block an applicable trigger. TRUE defeats only an established
duty; FALSE never means "duty remains" as a verdict, only absence of
relief; no routing consequence (AUT-013 static); no procedural consequence
encoded (DOC-012/SLA-031 stay in document/display layers). Anything the
T1 exemptions list does not establish is marked accordingly; Medium
exclusion is explicit in the register notes.

## 4. Engine semantics

Path traced live: predicate → EXEMPTION role → `summarize_by_approval`
(APR-043 record: triggers R-044/R-077) → `compose_approval_evaluations` →
approval verdict → `_determine_status` → orchestration → handoff gate. No
legacy APPLIES-first path can consume R-043: both production summarize
sites route composed approvals to composition; the only other
`summarize_by_approval` callers are tests. Verified matrix on live pack
rules (A–H): TRUE-alone→INSUFFICIENT; FALSE-alone→INSUFFICIENT;
TRUE+trigger→DOES_NOT_APPLY+"Exempt under R-043"; FALSE+trigger→APPLIES;
UNKNOWN+trigger→CONDITIONAL; UNKNOWN+TRUE→INSUFFICIENT; all-UNKNOWN→
INSUFFICIENT. No row yields APPLIES from exemption, DNA from exemption
alone, or vanished UNKNOWN.

## 5. Truth-table verification

Covered by the implementation suite (19 rows) plus audit probes above;
reason preservation asserted (`Exempt under R-043` + limb reason; unknown
names the blocking rule). The B-pure isolation (LARGE only → R-043 FALSE,
siblings unknown → INSUFFICIENT, never DNA) and E-pure isolation (LARGE
domestic ≤5 → R-044 TRUE + R-043 FALSE → APPLIES) confirm FALSE carries no
verdict of its own.

## 6. Fail-open falsification

Old defects attempted live and dead in all paths: exemption TRUE→APPLIES
(impossible — composition has no such row; orchestration never sees it);
exemption FALSE→DOES_NOT_APPLY (impossible — FALSE contributes nothing);
trigger TRUE + exemption UNKNOWN→APPLIES (impossible — CONDITIONAL row).
Alternate-path sweep: production `summarize_by_approval` callers (2,
both composed); `evaluate_approval_applicability` direct consumers return
per-rule verdicts by design (raw/composed separation); obligations
endpoint client exists in frontend but is never called (verified — UI
renders composed orchestration verdicts + explanations only); what-if,
impact-rehearse, and handoff paths all forward compositions; GJ has no
records (all-TRIGGER, empty map). Migration classified SAFE on this axis.

## 7. Readiness/handoff audit

Live-path proofs: exemption-TRUE alone → INSUFFICIENT_DATA (not READY);
no completion masquerade (non-READY statuses only); UNKNOWN defeater
survives aggregation to non-READY; classification creates no node;
insufficient prereqs BLOCK (obtained cures only applies-state prereqs —
proves defeat can never read as grant, since obtained derives solely from
terminal workflow status `approved`, and exemption-defeated DNA is not an
obtained record); DEP-009 enforced; UNKNOWN never FALSE; handoff raises
pre-portal-lookup for every non-ready status (all five asserted). No
exemption result is persisted as obtained (structural: `_TERMINAL_STATUSES
== {"approved"}`, pinned by new test).

## 8. Fact/evidence integrity

Migration changed interpretation only: builder diff is the role argument
plus comments (rule-level pins green unmodified prove predicate/facts/
refs/dates identical); F-INC-01 (derived enum, strict) + F-WAT-05 (number,
strict) unchanged; no new facts (128), claims, thresholds, authorities,
dates, exemptions, or prerequisites; SRC-052 in corpus; DOC-012 still
deferred (evidence preserved, not loaded); SLA-031 display-only.

## 9. Backward compatibility

Spot families green (environmental, HW, MIDC, utility, pack, e2e,
derivations, orchestration, dependency, handoff: 331 tests) plus full suite
green. Per-rule verdicts untouched (R-044 TRUE→applies still holds at rule
level — raw/composed separation is intentional). GJ byte-identical (empty
compositions, all-TRIGGER, 19 rules). Legacy no-composition paths unchanged
where intended (tests calling summarize directly). Three deliberate
defect-fix re-pins from the implementation task stand (api_e2e APR-001,
derivation-wiring ×2 — rule-level APPLIES + provenance intact in each).

## 10. Test coverage

Implementation suite (56→59 tests) reviewed against the required list —
role identity, T/F/U, composition, reason, no-APPLIES, no-DNA,
UNKNOWN propagation, readiness, dependency, handoff, legacy isolation:
all present. Gaps found and closed in this audit: DEP-022 triage pin,
no-APR-043-edges pin, obtained-provenance pin (3 new tests). No redundant
tests added; no existing test weakened (re-pins are commented defect
fixes, rule-level assertions intact).

## 11. Safety classification

**SAFE_WITH_LIMITATION.** The migration itself is safe in all 8 matrix
positions, readiness, handoff, and evidence handling. The precise
limitation: sibling rule R-044 (domestic limb, exemption-shaped) remains
an unmigrated TRIGGER inside APR-043's composition, so domestic-only cases
still report APPLIES (duty overstated — fail-safe direction, but noisy and
legally imprecise). This is scoped future work (already listed as a
migration candidate), not a defect in R-043's migration; no additional
rule may be migrated on the back of this audit.

## 12. APR-001 migration gate

Gate criteria assessed: semantic correctness (proven rows 14–17
equivalents for R-002? — covered by implementation suite APR-001 tests:
small TRUE/FALSE alone → INSUFFICIENT, never APPLIES/DNA); fail-closed
(yes); readiness safety (INSUFFICIENT_DATA, not READY); regression safety
(full suite green; 1 deliberate re-pin standing); role plumbing (live in
pack composition); test coverage (dedicated APR-001 class); evidence
preservation (R-001 still deferred, no invention); legacy compatibility
(legacy paths green). **Gate: OPEN** — but this audit migrates nothing;
APR-001/R-002 migration, if undertaken, is a separate task owning its own
re-pins. R-002's current CLASSIFICATION state is production-safe as
audited (INSUFFICIENT_DATA verdicts, no READY).

## 13. Remaining limitations

R-044 domestic-limb inversion (fail-safe overstatement until migrated);
R-030/R-087/R-035/R-077 unmigrated (documented candidates); named-only
partitioning ignores unlisted rules of composed approvals (lint-enforced
completeness); CONDITIONAL-vs-INSUFFICIENT preservation refinement
(accepted, pinned); `evaluate_rule`-level TRUE→applies for migrated rules
is intentional raw/composed separation.

## 14. Exact next task

Migrate R-044 (domestic exemption) as EXEMPTION inside the existing APR-043
composition (no new composition record needed; triggers R-077 + exemption
pair R-043/R-044): re-pin domestic TRUE→APPLIES pack expectations to
reasoned DOES_NOT_APPLY, prove LARGE-domestic and MICRO-domestic rows,
re-run readiness + full suite. Estimated scope mirrors this audit. R-002/
APR-001 migration may proceed in parallel as a separate task per the gate
above. R-054 stays deferred; no facts/evidence work required for either.
