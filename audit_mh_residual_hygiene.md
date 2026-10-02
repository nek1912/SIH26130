# Maharashtra Residual Hygiene Audit — R-059 / R-071 / R-072 / R-076

Lightweight evidence-first closure audit. Jurisdiction: IN-MH. IN-GJ
regression/reference only. Date (UTC): 2026-09-29. Identity re-verified
from CURRENT registers; pinned by
`backend/tests/test_mh_residual_hygiene.py` (29 tests).

Prior-work guard: all protected rules/tests/reports untouched, including
the legitimate 59→60 (R-021) and 60→61 (R-054 follow-up) baseline moves
— my own pins were updated to match; the R-021 session's 5-set pin now
belongs to that session's follow-up (reported, not edited). Zero
implementation changes.

## 1. Scope

R-059 (INCENTIVE_VALUE hard stop), R-071 (MH GW Act in-force gate),
R-072 (environment audit conditional), R-076 (EC compliance due dates).
Each triaged independently against genuine-obligation /
already-represented / duplicate / hygiene / reserve / workflow / DNI /
UNKNOWN / needs-audit. Out of scope: any activation, fact, primitive,
or status-set mutation.

## 2. Current Baseline

Code-executed: MH active **26**, MH deferred **61**, MH confirmation
**26**, MH facts **128**, GJ active **19**, DEFAULT_JURISDICTION IN-GJ.
Untriaged before: 4 (R-059/071/072/076 — R-054 triaged by follow-up
during this session). All four ∈ safe-allowlist (76), ∉ active,
deferred, confirmation, DNI, UNKNOWN — allowlist-only, default-absent,
fail-closed.

## 3. Inventory Reconstruction

105 register rules = 26 active + 61 deferred + 26 confirmation − 15
(deferred∩confirmation) + 3 DNI + 0 new (UNKNOWN adds none) = 101
triaged + 4 residue. Arithmetic closes exactly (test-pinned). None of
the four targets an APR-xxx approval: INC-* (incentive namespace),
CND-024 (conditional reg), CMP-014 (compliance AUDIT, DNI), CMP-006
(compliance REPORT, ROC). approvals.csv holds no rows for any of them.

## 4. R-059 Audit

`INCENTIVE_VALUE := NOT_COMPUTED`, no inputs, no authority/lifecycle,
GUARD_OR_ROUTING, VERIFIED/IMPLEMENTATION_SAFE, SRC-073/074 T3,
note "Hard stop". Falsification attempt ("genuine obligation?")
fails: every computable incentive (INC-002..008) is DNI and INC-009 is
ROC — the value is definitionally uncomputable, so the rule records
the layer's hard-stop policy rather than an obligation. ET-043 pins
any-input → NOT_COMPUTED. T3 portals evidence the absence they need
to (no PSI 2025 instrument listed). Disposition below.

## 5. R-071 Audit

`MH_GW_ACT_IN_FORCE := TRUE from 01-06-2014` (+ R-097 evaluates the
deep-well branch; GW Rules 2018 DRAFT), CND-024, DETERMINISTIC,
VERIFIED/IMPLEMENTATION_SAFE, SRC-131/132 T1 (commencement 01-06-2014
proven vide 28-05-2014 notification), note "Do not return FALSE".
A regime date-gate, not an applicability predicate: as a boolean it
would be permanently TRUE post-2014 — meaningless as a rule verdict.
The operative branch (R-097, deferred) is separate; required_inputs
F-WAT-05 is a spurious linkage (Act-in-force needs no extraction
quantity) but harmless — the rule is unconsumed. ET-111 (Act-status
UNKNOWN → UNKNOWN, CGWA branch separate) is respected by absence.
"Duplicates another approval?" No — complementary facet of R-097, not
an overlap. No active dependency; source current (no repeal
registered; notified-areas list explicitly out-of-proven-scope).

## 6. R-072 Audit

