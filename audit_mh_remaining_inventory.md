# Maharashtra Regulatory Engine — Remaining Inventory, Safety & Roadmap Sweep

Independent parallel-session sweep. Jurisdiction: IN-MH (primary). IN-GJ is
regression/reference only. Date (UTC): 2026-09-29.

Scope guard: the consent-category cluster **R-013 → R-014 → R-015 → R-017 is
audited in a parallel session and is excluded from this roadmap**. No file
owned by that cluster was modified here; no pack logic, engine, fact, or
active-rule code was changed.

Authoritative inputs: CURRENT working-tree `backend/app/seed/mh/*`,
`backend/app/rules/facts.py`, `backend/app/seed/pack.py`, and the v5
registers under `UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/`
(73 files; rule_register_v5.csv = 105 rules R-001..R-105).
Completed-audit evidence on disk: 3 report artifacts
(`audit_mh_fire_building.md`, `audit_mh_workflow_lifecycle.md`,
`audit_mh_midc_lifecycle_tail.md`), 23 `test_mh_*.py` files, and
ARCHITECTURE.md §§35–63. Older clusters have **no standalone .md report**;
their record is the ARCHITECTURE section plus the cluster test file. Nothing
below infers "audited" from an old note without a current-register
cross-check.

## 1. Current Baseline

Verified from the working tree (not assumed from the brief):

| Dimension | Brief said | Verified now | Delta |
|---|---|---|---|
| MH active | 26 | **26** | — |
| MH deferred | 58 | **59** | +1 = **R-015** (multi-activity cardinality guard), added in working tree by the parallel consent-chain session |
| MH confirmation-gated | 26 | **26** | — |
| MH facts | 128 | **128** | — |
| GJ active | 19 | **19** | — |
| `DEFAULT_JURISDICTION` | IN-GJ | **IN-GJ** (`backend/app/seed/pack.py:73`) | — |

Register arithmetic (exact, machine-checked): 105 register rules = 26 active
+ 59 deferred + 26 confirmation − 15 (deferred∩confirmation overlap) + 3 DNI
− 0 (UNKNOWN adds no new ID: R-015 deferred, R-052 deferred+confirmation,
R-074 confirmation) = 99 triaged + **6 untriaged** (see §6). All five code
sets (`MH_INCLUDED`, `MH_DEFERRED_RULES`, `MH_REQUIRES_CONFIRMATION_RULE_IDS`,
`MH_DO_NOT_IMPLEMENT_RULE_IDS`, `MH_UNKNOWN_RULE_IDS`,
`MH_IMPLEMENTATION_SAFE_RULE_IDS`=76) are ⊆ R-001..R-105. Zero dangling IDs.

Addendum (2026-09-29, during the controlled-substance audit): a parallel
MSIHC session deferred **R-021** with a substantive reason (now 60
deferred, 100 triaged, **5 untriaged**: R-054/059/071/072/076).
`test_mh_remaining_inventory.py` was updated to the new legitimate
baseline; the §6 R-021 row is superseded by that session's triage.

