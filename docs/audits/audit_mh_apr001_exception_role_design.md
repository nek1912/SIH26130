# P0 APR-001 Exception/Exemption Semantic Design Audit

DESIGN-ONLY. No production code, facts, rules, schemas, APIs, frontend,
migrations, or test behavior modified in this task. Baseline verified from
the repository at audit time: MH active 26, MH deferred 61, MH
confirmation-gated 26, MH facts 128, GJ active 19, DEFAULT_JURISDICTION
IN-GJ. R-054 stays deferred; R-021 and all prior closures intact.

A parallel session drafted `audit_mh_apr001_exception_role_design.md` at
the tree root; this document is an independent verification written from
direct inspection of the model, evaluator, aggregation, orchestration,
registers, and tests. Findings converge where evidence supports the same
conclusion; every claim below was re-derived from the repository, with
exact file/line/test/register citations.

## 1. Executive finding

`ApprovalRule` has exactly one polarity: any rule evaluating TRUE is
aggregated by `summarize_by_approval` (priority APPLIES > DOES_NOT_APPLY >
CONDITIONAL > INSUFFICIENT_DATA, `backend/app/rules/applicability.py:570`)
into "approval applies", and `orchestration/service.py:_determine_status`
(`service.py:238`, applied at `:510`) turns applies-with-clear-deps/docs
into READY — which `handoff/service.py:prepare_initiation` accepts as the
sole gate for real-world external handoff. The model cannot say "an
exemption holds". Consequences, each verified against live code/tests:

- exemption TRUE alone → `applies` (R-002 small-unit, R-030 Class-B,
  R-043 MSE, R-044 domestic, R-087 deemed-registered — all live, all pinned
  by `test_mh_pack.py` TRUE→`applies` assertions);
- exemption FALSE alone → `does_not_apply` (a large chemical unit reads as
  "EC does not apply": fail-OPEN false negative);
