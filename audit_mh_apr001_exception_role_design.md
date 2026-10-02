# P0 APR-001 Exception-Role Semantic Design

Architecture-level design audit. **No implementation in this session:**
no change to `applicability.py`, `models.py`, `ConditionNode`/`ApprovalRule`,
registers, active rules, R-002/R-054/APR-001, predicates, or production
behavior. Baseline: MH active 26, deferred 61, confirmation 26, facts 128,
GJ active 19, untriaged 4 (documented hygiene). DEFAULT_JURISDICTION IN-GJ.

## 1. Problem Statement

`ApprovalRule` has one polarity: any rule evaluating TRUE aggregates (via
`summarize_by_approval`, priority APPLIES > DOES_NOT_APPLY > CONDITIONAL >
INSUFFICIENT_DATA) to "approval applies". The model cannot say "an
exception/exemption holds". Proven consequences (temp probes, current
tree, zero repo impact):

- exemption TRUE alone → `applies` (R-002 small-unit, R-030 Class-B,
  R-043 MSE, R-044 domestic, R-087 deemed-registered all live thus);
- exemption FALSE alone → `does_not_apply` (large chemical unit →
  "EC does not apply": fail-OPEN false negative);
- trigger TRUE + exemption TRUE → `applies` via first match
  (exemption invisible; Form-I routing of R-054's else-branch erased);
- trigger TRUE + exemption UNKNOWN → `applies` (unknown invisible:
  exemption that would defeat is silently ignored).

FACET TRUE is therefore conflated with APPROVAL APPLICABLE at the only
aggregation point, which also feeds orchestration (`service.py:420,598`)
→ `_determine_status` → READY. An exemption TRUE can mark READY today.

## 2. Evidence Base

EC-core audit (R-001 trigger deferred on FORMULATION_ONLY; R-064 scope
truncated + UNK-033; R-074 combination guard; R-002 small-unit facet
live with approval-level inversion proven); R-054 audit (6-conjunct
exemption, partial encoding proven fail-OPEN, Form-I else-branch);
inventory sweep (facet families, no true duplicates); hygiene audit
(guards correctly outside the engine); HW-chain audit (R-096 ANY≡overlap
precedent for exact, non-invented quantifier reduction). Pack tests
themselves name R-043/R-044 `test_r*_exemption` while pinning TRUE→
`applies` — the inversion is test-pinned, hence migration-visible.

## 3. R-002 Semantic Reconstruction

Register: `SMALL_UNIT := water<25 AND fuel<25 AND NOT MAH` (EIA 5(f)
col 5). Legal role per APR-001's trigger summary + R-003 (`CAT_BASE :=
A unless notified/small → B`): **exception to Category A /
classification facet feeding Category B** — small units still need EC
(state appraisal). It is NOT an exception to EC itself. Current engine
role: sole live trigger of APR-001. Desired role: CLASSIFICATION —
decisive only inside R-003's composition, never directly
approval-decisive. The design must not turn "small" into "EC does not
apply" (the naive EXEMPTION assignment) nor keep "small" as "EC
applies" (current). With trigger unknown + small TRUE, the only honest
verdict is INSUFFICIENT_DATA.

## 4. R-054 Semantic Reconstruction

`EC_EXPANSION_EXEMPT` := 6-AND (expansion; item∈{2,3,4,5}; no load
increase; Appendix-XIII certificate; OCMS≥95%; no B2→A/B1 change);
else Form I under 7(ii)(a). Desired role: EXEMPTION — TRUE relieves
the fresh-EC duty **and routes to the exemption consequence**
(certificate already filed by construction), FALSE/UNKNOWN contribute
nothing, and the else-branch is a routing outcome (Form I), never
DOES_NOT_APPLY. Preserved: EXEMPTION TRUE ≠ APPROVAL APPLIES;
EXEMPTION UNKNOWN ≠ EXEMPTION FALSE (UNKNOWN must block any APPLIES
built on the trigger, §8 row 12).

## 5. Current APR-001 Model

One live rule (R-002, mis-roled trigger); four deferred nodes of the
register's own five-rule tree (R-001 trigger, R-003 category composer
consuming R-002's output, R-004 GC escalator, R-005 estate gate);
R-064/R-074/R-075 outside `rule_ids` (scope guard, combination guard,
validity lifecycle — correctly external). The register's tree is
evidence-complete as a *description*; the engine can execute exactly
one mislabeled node of it.

## 6. Semantic Role Inventory

Evaluated seven; recommended three, with four explicitly excluded:

- **TRIGGER** (default): TRUE = duty/approval attaches; FALSE = trigger
  not met; UNKNOWN = unknown. Alone decisive under current priority.
  Backward-compatible home for R-007/009/011/012/018/026/028/046/056/
  067/070/073/077(with §8 note)/083/084/086/089/093/094/096.
- **EXEMPTION** (duty-defeat): TRUE = duty negated/relieved for the
  matched scope (reason carried, e.g. "Class-B exempt", "MSE exempt",
  "deemed registered"); FALSE = no information (not "duty attaches");
  UNKNOWN = unknown (blocks APPLIES, never ignored). Never produces
  APPLIES. Home for R-030/R-043/R-044/R-087/R-054-class.
- **CLASSIFICATION**: TRUE/FALSE = category input value; never directly
  approval-decisive; consumed only by explicit composition (R-003
  pattern); unconsumed output is informational (surfaces as
  INSUFFICIENT_DATA at approval level, never APPLIES/DOES_NOT_APPLY).
  Home for R-002. Merging it into EXEMPTION is rejected: small-unit
  TRUE must not negate EC (Cat B still applies).
- Excluded (stay outside the engine, current posture): GUARD
  (R-015/R-074/R-059 — verdicts about the decision, not inputs to
  it), ROUTING (R-023/047/078/080 — string selectors), LIFECYCLE
  (R-062/063/075/099/CMP-007 — validity/renewal state machines),
  WORKFLOW (R-081 — case-state consequences). Giving these half-roles
  inside applicability would re-create the defect with new names.

## 7. Polarity Analysis

Legal transformations (require explicit, typed composition):
TRIGGER TRUE + no live EXEMPTION TRUE → APPLIES. TRIGGER TRUE +
EXEMPTION TRUE → DOES_NOT_APPLY *with exemption reason* (typed
defeat, not silent inversion). TRIGGER TRUE + EXEMPTION UNKNOWN →
CONDITIONAL/INSUFFICIENT (never APPLIES). CLASSIFICATION alone (any
value, trigger not TRUE) → trigger's own result, i.e. at most
DOES_NOT_APPLY-as-"trigger unmet" or INSUFFICIENT — never APPLIES.
Illegal without composition: TRUE→DOES_NOT_APPLY, FALSE→APPLIES,
UNKNOWN→FALSE, UNKNOWN→DOES_NOT_APPLY, exception/exemption TRUE→
approval FALSE-by-silence, exemption FALSE→approval TRUE,
exemption TRUE→READY. R-077's embedded BLOCK (OE + LARGE → block) is
a trigger-with-defeater collapsed into one predicate: migration must
split it (TRIGGER limb + EXEMPTION limb) or explicitly grandfather
its collapsed form with a test pin — no silent third option.

## 8. Three-Valued Truth Model

Per-role values compose only through the approval function, never
rule-to-rule (no composition primitive is introduced in phase 1):

- TRIGGER ∈ {T (attaches), F (not met), U (unknown)}.
- EXEMPTION ∈ {T (defeats, with reason), F (no info), U (unknown)}.
- CLASSIFICATION ∈ {T, F} (informational) / U.
- Approval(TRIGGERS, EXEMPTIONS, CLASSIFICATIONS) =
  - any EXEMPTION T AND any TRIGGER T → DOES_NOT_APPLY(reason);
  - any EXEMPTION T AND no TRIGGER T → TRIGGER result (defeat needs
    something to defeat; exemption alone never APPLIES);
  - any EXEMPTION U AND any TRIGGER T → CONDITIONAL (unknown defeater
    blocks APPLIES);
  - else current priority over TRIGGER results only;
  - CLASSIFICATION outputs never enter the priority; unconsumed →
    approval INSUFFICIENT_DATA only if no TRIGGER result exists,
    else invisible with provenance retained.
- APPROVAL TRUE + EXEMPTION TRUE → DOES_NOT_APPLY(reason) — the only
  sanctioned TRUE→negative path, explicit and typed. APPROVAL TRUE +
  EXEMPTION UNKNOWN → CONDITIONAL — the anti-fail-OPEN row.

## 9. Approval Composition Model

Minimal data: per-approval optional `composition` naming trigger ids,
exemption ids, classification ids + their consumer (initially only
APR-001's R-003-pattern). Absent composition = current behavior
**if and only if** every rule defaults to TRIGGER — which is why
migration re-pins R-002/R-030/R-043/R-044/R-087 deliberately instead
of silently. R-001/R-003/R-004/R-005 stay deferred (evidence), R-064/
R-074/R-075 stay outside `rule_ids`; composition must work while they
remain absent (empty trigger set + CLASSIFICATION R-002 alone →
INSUFFICIENT_DATA: the honest current verdict for APR-001).

## 10. Downstream Readiness Implications

Readiness consumes the approval verdict, so role separation propagates
without graph changes: EXEMPTION-defeated DOES_NOT_APPLY carries its
reason into explanation/next-action ("no action: exempt under X") and
must NOT satisfy downstream prerequisites as "obtained" (defeat ≠
grant — DEP-009-style edges still require obtained_approvals). UNKNOWN
defeaters hold READY via CONDITIONAL. CLASSIFICATION-only approvals
report INSUFFICIENT_DATA, blocking READY fail-closed. Documents/SLA
paths are untouched (they key off approval_id, not roles).

## 11. Similar Patterns in Repository

Defect family (live, test-pinned TRUE→applies): R-002 (classification
posing as trigger), R-030/R-043/R-044 (exemptions), R-087 (deeming).
Collapsed-form note: R-077 (trigger+block), R-035 (branch guard;
TRIGGER-compatible for branch-record APR-029, no change proposed).
Correctly-external kin (must NOT gain roles): guards R-015/R-074,
routers R-047/R-078/R-080, lifecycle R-062/R-063/R-099/R-075/R-055,
workflow R-081, hygiene R-059/R-071/R-072/R-076. GJ pack: same engine,
all A-code rules trigger-shaped; default-TRIGGER preserves
byte-identical GJ behavior (regression suite is the proof gate).

## 12. Design Option A — Role Field + Approval Composition

Add optional `role: TRIGGER (default) | EXEMPTION | CLASSIFICATION`
to `ApprovalRule` (default preserves byte-identical behavior for all
26 MH + 19 GJ rules on day one), plus optional per-approval
`composition` naming trigger/exemption/classification ids with the §8
function. `evaluate_rule` unchanged (three-valued per-rule verdicts);
`summarize_by_approval` becomes role-aware (single production
consumer besides tests: `orchestration/service.py:420,598`); reason
strings carry defeat provenance ("DOES_NOT_APPLY: exempt under R-043
MSE limb"). Migration = data (role labels in `seed/mh/approvals.py`,
composition for APR-001) + re-pinned rule tests + new composition
tests; no engine-operator changes.

## 13. Design Option B — Facet Layer + Outcome Mapping

Keep `ApprovalRule` trigger-only: move exception/exemption/
classification predicates to a parallel facet registry evaluated by
the same three-valued engine, with a per-approval mapping function
(TRIGGER verdicts × facet verdicts → approval verdict, implementing
§8). Production `ApprovalRule` semantics never change meaning;
facets cannot leak into `summarize_by_approval` by construction
(separate types). Costs a second registry + loader + pack dimension +
mapping DSL; mapping rows need the same audit rigor as roles, and two
registries can drift (a facet renamed without its mapping).

## 14. Tradeoffs

Correctness: both express §8 exactly. Complexity: A touches one model
+ one aggregator; B adds a registry, loader, pack field, and mapping
layer. Compatibility: A defaults safe (unmigrated rules behave today);
B is safe by construction (facets start outside the decision path).
Testability/auditability: A keeps one rule list with visible labels
(auditors read role beside predicate); B separates concerns but
splits the audit trail across two registries. Traceability: A carries
defeat reason in the existing reason channel; B needs a parallel
channel. Migration cost: A = relabel + repin; B = new layer + move +
repin. Misuse risk: A — future authors omit `role` (defaults to
TRIGGER: fail-OPEN by default; needs a lint/test enforcing explicit
roles for new APR-001-family rules); B — future authors put a trigger
in the facet layer or vice versa (needs the same lint, plus
cross-registry review). UNKNOWN preservation and inversion
prevention: equivalent given §8 in either.

## 15. Rejected Designs

- Every TRUE = approval applies / every FALSE = does not apply:
  the current defect (§1 probes).
- Exemptions as NOT predicates (`NOT small → EC applies`): double
  negation collapses UNKNOWN→FALSE and erases the defeat reason;
  also cannot express the Form-I else-route.
- Silent negation of exception results: same information loss, plus
  R-002-as-negation would yield "EC does not apply" for small units
  (Cat B still applies — wrong).
- Name-inferred polarity (`EXEMPT` in id → invert): renames change
  law; unauditable.
- LLM interpretation of role: nondeterministic, untraceable,
  violates deterministic-rules-decide.
- Generic `invert: true` flag without typing: permits TRIGGER
  inversion and CLASSIFICATION defeat — the R-002 trap with a config
  switch; no reason channel.
- Routing/guards as applicability (R-078/R-080/R-015 patterns):
  string selectors and verdicts-about-verdicts are not truth-apt
  inputs; prior audits already hold them out.
- Single DEFEATER role swallowing CLASSIFICATION: small-unit TRUE
  would negate EC (Cat B exists) — refuted by R-003 semantics.
- Collapsed trigger+block predicates for new rules (R-077 pattern):
  grandfathered only with explicit pins, never as a template.

## 16. Backward Compatibility

R-018/096/007/009/011/012/026/028/046/056/067/070/073/083/084/086/
089/093/094 are TRIGGER (no change under either option; their pins
stand). Behavior-changing migrations, each with deliberate re-pinning:
R-002 → CLASSIFICATION (APR-001 alone → INSUFFICIENT_DATA: the defect
fix), R-030/R-043/R-044/R-087 → EXEMPTION (TRUE → reasoned
DOES_NOT_APPLY; UNKNOWN → CONDITIONAL instead of invisible),
R-077 → split or grandfathered collapse, R-035 unchanged (branch
TRIGGER). GJ: default preserves byte-identity; full GJ suite green
required before/after. No migration without moving the corresponding
pinned expectations explicitly — silent behavior drift is the failure
mode this design exists to prevent.

## 17. Migration Strategy

1. Model: add optional role (A) or facet registry (B); default =
   current behavior; no rule touched.
2. Schema/register: role labels live beside predicates in
   `seed/mh/approvals.py` (A) or facet rows with mapping (B); no CSV
   format change required in either (code-side data first, registers
   later if at all).
3. Engine: role-aware aggregation only (A) or mapping evaluator (B);
   leaf/AND/OR/NOT untouched.
4. Pack: serve composition/mapping through `load_regulatory_pack`
   (no second source of truth).
5. Order: one isolated facet first (R-043 MSE exemption: single
   approval APR-043, clean TRUE/FALSE/UNKNOWN pins) → regression →
   APR-001 (R-002 → CLASSIFICATION; R-001 still deferred so verdict
   becomes honest INSUFFICIENT_DATA) → downstream readiness verify
   (DEP-009 BLOCKED preserved) → R-030/R-044/R-087 only with fresh
   pins → R-077 split decision last.
6. Tests: behavior-change tests moved deliberately; composition truth
   table (§18) implemented; GJ + full MH suites green at every step.
7. Regression: any unmigrated approval behaves byte-identically
   (default TRIGGER / trigger-only layer).
8. Reports: EC + R-054 audits updated with outcome; inventory counts
   unchanged (no rule added/removed).

## 18. Test Specification

Each row: INPUT → ROLE → rule verdict → APPROVAL consequence + WHY.
(1) trigger T → TRIGGER → T → APPLIES (duty attaches).
(2) trigger F → TRIGGER → F → DOES_NOT_APPLY (trigger unmet).
(3) trigger U → TRIGGER → U → INSUFFICIENT_DATA.
(4) exemption T alone → EXEMPTION → T → trigger result only, never
APPLIES (no duty established to defeat; current defect corrected).
(5) exemption F alone → EXEMPTION → F(no info) → trigger result only,
never DOES_NOT_APPLY-by-exemption (current defect corrected).
(6) exemption U alone → U → INSUFFICIENT_DATA.
(7) R-054-shape T → EXEMPTION → T → recorded exemption consequence
(Form-I else preserved), never APPROVAL APPLIES.
(8) R-054-shape F → EXEMPTION → F(no info) → trigger result.
(9) R-054-shape U → U → blocks APPLIES (CONDITIONAL).
(10) trigger T + exemption T → DOES_NOT_APPLY(reason) (sole sanctioned
TRUE→negative path).
(11) trigger T + exemption F → APPLIES (no defeat).
(12) trigger T + exemption U → CONDITIONAL (anti-fail-OPEN row).
(13) trigger U + exemption T → INSUFFICIENT_DATA (defeat needs a
duty; exemption recorded in provenance).
(14) trigger U + exemption F → INSUFFICIENT_DATA.
(15) trigger U + exemption U → INSUFFICIENT_DATA.
(16) R-002 small T, R-001 U → INSUFFICIENT_DATA (not APPLIES).
(17) R-002 F (not small), R-001 U → INSUFFICIENT_DATA (not
DOES_NOT_APPLY).
(18) R-054-shape T + APR-052 docs clear → exemption consequence, and
approval must NOT report READY-as-grant (READY only via trigger
path; exemption path yields its own terminal status).
(19) any U defeater with READY-candidate trigger → READY withheld
(CONDITIONAL) — downstream INSUFFICIENT_DATA protection.

## 19. Regulatory Evidence Boundaries

Design changes no evidence: UNK-033, category lookup, GIS, R-001/R-064
formulation evidence, R-074 combination evidence, R-054 missing facts
all remain deferred/ungated exactly as audited. Composition works
with R-001 absent (CLASSIFICATION alone → INSUFFICIENT_DATA). No
evidence may be invented to populate a role: role labels cite the
register predicate + audit (R-002→R-003 CAT_BASE; R-030 s.7(1)(a);
R-043/044 GW exemption limbs; R-087 s.45(2) deeming).

## 20. Open Design Questions

1. Should CLASSIFICATION outputs surface informationally in
   explanations while INSUFFICIENT_DATA holds (yes, recommended)?
2. Terminal status vocabulary for exemption-defeated approvals
   (DOES_NOT_APPLY+reason vs a dedicated EXEMPT status — deferred to
   implementation; reason channel suffices for phase 1).
3. Whether R-077's collapse is split now or grandfathered (needs its
   own mini-audit; both paths specified).
4. Lint enforcement for explicit roles on new rules (required under
   A; cross-registry review under B).
5. Whether CMP-duty rules (R-070/093/094) want a DUTY role later —
   explicitly out of phase 1 (they behave trigger-compatibly today).

## 21. Implementation Preconditions

Coding starts only when ALL hold: (a) option chosen + §8 frozen as
the acceptance table; (b) §18 rows written as tests first (TDD);
(c) default-behavior-unchanged proof (full MH+GJ suites green with
defaults); (d) migration order (§17.5) agreed with audit owners of
R-002/R-030/R-043/R-044/R-087 pins; (e) orchestration READY-path
review signed off (defeat ≠ grant for DEP-009-style edges);
(f) no evidence prerequisite — design must land with R-001/R-054
still deferred.

## 22. Final Design Recommendation Without Ranking Alternatives

The minimum semantic contract implementation must satisfy: (i) every
rule carries an explicit, audited role from {TRIGGER, EXEMPTION,
CLASSIFICATION} (TRIGGER default only with a lint requiring explicit
labels on new rules); (ii) EXEMPTION/CLASSIFICATION outputs can never
produce APPLIES, alone or combined; (iii) EXEMPTION TRUE with TRIGGER
TRUE yields DOES_NOT_APPLY carrying the exemption reason — the sole
permitted TRUE→negative path; (iv) EXEMPTION UNKNOWN with TRIGGER
TRUE yields CONDITIONAL, never APPLIES; (v) CLASSIFICATION outputs are
consumed only by named composition, otherwise informational;
(vi) GUARD/ROUTING/LIFECYCLE/WORKFLOW stay outside the applicability
engine; (vii) defeat never counts as grant downstream (READY only via
the trigger path); (viii) UNKNOWN never becomes FALSE at any layer.
Either option A or B satisfies the contract if it implements (i)–
(viii) verbatim with §18 green before migration begins.