Addendum 2 (2026-09-29, during the residual-hygiene audit): a follow-up
session implemented the R-054 audit's recommendation and deferred
**R-054** with the falsification rationale (now **61 deferred**, 101
triaged, **4 untriaged**: R-059/071/072/076 — exactly this hygiene
audit's scope). Pins updated again; the R-021 session's 5-set pin now
belongs to that session's follow-up.

Pre-existing working-tree changes (committed HEAD = sector-specific cluster,
deferred 50; uncommitted = EPR/CTO/establishment/fire/workflow/MIDC-tail
audits + R-015 + relaxed sector count test) were inspected via `git status` /
`git diff` and left untouched. During this session the parallel consent-chain
audit added `audit_mh_consent_category_chain.md` +
`backend/tests/test_mh_consent_category_chain.py` (observed, untouched).
New files from this session: this report +
`backend/tests/test_mh_remaining_inventory.py` (12 tests).

## 2. Complete MH Rule Inventory

`_encode()` is default-deny (deferred → safe-allowlist → confirmation → DNI
→ UNKNOWN), so anything unlisted fails closed. Buckets A–J per rule
(A=active-audited, B=deferred-justified, C=confirmation-justified,
D=safe-untriaged, E=re-audit-ready, F=duplicate, G=orphan, H=obsolete,
I=evidence-blocked, J=architecture-blocked; deferred∩confirmation members
shown as B+C):

Active, audited (A, 26): R-002 APR-001 · R-007 APR-003 · R-009 APR-004 ·
R-011 APR-006 · R-012 APR-007 · R-018 APR-010 · R-026 APR-019 · R-028 APR-023 ·
R-030 APR-026 · R-035 APR-029 · R-043 APR-043 · R-044 APR-043 · R-046 APR-044 ·
R-056 APR-054 · R-067 APR-055 · R-070 CMP-018 · R-073 APR-023 · R-077 APR-043 ·
R-083 LOC-CRZ · R-084 LOC-FOREST · R-086 APR-023 · R-087 APR-023 ·
R-089 APR-022 · R-093 CMP-024 · R-094 CMP-025 · R-096 APR-010.
All 26 use only F-facts (36 distinct, all present in the 128-fact registry),
all source_refs resolve in the 22-source loaded corpus, all approvals carry
an authority string. No rule-reference composition exists in any builder
(verified: every leaf field is `F-*`).

Deferred, justified (B, 44 incl. overlaps): R-001 R-003 R-004 R-008 R-013
R-014 R-017 R-019 R-020 R-022 R-023 R-024 R-025 R-027 R-031 R-032 R-033 R-034
R-038 R-041 R-045 R-047 R-048 R-050 R-051 R-052 R-053 R-055 R-060 R-061 R-062
R-063 R-064 R-065 R-066 R-068 R-069 R-075 R-078 R-079 R-080 R-081 R-082 R-085
R-088 R-090 R-091 R-092 R-095 R-097 R-098 R-099 R-100 R-101 R-102 R-103 R-104
R-105 (44 of the 59; 15 more are B+C below; R-015 counted in the 59).

Confirmation-justified (C, 26): R-005 R-006 R-010 R-022 R-023 R-025 R-034
R-036 R-037 R-038 R-039 R-040 R-042 R-048 R-049 R-051 R-052 R-053 R-057 R-063
R-068 R-069 R-074 R-090 R-097 R-098 — of which 15 are also B
(R-022 R-023 R-025 R-034 R-038 R-048 R-051 R-052 R-053 R-063 R-068 R-069
R-090 R-097 R-098) and 11 are C-only (R-005 R-006 R-010 R-036 R-037 R-039
R-040 R-042 R-049 R-057 R-074).

Untriaged SAFE (D/J/I, 6): R-021 (J) · R-054 (I) · R-059 (J-intentional) ·
R-071 (J-intentional) · R-072 (D-documented, EPR-audited) · R-076
(J-intentional). Details in §6.

DNI (intentional, 3): R-016 (CTE deemed/micro-small) · R-029 (petroleum
licence core + Class-A exemption) · R-058 (INCENTIVE_BASKET). All match
`do_not_implement.csv`.

E (re-audit-ready): **none** — no deferred rule's missing source/fact was
added, no primitive was introduced, fact registry unchanged at 128
(see §4). R-015's status change belongs to the parallel session.

F/G/H: no confirmed true duplicates, no orphaned rules (every R-001..R-105
is referenced by ≥1 register/code set), no confirmed obsolescence (see §7–8).

Audit-coverage map (cluster → rules → evidence on disk): batch-1 →
R-002/007/009/011/012/018/026/028/030/035/043/044/046/056/067/070/089/093/094
(`test_mh_pack.py`); batch-2 → R-073/086/087 + R-075/088/100–104 triage
(`test_mh_pack_batch2.py`); location → R-077/083/084/096 + R-060/061/085/091
triage (`test_mh_pack_location_cluster.py`); planning/fire → R-041/078/079/
080/082 (`test_mh_pack_planning_fire.py` + `audit_mh_fire_building.md`
re-audit incl. R-037); environmental/consent → R-003/004/007/008/013/014
(`test_mh_pack_environmental_consent.py`); labour/factory →
R-019/020/027/022/023/090 (`test_mh_pack_labour_factory.py`); utilities →
R-038/048/052/053/097 (`test_mh_utilities_water_power.py`); safety/hazmat →
R-030/032/033/034/035/062/092 (`test_mh_safety_hazardous_transport.py`);
sector → R-051/068/069/095/105 (`test_mh_sector_specific.py`); EPR →
R-094/EPR regimes/Form V/env-audit (`test_mh_environmental_epr.py`,
uncommitted); CTO/renewal → R-017/055/063/CMP-007 (`test_mh_cto_renewal.py`,
uncommitted); establishment → R-024/025/098
(`test_mh_establishment_labour.py`, uncommitted); workflow →
R-081/099/036 (`audit_mh_workflow_lifecycle.md`, uncommitted); MIDC-tail →
R-039/040/APR-031/DEP-019 (`audit_mh_midc_lifecycle_tail.md`, uncommitted).
Parallel: R-013/014/015/017 (files owned elsewhere — not inspected beyond
the R-015 deferred entry).

## 3. Active Rule Safety Review

Every active rule's leaves ⊆ MH_FACTS (36/36 used facts present, zero
missing), sources ⊆ 22-source corpus, approvals ⊆ authority map,
no rule-as-fact composition. **Zero unsafe active rules.**