- trigger TRUE + exemption TRUE → `applies` via first match (the exemption
  is invisible; R-054's Form-I else-branch would be erased);
- trigger TRUE + exemption UNKNOWN → `applies` (an unknown defeater is
  silently ignored).

The minimum contract that closes this without an LLM and without breaking
the 26 active MH + 19 GJ rules: label every rule TRIGGER (default),
EXEMPTION, or CLASSIFICATION; evaluate each with the unchanged three-valued
engine; compose per approval with an explicit approval function in which
EXEMPTION/CLASSIFICATION outputs can never produce APPLIES, EXEMPTION TRUE
plus TRIGGER TRUE yields reasoned DOES_NOT_APPLY (the sole sanctioned
TRUE→negative path), and EXEMPTION UNKNOWN plus TRIGGER TRUE yields
CONDITIONAL. GUARD/ROUTING/LIFECYCLE/WORKFLOW stay outside the engine, as
prior audits already hold them.

## 2. Existing semantic model

- `ApprovalRule` (`backend/app/rules/models.py:405`): id, approval_id,
  `applicability_conditions: list[ConditionNode]`, source_refs, version,
  effective window. No role, polarity, or consequence field.
- `ConditionNode`: leaf (`field/op/value`, ops exactly
  eq/in/gte/lte/gt/lt) + AND/OR/NOT + `LiteralNode("unknown" |
  "not_applicable")`. No lookup, aggregation, EXISTS, rule-reference,
  routing, or temporal operators (asserted exact by consent-chain tests).
- `_evaluate_leaf` / `_evaluate_node` (`applicability.py:64-230`):
  three-valued (True/False/None) with NOT_APPLICABLE sentinel; None/"UNKNOWN"
  never coerce to FALSE (plus the HW-chain fix: list-embedded "UNKNOWN"
  with no match now yields None instead of FALSE).
- `evaluate_rule` (`applicability.py:~300-490`): effective-window pre-check,
  per-tree evaluation, any-TRUE→APPLIES; all-FALSE→DOES_NOT_APPLY;
  INSUFFICIENT-mixed→CONDITIONAL/INSUFFICIENT_DATA; explicit-NA handling.
- `evaluate_approval_applicability` (`applicability.py:499`): one
  evaluation per rule, no cross-rule interaction.
- `summarize_by_approval` (`applicability.py:555`): groups by approval_id,
  returns first APPLIES else first DOES_NOT_APPLY else CONDITIONAL else
  INSUFFICIENT_DATA. This is the single polarity assumption in the
  pipeline: every rule's TRUE means the same thing.
- `LiteralNode("not_applicable")` machinery exists (`models.py:209-230`,
  evaluator lines 22-24, 159-230, 380-478) but **zero MH builders use it**
  (verified by search): the explicit-NA channel is dead code for MH, so it
  cannot currently express exemptions either.
- Dependency engine (`dependency_engine.py:277-305`, verified by reading):
  prerequisite satisfied iff `does_not_apply` or (`applies`/missing AND in
  obtained); `conditional`/`insufficient_data`/anything else blocks — and
  obtained cures only applies-state prereqs (proven by HW-chain tests).
  Lowercase result-value contract (`applies`, `insufficient_data`, …);
  uppercase input falls into the blocking branch.

## 3. Current failure mode

Data path, traced end to end:

1. rule definition — no role field; an exemption predicate and a trigger
   predicate are indistinguishable data;
2. evaluator — computes leaf truth faithfully; verdict strings
   (`applies`, …) are approval-shaped regardless of what was evaluated;
3. aggregation — `summarize_by_approval` APPLIES-first priority collapses
   facet TRUE into approval TRUE;
4. approval composition — none exists; R-003-style `CAT_BASE` composition
   lives only in deferred register text;
5. orchestration — `_determine_status` maps applies+clear to READY;
6. persistence — `ApprovalOrchestration` stores status +
   `applicability_result` + explanation; no role/provenance of *which kind*
   of rule produced the verdict;
7. presentation — frontend renders backend verdict strings generically
   (`OrchestrationPanel`, `HandoffPanel` "no longer READY" history note);
   no semantic logic lives there, so the loss is upstream, not in the UI.

Loss points: (1) definition and (3) aggregation. The evaluator is
faithful; orchestration/persistence/presentation propagate the collapsed
meaning correctly — which is exactly why the defect reaches READY and the
handoff gate.

## 4. R-002/APR-001 reconstruction

Register (`rule_register_v5.csv`, re-read): R-001 `EC_5F_REQUIRED :=
F-PRD-01 == TRUE AND F-PRD-03 IN {SYNTHESIS,MIXED}` (the trigger, deferred
on FORMULATION_ONLY non-falsing); R-002 `SMALL_UNIT := water<25 AND
fuel<25 AND NOT MAH` (EIA 5(f) col 5 — a classification facet feeding
R-003's `CAT_BASE := 'A' unless notified/small → 'B'`); R-003 category
composer (deferred, needs R-002 composition); R-004 GC escalator (deferred,
needs R-003 + existential F-LOC-07); R-005 estate gate (confirmation,
register warns "do not auto-exempt"); R-064 scope-truncated + UNK-033
(deferred); R-074 combination guard (UNKNOWN-listed). Only R-002 is live,
as APR-001's sole trigger.

Facets: R-002 = CLASSIFICATION (small-unit input to category
determination; small units still need EC via Cat B — it is not an exception
to EC itself). R-001 = TRIGGER (deferred). R-003 = composer (deferred).
R-004 = authority escalator (deferred). R-005 = scope gate (confirmation).
R-064/R-074 = scope/combination guards (outside rule_ids).

Polarity problem, stated exactly: the source's "does not require prior EC
[at Category A]" (small-unit → Cat B appraisal) must never become
approval DOES_NOT_APPLY — Cat B still requires EC. Under the current
model, R-002 TRUE yields approval APPLIES (wrong: smallness presented as
the EC trigger) and a naive negation encoding would yield DOES_NOT_APPLY
(wrong: EC still required). With trigger (R-001) UNKNOWN + small TRUE, the
only honest verdict is INSUFFICIENT_DATA. The design must also not turn
"small" into "EC does not apply" (naive EXEMPTION assignment) — the reason
CLASSIFICATION is a separate role from EXEMPTION (see §6).

## 5. R-054 reconstruction

`EC_EXPANSION_EXEMPT` := 6-AND (expansion; item∈{2,3,4,5}; no load
increase; Appendix-XIII certificate PARIVESH+SPCB; OCMS≥95%; no B2→A/B1
change); else Form I under 7(ii)(a) (register + ET-067/068/069, verified).
Desired role: EXEMPTION — TRUE relieves the fresh-EC duty **and** routes to
the exemption consequence (certificate already filed, by construction);
FALSE = no information (not "duty attaches"); UNKNOWN blocks APPLIES, never
ignored; the else-branch is a routing outcome (Form I), never
DOES_NOT_APPLY. Preserved invariants: EXEMPTION TRUE ≠ APPROVAL APPLIES
(the duty was never established by this rule); EXEMPTION FALSE ≠ APPROVAL
DOES_NOT_APPLY (contrast with current engine behavior); EXEMPTION UNKNOWN
≠ EXEMPTION FALSE. Only an explicit, typed composition with a TRIGGER may
convert defeat into DOES_NOT_APPLY-with-reason.

## 6. Semantic-role analysis

Minimum sufficient set: TRIGGER, EXEMPTION, CLASSIFICATION. Each role:

- TRIGGER (default): purpose — duty/approval attaches. Input: three-valued
  leaf truth. Output: APPLIES / DOES_NOT_APPLY / CONDITIONAL /
  INSUFFICIENT_DATA, alone decisive under current priority. Affects
  applicability (yes, directly), routing (no), dependencies (verdict feeds
  readiness), composition (as trigger limb), UNKNOWN (yes),
  persistence (yes, current shapes). Home for all current pure triggers
  (R-007/009/011/012/018/026/028/046/056/067/070/073/077-with-note/083/084/
  086/089/093/094/096 — verified trigger-shaped).
- EXEMPTION (duty-defeat): purpose — negate a matched duty with reason.
  Input: three-valued. Output: defeat + reason / no-information / unknown.
  Affects applicability only via explicit composition (never alone);
  routing no (Form-I consequence recorded as reason/provenance, not a
  selector); dependencies no (defeat ≠ grant — DEP-009-style edges still
  require obtained); composition yes as defeater limb; UNKNOWN yes;
  persistence yes (reason channel). Home for R-030/R-043/R-044/R-087 and
  the R-054 class.
- CLASSIFICATION: purpose — category input value. Input: three-valued.
  Output: informational value, never directly approval-decisive; consumed
  only by named composition (R-003 pattern); unconsumed → approval
  INSUFFICIENT_DATA if no trigger verdict exists, else invisible with
  provenance retained. Composition yes as input limb; routing/dependencies
  no; UNKNOWN yes; persistence yes (provenance). Home for R-002.
  Merging into EXEMPTION rejected: small-unit TRUE must not negate EC.

Excluded (stay outside; current posture correct): GUARD (R-015/R-074 —
verdicts *about* the decision), ROUTING (R-023/047/078/080 — string
selectors, not truth-apt), LIFECYCLE (R-062/063/075/099/CMP-007 —
validity/renewal state machines), WORKFLOW (R-081 — case-state
consequences). R-045 (deferred: "cross-rule exemption refs (R-043/R-044)
plus OE block; needs rule composition") independently confirms composition
— not roles alone — is the missing link. CMP-duty rules (R-070/093/094)
are plain threshold triggers on CMP approvals (verified live shapes);
no DUTY role in phase 1. Fewer than three roles fails: two roles force
either R-002-as-EXEMPTION (negates Cat-B EC — wrong) or R-054-as-TRIGGER
(current defect).

## 7. Truth tables

Three-valued throughout (T/F/U); no fourth value required — CONDITIONAL
and INSUFFICIENT_DATA are approval-level presentations of U with/without a
decisive trigger, already in the model.

Per-role: TRIGGER T→attaches / F→not-met / U→unknown. EXEMPTION T→defeats
(with reason) / F→no-information / U→unknown. CLASSIFICATION T/F→input
value / U→unknown. GUARD/ROUTING/LIFECYCLE/WORKFLOW: not truth-apt inputs
(excluded).

Composition (approval function over limb sets; no rule-to-rule
composition):

| # | TRIGGER | EXEMPTION | Approval verdict (safe) |
|---|---|---|---|
| 1 | T | — | APPLIES (duty attaches) |
| 2 | F | — | DOES_NOT_APPLY (trigger unmet) |
| 3 | U | — | INSUFFICIENT_DATA |
| 4 | — | T | trigger result only, never APPLIES (nothing to defeat) |
| 5 | — | F | trigger result only (no info; never DNA-by-exemption) |
| 6 | — | U | INSUFFICIENT_DATA |
| 7 | T | T | DOES_NOT_APPLY **with exemption reason** (sole sanctioned TRUE→negative) |
| 8 | T | F | APPLIES (no defeat) |
| 9 | T | U | CONDITIONAL (unknown defeater blocks APPLIES — anti-fail-OPEN) |
| 10 | F | T | trigger result (F); exemption recorded, nothing defeated |
| 11 | U | T | INSUFFICIENT_DATA (defeat needs a duty; provenance retained) |
| 12 | U | F | INSUFFICIENT_DATA |
| 13 | U | U | INSUFFICIENT_DATA |
| 14 | T(R-001 U→U) | small T (R-002) | INSUFFICIENT_DATA (never APPLIES) |
| 15 | T | R-054-shape T | exemption consequence recorded (Form-I else preserved); never APPROVAL APPLIES |
| 16 | T | R-054-shape U | CONDITIONAL (blocks APPLIES) |

Rows 9 and 12 are the defect killers: current engine returns APPLIES on
rows 9/12-equivalents (trigger TRUE alone decisive, exemption invisible).

## 8. Polarity analysis

Repository sweep (`app/`, exemption/exception/unless/provided/Form-I/
NOT_APPLICABLE): genuine approval applicability (all TRIGGER rules — no
exemption language in live predicates); explicit NOT_APPLICABLE (LiteralNode
mechanism exists, **zero MH builders use it** — dead channel, not a defect
but unavailable as an exemption vehicle); exemptions-live-as-triggers
(R-002/R-030/R-043/R-044/R-087 + pins in `test_mh_pack.py`
`test_r043_mse_exemption` / `test_r044_domestic_exemption` /
`test_r030_class_b_boundaries` / R-002 TRUE→`applies` — the inversion is
test-pinned, hence migration-visible); composition-shaped deferrals
(R-003/R-004/R-045/R-013/R-014/R-017/R-042/R-081/R-099 reasons all cite
rule-reference needs); routing/lifecycle/workflow vocabulary confined to
deferred reasons, docs, and display strings (no live predicate). False
positives separated: "exemption" in builder comments (R-030/R-043/R-044
comments describe register predicates — accurate prose, defective role),
"unless" in API/handoff comments (ordinary code prose), "exemption" in
seed/evidence text ( evidentiary discussion, not verdicts), incentives
"electricity duty exemption" (eligibility engine, separate relevance
states, never approval verdicts). Legal transformations requiring explicit
typed composition: rows 7, 9, 11 of §7. Illegal without composition:
TRUE→DOES_NOT_APPLY, FALSE→APPLIES, UNKNOWN→FALSE, UNKNOWN→
DOES_NOT_APPLY, exemption TRUE→approval FALSE-by-silence, exemption
FALSE→approval TRUE, exemption TRUE→READY, CLASSIFICATION→APPLIES.

## 9. UNKNOWN semantics

Missing facts → INSUFFICIENT_DATA preserved at every layer: leaf None/
"UNKNOWN" (plus list-embedded UNKNOWN with no match, per HW-chain fix);
rule-level U propagation through AND/OR/NOT (existing, tested); approval
rows 3/6/11–13; composition row 9 CONDITIONAL (unknown defeater) — an
exemption that is unknown can never become an implicit exemption (rows
9/12) nor an implicit denial (row 11 → INSUFFICIENT, not DNA). Conceptual
exemption-unknown cases: R-054-shape U + trigger T → CONDITIONAL with
"exemption evidence missing" reason; R-002 U + R-001 U → INSUFFICIENT_DATA
with classification provenance; unlisted-sector exemption query → the
exemption rule itself yields U → composition row 6/13.

## 10. Downstream readiness contract

Minimum contract (no orchestration rewrite): an approval node is created
from the approval verdict as today; it is BLOCKED on deps/docs/evidence
gaps as today; an alternate route (Form I) is created only as recorded
exemption-consequence provenance, never as a second approval node, until a
routing layer exists; INSUFFICIENT_DATA whenever no trigger verdict exists
or an unknown defeater/classification is in play (rows 3/6/9/11–13);
an exemption may suppress an approval node to DOES_NOT_APPLY **only** via
the typed row-7 transformation (TRIGGER T + EXEMPTION T + cited reason);
a guard never becomes a node (R-015/R-074 stay out); routing metadata
(AUT-xxx strings, FIRE/BP_AUTHORITY) never enters verdicts. Defeat ≠
grant: DEP-009-style edges still require obtained_approvals (verified
engine semantics: obtained cures only applies-state prereqs); exemption-
defeated DOES_NOT_APPLY must NOT satisfy downstream prerequisites
(requires an explicit obtained record). UNKNOWN defeaters hold READY via
CONDITIONAL. Current READY behavior for pure-trigger approvals is
byte-identical under this contract.

## 11. Design options

OPTION A — role field + approval composition: add optional
`role: TRIGGER (default) | EXEMPTION | CLASSIFICATION` to `ApprovalRule`
plus optional per-approval `composition` (trigger/exemption/
classification id lists + consumer, initially only APR-001's R-003
pattern). `evaluate_rule` unchanged; `summarize_by_approval` becomes
role-aware (single production consumer besides tests:
`orchestration/service.py:420,598`); defeat reason travels in the existing
reason channel. Migration is data (labels + composition + re-pinned rule
tests + composition tests); no engine-operator changes.

OPTION B — facet layer + outcome mapping: keep `ApprovalRule`
trigger-only; move exception/exemption/classification predicates to a
parallel facet registry evaluated by the same three-valued engine, with a
per-approval mapping (TRIGGER × facets → verdict implementing §7).
Facets cannot leak into aggregation by construction (separate types).
Costs: second registry + loader + pack dimension + mapping DSL; mapping
rows need audit rigor equal to roles; two registries can drift.

Factual tradeoffs (no ranking): correctness equivalent given §7;
complexity lower in A (one model + one aggregator) vs new layer in B;
compatibility — A defaults safe (unmigrated rules behave today) but needs
a lint enforcing explicit roles on new rules (default-TRIGGER is fail-OPEN
by default for future exemption-shaped rules); B safe by construction but
needs the same lint plus cross-registry review; auditability — A keeps one
rule list with visible labels, B splits the trail; traceability — A reuses
the reason channel, B needs a parallel channel; test burden equivalent
(§7 rows + re-pins + GJ green both ways); failure modes — A: omitted role,
stale composition ids; B: facet/trigger misplacement, mapping drift, loader
divergence. Minimum decision before implementation: **choose the home of
role information (field on ApprovalRule vs separate registry) and freeze
§7 as the acceptance table** — everything else follows.

## 12. Backward compatibility

Unchanged under either option with default behavior: R-007/009/011/012/
018/026/028/046/056/067/070/073/077(with note)/083/084/086/089/093/094/096
as TRIGGER (pins stand); R-035 branch guard TRIGGER-compatible for
branch-record APR-029. Deliberate, re-pinned migrations only: R-002 →
CLASSIFICATION (APR-001 with R-001 still deferred becomes honest
INSUFFICIENT_DATA — the defect fix), R-030/R-043/R-044/R-087 → EXEMPTION
(TRUE→reasoned DOES_NOT_APPLY; UNKNOWN→CONDITIONAL), R-077 → split TRIGGER
+ EXEMPTION limbs or explicitly grandfathered collapse with a test pin
(its OE+LARGE non-grantability is trigger-with-defeater in one predicate;
no silent third option). R-001/R-003/R-004/R-005 stay deferred on evidence;
R-064/R-074/R-075 stay outside rule_ids. GJ: 19 rules verified
trigger-shaped by spot check (`industry_type` eq, effluent ANDs); default
preserves byte-identity with the full GJ suite as proof gate. No migration
without moving the corresponding pinned expectations explicitly.

## 13. Migration strategy

1. Model: optional role (A) or facet registry (B); defaults = current
   behavior; no rule touched. 2. Register: labels beside predicates in
   `seed/mh/approvals.py` (A) or facet rows + mapping (B); no CSV format
   change required either way (code-side data first). 3. Engine:
   role-aware aggregation (A) or mapping evaluator (B); leaf/AND/OR/NOT
   untouched. 4. Pack: serve composition/mapping via
   `load_regulatory_pack` (no second source of truth). 5. Order: one
   isolated facet first (R-043 MSE exemption — single approval APR-043,
   clean pins) → regression → APR-001 (R-002 → CLASSIFICATION; verdict
   becomes INSUFFICIENT_DATA) → readiness verify (DEP-009 BLOCKED
   preserved) → R-030/R-044/R-087 with fresh pins → R-077 split decision
   last. 6. Tests: §7 rows as tests first (TDD); GJ + MH green each step.
   7. Regression: unmigrated approvals byte-identical. 8. Reports: EC +
   R-054 audits record outcomes; inventory counts unchanged (no rules
   added/removed).

## 14. Test specification

(Not implemented in this task.) Unit: per-role verdict shapes (TRIGGER
T/F/U; EXEMPTION T=defeat+reason/F=no-info/U=unknown; CLASSIFICATION
informational). Truth-table: §7 rows 1–16 as executable cases. Aggregation:
multi-rule same-approval priority with roles (exemption TRUE never first;
CLASSIFICATION never decisive). Polarity: each §8 illegal transformation
asserted absent (probe-style, as the R-054 probe proved fail-OPEN).
UNKNOWN propagation: rows 3/6/9/11–13 + list-embedded UNKNOWN (existing
pin) + missing-field matrix. Composition: R-003-pattern consumer with
R-001 absent → INSUFFICIENT_DATA; defeat→reasoned DNA; unknown defeater→
CONDITIONAL. Routing preservation: Form-I consequence recorded, never a
second node; AUT-xxx strings never in verdicts. Backward compat: all
current TRIGGER pins green unmoved; GJ suite green. Regression proving no
return: R-054-shape probe asserting never-APPLIES; R-002-small asserting
never-APPLIES and never-DNA.

## 15. Minimum semantic contract

The smallest domain-model/evaluation change preventing exemption/exception
TRUE from being mistaken for approval applicability, preserving three-
valued fail-closed semantics: (i) every rule carries an explicit audited
role from {TRIGGER, EXEMPTION, CLASSIFICATION}, TRIGGER default only with
a lint requiring explicit labels on new rules; (ii) EXEMPTION/
CLASSIFICATION outputs can never produce APPLIES, alone or combined;
(iii) EXEMPTION TRUE + TRIGGER TRUE → DOES_NOT_APPLY carrying the
exemption reason — the sole permitted TRUE→negative path; (iv) EXEMPTION
UNKNOWN + TRIGGER TRUE → CONDITIONAL, never APPLIES; (v) CLASSIFICATION
consumed only by named composition, otherwise informational;
(vi) GUARD/ROUTING/LIFECYCLE/WORKFLOW stay outside applicability;
(vii) defeat never counts as grant downstream (READY only via trigger
path); (viii) UNKNOWN never becomes FALSE at any layer. Either option
satisfies the contract by implementing (i)–(viii) verbatim with the §14
table green before migration begins.

## 16. Explicit non-goals

No engine-operator changes; no lookup/aggregation/EXISTS/composition
primitives for the deferred chains (R-003/R-004/R-013/R-014/R-017/R-042);
no GIS; no LLM anywhere in the decision path; no new facts; no R-054 or
APR-001-exception activation (both stay deferred on evidence); no GJ
changes; no CSV format changes; no orchestration rewrite; no terminal
EXEMPT status (reason channel suffices for phase 1); no DUTY role for
CMP rules.

## 17. Open decisions

1. Informational surfacing of CLASSIFICATION outputs during
   INSUFFICIENT_DATA (recommended yes). 2. Terminal vocabulary:
   DOES_NOT_APPLY+reason vs dedicated EXEMPT status (deferred; reason
   channel suffices). 3. R-077 split-now vs grandfather-with-pin (needs
   mini-audit). 4. Lint vs review enforcement of explicit roles. 5. Future
   DUTY role for CMP rules (out of phase 1). 6. Option A vs B selection
   (the minimum decision, §11).

## 18. Implementation prerequisites

Coding starts only when ALL hold: (a) option chosen + §7 frozen as
acceptance table; (b) §14 rows written as tests first; (c) default-
unchanged proof designed (full MH+GJ green with defaults); (d) migration
order agreed with audit owners of R-002/R-030/R-043/R-044/R-087 pins;
(e) orchestration READY-path review signed off (defeat ≠ grant);
(f) no evidence prerequisite — design lands with R-001/R-054 deferred.