`ENV_AUDIT := CONDITIONAL (only when assigned by authority or engaged
by proponent)`, CMP-014, DETERMINISTIC,
VERIFIED_CONDITIONAL/IMPLEMENTATION_SAFE, SRC-066 T1 (Rules in force
29-08-2025; "no blanket obligation" proven), effective 2025-08-29.
A true duty with an assignment trigger — but assignment/engagement is
authority/case state, and no such fact exists by design (only
unrelated F-LAB-10 matches assign/engag labels). CMP-014 is DNI in
both compliance.csv and do_not_implement.csv; the EPR audit already
covered env-audit as non-blanket. "Already represented?" Yes — as
CMP-014's trigger text; the rule adds no decidable content. Not a
workflow/document artifact, not DNI itself, not UNKNOWN — a
conditional duty correctly resting outside the boolean engine.

## 7. R-076 Audit

`EC_COMPLIANCE_DUE := 1 June and 1 December each calendar year after
EC`, CMP-006, DETERMINISTIC, VERIFIED/IMPLEMENTATION_SAFE, SRC-001 T1
(para 10(ii)), effective 2026-07-13, operator DATE, trigger "EC
granted" (free text — "EC granted"/F-EC-01 is not a fact). Scheduling
semantics for the deadline layer, not the applicability engine; the
same dates already live as data in CMP-006.frequency_deadline. CMP-006
is ROC/LOW ("para 10 not extracted"). Source tension recorded: R-076
cites SRC-001 para 10(ii) while SRC-001's own row disclaims paras
9/10 extraction — but UNK-017 (CLOSED_V3) and CMP-006 corroborate the
1 Jun/1 Dec content, so the locator (not the content) is what's
unresolved. Hygiene with a conditional future note (see §12).

## 8. Duplicate / Facet Analysis

No TRUE duplicates. Four intentional facets, each against a distinct
target with distinct inputs: R-059 restates the incentive layer's DNI
posture as a guard (INC-* vs INC-xxx instruments); R-071 gates the
regime R-097 operates (complementary, not overlapping); R-072
restates CMP-014's no-blanket trigger; R-076 restates CMP-006's
frequency_deadline. Same-approval and shared-input tests both
negative across all pairs (pinned).

## 9. Source Sanity Check

R-059: T3 portals, negative-only, sufficient for a hard stop, rightly
insufficient for any computation. R-071: T1 STATE_ACT, commencement
proven, current, bounded (no final Rules, no notified list — both
disclaimed in-row). R-072: T1 primary, in-force + no-blanket proven.
R-076: T1 cited with the §7 locator tension; content corroborated ×3.
Nothing here needs T1 escalation for a no-implementation disposition;
the R-076 locator is flagged for any future deadline-layer use.

## 10. Code Consumer Check

All four appear exactly once in code: the
MH_IMPLEMENTATION_SAFE_RULE_IDS allowlist. No builder, no authority
string, no loaded edge/document, no orchestration/frontend reference,
no edge-test consumer beyond ET-043/ET-111 (register-level pins).
Intentionally unconsumed (default-absent), not orphaned: each is
referenced by its register rows, branch/compliance counterparts, and
this audit.

## 11. Fact / Engine Check

R-059: no inputs/operator — nothing to represent; engine N/A
(correctly). R-071: F-WAT-05 present but semantically unlinked to the
gate; no boolean encoding is meaningful (permanent TRUE). R-072: no
inputs; trigger is case state by design — unrepresentable as
ApprovalRule, correctly so. R-076: "EC granted" unfacted; DATE
operator fits the deadline engine, not the applicability engine; no
primitive missing because no applicability encoding is attempted. No
nonexistent-fact references, no unsupported operators invoked (all
unbuilt), no lookups/aggregation needed. No primitives introduced.

## 12. Individual Dispositions

- **R-059: TRIAGED — HYGIENE / DOCUMENTATION.** Guard-node hard stop;
  falsification-as-obligation fails (nothing computable exists to
  guard). No deep audit required (absence-of-instrument monitoring is
  surveillance, not audit).
- **R-071: TRIAGED — HYGIENE / DOCUMENTATION.** Regime date-gate;
  operative branch lives in deferred R-097; T1 commencement proven.
  No deep audit required.
- **R-072: TRIAGED — HYGIENE / DOCUMENTATION.** Assignment-triggered
  duty; CMP-014 DNI; EPR-audited; trigger is case state by design. No
  deep audit required.