Two safe-but-notable findings (no action required):

1. **Known-blocked readiness (fail-closed, correct).** Loaded dependencies
   are exactly DEP-009 ×2: APR-010 requires APR-008 (CTE) + APR-009 (CTO).
   Neither APR-008 (R-013/014/015 deferred, R-016 DNI, R-062 deferred) nor
   APR-009 (R-017/R-063 deferred) has an active rule, so R-018/R-096 may
   evaluate APPLIES yet never reach READY until the consent chain lands.
   Pinned in `test_mh_remaining_inventory.py::TestKnownBlockedReadiness`.
2. **Partial APR-001/APR-043 coverage (correct, not a bug).** APR-001's
   affirmative EC trigger R-001 is deferred; only the small-unit exception
   facet R-002 is active. APR-043 rests on exemption/OE facets
   (R-043/044/077) while the general core R-045 is deferred; unevaluated
   facets yield INSUFFICIENT_DATA, never a false DOES_NOT_APPLY.
   DEP-030 (SC-NBWL → APR-001) is registered but intentionally not loaded,
   so applicability is unaffected.

## 4. Deferred Rule Review

All 59 deferred entries re-checked against current code/registers:
**DEFERRAL STILL VALID** for 58. Nothing they wait on has moved — fact
registry still 128, source corpus still 22/188, no new ConditionNode
primitive, no lookup/aggregation/composition/GIS/date-arithmetic support,
MIDC DCR text still missing (UR-19), sector table still undigitized
(R-014), multi-code aggregation still forbidden (R-015 note). The 59th,
**R-015, is owned by the parallel consent-chain audit** (its working-tree
deferral entry is recorded here for arithmetic only, not judged).

Deferred rules never given a 20-dimension cluster audit (batch-2 one-line
triage only, still valid on current evidence): R-001 R-031 R-045 R-047
R-050 R-064 R-065 R-066 R-075 R-088 R-100 R-101 R-102 R-103 R-104. These feed
the roadmap (§13), not a re-audit verdict.

## 5. Confirmation-Gated Review

All 26 gates re-checked: **every gate still valid; none removed, none
demoted to deferred, none promoted.** Spot notes: R-057 (MSME_CLASS) is
correctly gated (turnover bands await confirmation) while its verbatim-band
derivation `derive_msme_class()` already serves R-043/R-077 inputs —
derivation ≠ rule activation, no conflict. R-074 (5(f)+8(a) UNKNOWN) is
correctly gated per UNK-010 (register note confirms Dec-2025 secondary
reports were rightly refused as evidence). R-049 (lift) is gated on
UNK-006 (1939 vs 2017 Act commencement) — the single C-only rule with no
cluster audit and a pure-threshold shape; it is an evidence case, not an
engine case (§13). R-005/R-006/R-010 (EC scope/estate) are gated on
per-estate/per-product appraisal facts (UNK-004, expert scope) — correctly
not deferred (the question is evidence, not representability). The 15 B+C
members are correctly double-held (unrepresentable AND unconfirmed).

## 6. Untriaged Rules

Exactly six register-IMPLEMENTATION_SAFE rules have no builder and no
explicit code triage (default-deny `_encode()` refuses them with the generic
"not IMPLEMENTATION_SAFE", which is safe but reason-free):

| Rule | Approval | Why untriaged | Difficulty | Likely class |
|---|---|---|---|---|
| R-021 MAH derived notification/safety-report/plan | APR-012 REPORT | required_inputs is rule R-019; needs EXISTS + schedule aggregation + mapping pipeline | MEDIUM | dependency/compliance → expect J-deferral |
| R-054 EC expansion / no-pollution-increase exemption | APR-052 APPROVAL/OPERATION | needs auditor-certificate-on-PARIVESH + SPCB-submission workflow facts; effective UNKNOWN; Sch-item {2,3,4,5} scope | MEDIUM | lifecycle/evidence → audit first |
| R-059 INCENTIVE_VALUE := NOT_COMPUTED | INC-* guard | hard-stop guard node; nothing to encode | LOW | other (intentional; needs triage note only) |
| R-071 MH_GW_ACT_IN_FORCE regime gate | CND-024 RULE_LOGIC | regime date-gate, not an approval | LOW | other (intentional; needs triage note only) |
| R-072 ENV_AUDIT conditional | CMP-014 RULE_LOGIC | EPR-cluster audited; CMP-014 is DNI in compliance.csv | LOW | compliance (intentional; needs explicit code note) |
| R-076 EC_COMPLIANCE_DUE 1-Jun/1-Dec | CMP-006 RULE_LOGIC | DATE-scheduling semantics → deadline/compliance layer, not the applicability engine | LOW | workflow (intentional; needs explicit code note) |

Nothing here is implemented (correct). The gap is traceability, not safety.

## 7. Duplicate / Semantic Overlap Findings

**No confirmed true duplicates.** Findings are facet families (one legal
regime, several non-overlapping rule facets — the register's design, not a
defect): APR-001 EC facets (R-001 core deferred / R-002 exception active /
R-064 scope deferred / R-003/004 category deferred / R-074 combo UNKNOWN);
APR-043 GW facets (R-043 MSE / R-044 domestic-greenbelt / R-077 OE /
R-045 general core deferred); APR-023 boiler facets (R-028 registration /
R-073 BOE operating condition / R-086 NOT_REGISTERED restatement mirroring
R-028 by pinned test / R-087 transitional); APR-026 petroleum facets
(R-030 Class-B exemption active / R-031 Class-C deferred / R-032 form
routing deferred / R-092 NOC deferred / R-029 core DNI); APR-010 HW facets
(R-018 authorisation / R-096 Schedule-II characteristic); fire/planning
routing-vs-applicability separations (R-078/R-080 CASE selectors,
R-082 regime selector, R-042 composition hub — all correctly held out of
the applicability engine); triple-target bundle R-036 (APR-030/031/033,
correctly gated, not split). Shared AUT-xxx authorities and the DEP-009
split into two explicit edges are intentional, not duplication.
Report-artifacts-as-approvals (APR-031 plinth intimation = REPORT) are
correctly unmodeled with zero code references.

## 8. Orphan / Dead Data Findings