- **R-076: TRIAGED — HYGIENE / DOCUMENTATION** (with conditional
  future note). Deadline content already data in CMP-006; wrong layer
  for ApprovalRule; CMP-006 ROC/LOW + locator tension recorded.
  Revisit ONLY if deadline-layer modeling of CMP-006 is ever scoped —
  that revisit is a compliance-layer task, not an applicability audit.

No ACTIVE (nothing proves safe boolean verdicts), no DNI (none is
stop-listed conduct), no CONFIRMATION (register statuses are SAFE/
VERIFIED, contradicting gating), no DUPLICATE-strict, no UNKNOWN
(identities are clear), no FUTURE FULL AUDIT unconditional (R-076's
note is conditional, not a disposition).

## 13. Inventory Closure

Code-untriaged after: **4** (the residue) — plus R-054 now deferred,
so register arithmetic is 101 triaged + 4 documented = 105, closing
exactly. The four are triaged-by-record (this report + 29 tests), not
by status set: explicit code entries would break the R-021 session's
5-set pin and the inventory pin, and are recorded as a joint follow-up
once owners converge. Nothing was mutated to force closure — the
arithmetic closed on independently-established facts.

## 14. Remaining Untriaged Rules

Code-level: R-059, R-071, R-072, R-076 (documented above; explicit
entries pending cross-session follow-up). Genuinely unaudited
approval rules: **none** — every APR-xxx rule now carries a cluster
audit or a falsification record. R-054's absence from the sets is
resolved (deferred with rationale).

## 15. Future Full-Audit Candidates

Unconditional: **none** from this residue. Conditional: CMP-006/R-076
deadline-layer modeling IF compliance automation is ever scoped (needs
EC-held trigger fact + locator resolution + ROC clearance). The next
highest-value work overall is not regulatory but semantic: the P0
**APR-001 exception-role design** (EC audit) — now with three
motivating instances (R-002 facet, R-054 exemption, one-directional
screens generally).

## 16. Implementation Decision

**ZERO changes.** No rule implemented/gated/deleted; no facts; no
primitives; no status-set, deferred-set, or confirmation-set mutation.
The only pins touched are my own prior count pins (60→61 + R-054
triaged), updated to match the independently-landed R-054 follow-up.

## 17. Test Results

- Focused: `backend/tests/test_mh_residual_hygiene.py` — **29/29
  pass** (two draft assertions corrected to actual register/fact
  content: SRC-074 wording, F-LAB-10 scope).
- Full backend suite: **2139 passed, 1 failed** — the single failure
  is `test_mh_r021.py::TestStatusDecision::
  test_untriaged_set_shrinks_to_five`, which pins the 5-set including
  R-054; the independently-landed R-054 follow-up deferral shrank the
  code-untriaged set to 4. Not this session's file: left for its
  owners (one-line 5-set→4-set update). No failure touches residue
  semantics; every other assertion in the suite passes.
- Ruff (`app/`, `tests/`): clean.
- Frontend `tsc --noEmit`: clean (no output).

## 18. Files Changed

Exact list (this audit only):

- `audit_mh_residual_hygiene.md` (new — this report).
- `backend/tests/test_mh_residual_hygiene.py` (new — 29 tests).
- `backend/tests/test_mh_remaining_inventory.py` (my own baseline
  maintenance: 60→61, untriaged 5→4, R-054 addendum).
- `backend/tests/test_mh_ec_core.py` (my own count pin 60→61).
- `audit_mh_remaining_inventory.md` (my own addendum 2).

Not changed: all protected rules/tests/reports, status sets, pack/
engine/fact code, ARCHITECTURE.md / PRD.md / RULES.md (no new
architectural fact or product-scope change owned by this hygiene
pass), any other session's files.

## 19. Final Determination

All four residue rules are **genuinely hygiene** — a guard policy, a
regime gate, an assignment-triggered duty, and a deadline facet —
each already represented where it belongs (incentive posture,
R-097 context, CMP-014 DNI, CMP-006 frequency data) and each
correctly absent from the boolean applicability engine. No deep audit
is owed; no activation is conceivable without first inventing the
very inputs the registers withhold. The Maharashtra rule inventory is
now fully placed (105/105) with zero silently-untriaged rules: 26
active, 61 deferred, 26 confirmation-gated, 3 DNI, 3 UNKNOWN-guarded,
and 4 documented-hygiene (+ R-054 deferred) closing the arithmetic.