**No orphaned rules; no dangling references.** All status sets ⊆
R-001..R-105 (machine-checked). Intentional-unmodeled inventory (kept, not
stale): rule-less approvals APR-011/APR-013/APR-060 (all DNI) and FAC-001
(facilitation, never a readiness edge); 92/128 facts unused by active
rules (reserve for deferred/future rules + derivations — batch-1 consumes
29, derivations consume F-INC-02/09 + F-HAZ-01/02); 166/188 sources
unloaded (deferred-rule provenance, correctly out of the 22-source active
corpus); 32/34 register dependencies triaged out in `MH_DEP_DEFERRED`
(loaded: DEP-009 ×2 only); UNKNOWN-edge deps DEP-021/023/024/025 and
FACILITATION_ONLY DEP-020 correctly never edges. `requires_confirmation.csv`
carries 26 approval/topic-keyed rows plus 26 R-xxx-keyed rows whose `id`
values match `MH_REQUIRES_CONFIRMATION_RULE_IDS` exactly (verified during
the EC-core audit), so no rule-level dangling entries exist. Empty dimensions are explicit
by evidence (MH consistency = [] by register-wide search; incentives empty
for IN-MH), not accidental.

## 9. Consolidated Evidence Gaps

Grouped per the mandated 13 categories (severity: BLOCKING stops an audit
conclusion; IMPORTANT narrows it; LOW is hygiene):

1. **Source missing** — MIDC DCR text (UR-19, BLOCKING for R-036/037/039/
   040); GCR amendment gazettes (UR-10, BLOCKING for R-033/034/103/104);
   sector notifications for Mathadi scheduled employment (BLOCKING for
   R-098); MAITRI per-service specs (UR-13, IMPORTANT).
2. **Source outdated** — CEI RTS 2018 citing superseded CEA 2010 regs
   (R-048, BLOCKING); PESO SOP T3 as sole Class-A basis (CON-014 → R-029
   DNI, BLOCKING); portal-legacy boiler citations (CLOSED_V3, LOW).
3. **Amendment status unresolved** — HOWM post-2016 Schedule I/II currency
   (UNK-034, IMPORTANT for R-065/096); MSIHC post-2000 amendments
   (UNK-035, IMPORTANT); ODS post-2000/Kigali (IMPORTANT for R-095).
4. **Effective date unresolved** — MIDC/fire rows effective UNKNOWN
   (R-036/037/039/040/042, BLOCKING for any activation); R-054 expansion
   date UNKNOWN (BLOCKING); 2017 Lifts Act commencement (UNK-006,
   BLOCKING for R-049).
5. **Authority unresolved** — insecticide/drugs licensing officer + forms
   (UR-11/UNK-036, BLOCKING for R-068); WRD competent authority (UR-17,
   BLOCKING for R-053); APR-055 licensing-officer identity noted UNKNOWN
   in the active authority string (IMPORTANT, display-level).
6. **Threshold unresolved** — F-ELE-02 Maharashtra self-certification
   voltage (UNK-005, BLOCKING for R-048); Sch-2 ethylene-oxide col-4
   print ambiguity (UR-01, IMPORTANT); ethyleneimine 50t-vs-5t (UR-02,
   IMPORTANT); GSR 90/60/30 category-column mapping (UNK-031/GSR-11,
   BLOCKING for R-063 activation).
7. **Classification table incomplete** — CPCB sector→category table
   undigitized (R-014, BLOCKING; parallel session); Schedule-A
   substance list unencoded (R-066, IMPORTANT); CWC declaration
   sub-schedules inside F-CWC-03 list (IMPORTANT for R-065).
8. **Geographic scope unresolved** — 80-watershed village list currency
   (UR-15, BLOCKING for R-097); estate-level CETP facts (UNK-011,
   BLOCKING for R-052); notified-estate status per MIDC estate
   (UNK-004, IMPORTANT for R-003/005); CRZ/forest WLPA site facts
   (CLOSED_V3 as site-dependent, LOW for engine).
9. **Workflow evidence only** — MIDC/fire/consent rows backed solely by
   T3 portal listings (UR-19/UR-04/UR-09, BLOCKING for R-036–R-042,
   R-081/099 correctly held out regardless).
10. **Legal interpretation unresolved** — FORMULATION_ONLY auto-FALSE ban
    + blending/formulation scope (R-001 note + UNK-033, BLOCKING for
    R-001/R-064); 5(f)+8(a) combination silence (UNK-010/UR-06, BLOCKING
    for R-074); factory-construction BOCW exclusion (ET-126, BLOCKING
    for R-090); CTO valid-till-cancelled vs MPCB auto-renewal (CON-006,
    BLOCKING for CMP-007); fire-renewal conflict (CON-013, IMPORTANT).
11. **Missing project fact** — contractor workforce (R-027, BLOCKING);
    licence-held inputs SSC-01/02/03 (R-100/101/102, BLOCKING);
    new-licence/application-date (R-103, BLOCKING); GCR purpose/
    filling-plant (R-104, BLOCKING); package-marking conjunct (R-050,
    BLOCKING); EC grant date (R-075, BLOCKING); `construction`
    (R-036/041, BLOCKING).
12. **Missing system/workflow state** — application/requisition dates +
    DCR-conformance for deemed permission (R-081, BLOCKING by design —
    belongs to case state, never facts); renewal-assignment state
    (R-099/CMP-007, IMPORTANT).
13. **Architecture limitation** — EXISTS/list quantifiers (R-019/020/021/
    033/034/060/061/065-part/091); multi-site aggregation (R-061);
    lookup tables (R-014/R-057-note/R-058/R-066); rule composition
    (R-003/004/008/013-chain/017/042/045/079/092); dynamic authority
    routing (R-023/047/078/080); GIS (R-051/083-note/084-note/097);
    DATE arithmetic (R-075/081/088/076). None justified for the MVP
    (anti-overengineering gate holds).

## 10. Current Engine Capability Check

Question: any remaining MH rule safely implementable with the CURRENT
engine (AND/OR/NOT + eq/in/gte/lte/gt/lt + LiteralNode + effective window)
and CURRENT 128 facts, adding no primitive?

**Answer: NO — no remaining rule is proven-safe to encode now.** The
closest candidates and their exact blockers:

- R-065 (CWC declarations, APR-058): all facts present (F-CWC-01/02/03),
  pure `>` thresholds, T2 source, VERIFIED_CONDITIONAL — structurally the
  closest. Blocked by: (a) RETURN-vs-approval boundary audit still owed
  (APR-058 is COMPLIANCE_APPROVAL/RETURN; R-093/R-094 precedent cuts both
  ways); (b) post-2016 amendment currency (UNK-034); (c) Sch2A*/Sch2B
  sub-list semantics inside the F-CWC-03 list need a quantifier reading.
- R-001 (EC 5(f) core, APR-001): facts present (F-PRD-01/03), T1, EXACT
  dates — structurally encodable. Blocked by: FORMULATION_ONLY no-auto-
  FALSE trap, UNK-033 scope question, and coupling to deferred category
  machinery (R-003/R-004).
- R-049 (lift): pure `>=` threshold, fact present — blocked by
  confirmation evidence (UNK-006), not by the engine.
- Everything else needs a missing fact (§9.11), a missing primitive
  (§9.13), or missing/weak sources (§9.1–3).

## 11. Rules Potentially Safe to Implement

None without a prior focused audit (§10). After the audits in §13,
the implementation order would be: R-065 (if the RETURN boundary audit
passes) → R-001 (if scope evidence resolves) → R-054 (if certificate
workflow facts are ruled case-state, the exemption collapses to
item-membership + dates).

## 12. Rules Requiring Further Audit

Explicit audit backlog (consent chain excluded): R-001, R-005, R-006,
R-010, R-021, R-031, R-045, R-047, R-049, R-050, R-054, R-064, R-065,
R-066, R-074, R-075, R-088, R-100, R-101, R-102, R-103, R-104 (+ hygiene
notes for R-059/071/072/076). All other non-active rules already carry a
cluster audit + fail-closed code entry.

## 13. Prioritized Remaining Roadmap

P1 — EC core cluster (highest regulatory value: the chemical domain's
primary trigger; APR-001 currently fires only its exception facet):
**R-001 + R-064 + R-074** (with R-005/R-003/R-004 as composition context).
Evidence targets: UNK-033, FORMULATION_ONLY appraisal view, UNK-010.
Difficulty MEDIUM. Expected outcome: likely partial activation (R-001
core and/or R-064 scope) or a strengthened, evidence-cited deferral.

P2 — Close the untriaged list + chemical-adjacent duties (small, bounded):
(a) **R-021** MAH-pipeline audit → expected J-deferral confirmation;
(b) **R-065 + R-066 + R-050** controlled-substance/legal-metrology cluster
(R-065 is the closest-to-encodable rule in the pack). Difficulty
LOW–MEDIUM.

P3 — Lifecycle/composition tails (needs new facts or case-state rulings):
**R-054** (EC expansion exemption) + **R-045** (GW general core), then
**R-031 + R-100** (petroleum Class-C + renewals) with R-101/102/103/104
as context. Difficulty MEDIUM–HIGH. Expected outcome: mostly confirmed
deferrals with narrower evidence targets.

P4 — Evidence-blocked singles (do not schedule until the cited unknown
closes): **R-049** (needs UNK-006 Lifts Act commencement), **R-075/R-088**
(event/date facts), **R-047** (confirm routing-only standing — LOW effort,
pairs with any electrical audit). No engine work justified.

P5 — Hygiene & future scope (no audit sessions): one-line explicit code
triage notes for **R-059/R-071/R-072/R-076** (intentionally unmodeled —
guard/regime/deadline semantics); GIS-dependent R-051/097; MAITRI
integration (UNK-009/UR-13); incentive layer R-057/058/059 (IISP
instruments still unlocated, UR-07/UNK-013); EPR residuals (role-dependent
UNK-040/UR-08).

## 14. Risks / Architectural Boundaries

Held boundaries (all respected by current code; re-affirmed): applicability
vs routing (R-023/047/078/080), applicability vs lifecycle/validity
(R-062/063/R-099/CMP-007), approval vs report/return/duty (APR-031,
CMP-005/008, EPR regimes), statutory dependency vs inferred ordering
(DEP-019 YES_INFERRED never an edge; DEP-002/021/023-025 UNKNOWN never
edges), classification vs applicability (R-003/004/008/014/015/023/057),
readiness vs legal obligation (DEP-009 blocks without denying), UNKNOWN
never FALSE (R-015/052/074 + fail-closed `_encode`), no GJ↔MH leakage
(namespaces + persisted-pack resolution + 19/26 isolation tests).
Risks: (a) six untriaged-SAFE rules carry only the generic refusal reason
— traceability debt, not safety debt; (b) uncommitted prior-cluster work
(7 test files + 3 reports + approvals/PRD/ARCH diffs) is the actual
working baseline — a fresh checkout at HEAD would show deferred 50, not
59; (c) display-level authority gaps (APR-055 unknown officer, empty
CMP strings) must never be rendered as authoritative routing.

## 15. Final Status

Inventory complete (105/105 placed); safety review clean (0 unsafe active,
2 safe-notable findings pinned); deferred review unanimous (58 valid +
R-015 parallel-owned); confirmation review unanimous (26/26 gates hold);
6 untriaged identified with dispositions; 0 true duplicates; 0 orphans;
gaps consolidated into 13 groups; engine check answered NO with named
closest candidates; roadmap prioritized P1–P5 excluding the parallel
consent-chain cluster. Implementation deliberately untouched: 0 rules
added, 0 rules activated, pack/engine/facts semantics unchanged.

Validation: new `backend/tests/test_mh_remaining_inventory.py` — 12/12
pass. Full backend suite — **1881 passed, 0 failed** (1809 prior-cluster
baseline + 12 this sweep + 60 parallel consent-chain tests present in the
working tree; no skips in this run). Ruff (`app/`, `tests/`) clean.
Frontend `tsc --noEmit` clean.
ARCHITECTURE.md/PRD.md intentionally unmodified (no new architectural
fact, product-scope change, or count milestone owned by this sweep —
PRD's in-progress cluster entries belong to their authoring sessions).
