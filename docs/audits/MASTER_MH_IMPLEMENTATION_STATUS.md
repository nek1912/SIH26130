# MASTER MH Implementation Status — DONE vs PARTIAL vs REMAINING

Date: 2026-10-02. Source of truth: CURRENT CODE + CURRENT TESTS + CURRENT REGULATORY EVIDENCE in working tree `D:\SIH` (branch `main`, HEAD `226879f` + large uncommitted working tree — see §0). Historical audit reports record intent/observation, not proof.

Core principle (unchanged): deterministic rules decide; RAG retrieves; system explains; human/statutory authority decides. Missing evidence fails closed. No invented regulatory facts, no claimed government integrations.

## §0. Baseline the whole report depends on

- HEAD `226879f` is the last commit. **Everything reconciled below lives ONLY in the uncommitted working tree**: 13 modified tracked files + 12 root `audit_mh_*.md` + `backend/app/seed/mh/scenario.py` + 19 new `test_mh_*.py` + entire `docs/audits/` (10 files, tracked count = 0). Nothing since HEAD is committed; a commit (not done here — not requested) is the single biggest demo-risk item.
- At HEAD, `RuleRole`/`ApprovalComposition` do not exist and R-030 is TRIGGER. The worktree adds the full exception-semantics layer (§4) plus 11 deferred entries (R-015, R-021, R-054, R-017, R-055, R-063, R-024, R-025, R-098, R-081, R-099): HEAD deferred = 50, worktree deferred = 61.
- Worktree test run (2026-10-02, `cd backend && python -m pytest tests/ -q`): **2348 passed, 0 failed**. T1 resolved the former R-030 contradiction (R-030 restored to TRIGGER, APR-026 composition removed, downstream APR-026 expectations restored to the STOP-approved document-blocked contract); code is now consistent with `docs/audits/audit_mh_r030_exemption_migration.md`. See item S-R030.
- `tsc --noEmit`: 0 errors. `ruff check app/ tests/`: 21 × E501 line-length, all worktree-introduced (1 prod line `approvals.py:499`, 20 in new test files). No other lint errors.
- Jurisdiction: `DEFAULT_JURISDICTION = "IN-GJ"` (`seed/pack.py:74`) preserved; persisted `(jurisdiction, pack_version)` identity (migration 010, written/review-verified, live-DB execution still pending staging) intact.

## TABLE 1 — Master status (Historical vs Actual)

Legend: Historical = last claim in PRD/ARCHITECTURE/audit docs. Actual uses only: DONE, PARTIAL, DEFERRED_BY_EVIDENCE, DEFERRED_BY_ARCHITECTURE, CONFIRMATION_GATED, BLOCKED, NOT_IMPLEMENTED, NOT_APPLICABLE, UNKNOWN.

### 1A. The 105-rule inventory (26 active + 61 deferred + 11 confirmation-only + 3 DNI + 4 hygiene = 105; verified: union of sets = 101, + 4 hygiene R-059/071/072/076 in no set)

| Item | Historical Status | Actual Current Status | Code Evidence | Test Evidence | Regulatory Evidence | Remaining Work | Priority | Safe to Leave Deferred? |
|---|---|---|---|---|---|---|---|---|
| R-001 (EC formulation-only) | deferred | DEFERRED_BY_ARCHITECTURE | `mh/approvals.py:76` in MH_DEFERRED_RULES | `test_mh_ec_core.py:157-161` asserts absence | SRC-001 T1; FORMULATION_ONLY non-falsing | None (needs Form-I else-branch primitive) | P3 | YES |
| R-002 (EC small-unit) | CLASSIFICATION (migrated) | DONE | `mh/approvals.py:379-392`, `role=CLASSIFICATION:391`, APR-001 comp `:773-776` | `test_mh_ec_core.py:285-355`; `test_mh_exception_semantics.py` | SRC-001; classification semantics verified | None | — | N/A (active) |
| R-003 (EIA Cat A/B) | deferred | DEFERRED_BY_ARCHITECTURE | `mh/approvals.py:129` deferred (needs R-002 composition) | `test_mh_ec_core.py` pins deferred | Category determination, not approval predicate | Rule-composition primitive | P3 | YES |
| R-004 (EIA GC escalation) | deferred | DEFERRED_BY_ARCHITECTURE | `:133` deferred (ANY over F-LOC-07) | `test_mh_ec_core.py` | Escalation modifier, not predicate | Existential + composition | P3 | YES |
| R-005 | confirmation-gated | CONFIRMATION_GATED | in `MH_REQUIRES_CONFIRMATION_RULE_IDS:50-55`, not deferred/included | residual inventory suite | Unresolved evidence | Evidence first | P3 | YES |
| R-006 | confirmation-gated | CONFIRMATION_GATED | same set | residual inventory suite | Unresolved evidence | Evidence first | P3 | YES |
| R-007 (EIA 8a B&C) | active TRIGGER | DONE | `:396` APR-003, 20,000≤x<150,000 m² | `test_mh_ec_core.py`; batch-1 suite | SRC-001/179; Vanashakti respected | None | — | N/A |
| R-008 (8a GC inoperative) | deferred | DEFERRED_BY_ARCHITECTURE | `:137` meta-rule, would contradict R-007 | `test_mh_ec_core.py` | Meta-rule, not predicate | None | P3 | YES |
| R-009 | active TRIGGER | DONE | `:409` APR-004 | `test_mh_pack.py` (batch-1, 34 tests) | v5 source refs, exact dates | None | — | N/A |
| R-010 | confirmation-gated | CONFIRMATION_GATED | confirmation set only | residual inventory suite | Unresolved evidence | Evidence first | P3 | YES |
| R-011 | active TRIGGER | DONE | `:422` APR-006 | batch-1 + canonical (`APR-006=ready`) | v5 refs | None | — | N/A |
| R-012 | active TRIGGER | DONE | `:432` APR-007 | batch-1 suite | v5 refs | None | — | N/A |
| R-013 (CTE trigger) | deferred | DEFERRED_BY_ARCHITECTURE | `:140` needs R-014 lookup + MPCB_CATEGORY | `test_mh_consent_category_chain.py:194-223` | Sector table not digitized | Lookup engine + composition | P2 | YES |
| R-014 (sector lookup) | deferred | DEFERRED_BY_ARCHITECTURE | `:144` LOOKUP undigitized | consent-chain suite | T4 table not digitized | Lookup digitization | P2 | YES |
| R-015 (multi-activity guard) | deferred (SAFE+UNKNOWN+DEFERRED) | DEFERRED_BY_ARCHITECTURE | `:147`; also UNKNOWN `:65` + SAFE `:38`; deferred check fires first `:354` | `consent_category_chain.py:328-332` | UNK-002; MAX-convention forbidden | Aggregation primitive (forbidden by evidence) | P3 | YES |
| R-016 | DNI | NOT_APPLICABLE | `MH_DO_NOT_IMPLEMENT:57-59`, no builder | residual inventory | Do-not-implement register | None | — | YES (permanent) |
| R-017 (CTO gate) | deferred | DEFERRED_BY_ARCHITECTURE | `:262` input literally R-013, no composition | `test_mh_cto_renewal.py:387-411` | CTO satisfied via DEP-009 obtained-path instead | R-013/R-014/R-015 chain | P2 | YES |
| R-018 (HW generation) | active TRIGGER | DONE | `:442` APR-010 F-HW-01 | `test_mh_hazardous_waste_authorization_chain.py:268-309` | SRC-013 T1 | None | — | N/A |
| R-019 (MSIHC notification) | deferred | DEFERRED_BY_ARCHITECTURE | `:168` EXISTS + Sch-5 routing | `test_mh_pack_labour_factory.py:78-97` | Sch-5 authority routing unresolvable | Quantifier + routing primitives | P3 | YES |
| R-020 (MSIHC safety report) | deferred | DEFERRED_BY_ARCHITECTURE | `:172` col-4 lookup + UR-01 | labour-factory suite | Unconfirmed col-4 values | Evidence + quantifier | P3 | YES |
| R-021 (MAH derivation) | deferred class D | DEFERRED_BY_ARCHITECTURE | `:153` in deferred; partial via `derive_mah_status()` | `test_mh_r021.py:168-175` (49 tests) | ET-081 UNKNOWN discipline; T1 SRC-016 ceilings | EXISTS/aggregation/lookup/Sch-5 | P3 | YES |
| R-022 (factory def.) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:176` + confirmation `:51`; s.85/ET-017/UNK-029 | labour-factory + establishment suites | Statutory definition, not predicate; MH proviso unverified | Evidence | P3 | YES |
| R-023 (DISH category) | deferred + conf. | DEFERRED_BY_ARCHITECTURE | `:181` + confirmation; string selector, not boolean | labour-factory suite | Category selector, not predicate | None (service-layer concern) | P3 | YES |
| R-024 (OSH est. reg.) | deferred | DEFERRED_BY_EVIDENCE | `:277` DRAFT OSH rules UR-12/UNK-008, DNI APR-017/060 | `test_mh_establishment_labour.py:115-129` | MH procedure/officer unnotified | State notification | P3 | YES |
| R-025 (S&E intimation) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:286` + confirmation; LOW T5 SRC-027 | establishment suite `:259-268` | Factory relevance unverified | Official confirmation | P3 | YES |
| R-026 | active TRIGGER | DONE | `:454` APR-019 | batch-1 + labour regression | v5 refs | None | — | N/A |
| R-027 (contractor licence) | deferred | DEFERRED_BY_EVIDENCE | `:88` contractor count fact absent | `test_mh_pack_labour_factory.py` | Applicant is occupier, not contractor | Evidence/fact | P3 | YES |
| R-028 (boiler trigger) | active TRIGGER | DONE | `:470` APR-023 | batch-1 + `test_mh_pack_batch2.py` mirror | SRC-034 s.12 | None | — | N/A |
| R-029 | DNI | NOT_APPLICABLE | DNI set, no builder | residual inventory | Do-not-implement | None | — | YES (permanent) |
| R-030 (petroleum Class-B) | STOP_UNSAFE (stay TRIGGER) per committed audit | DONE | `_r030` default TRIGGER, APR-026 uncomposed (legacy priority); SRC-092/SRC-017 refs kept | `test_mh_r030_exemption.py` (38 safety/falsification tests); APR-026 document-blocked contract live in `test_mh_consistency_sla.py`, `test_mh_api_e2e.py`, canonical scenario | SRC-092 s.7(i) genuine exemption; no active APR-026 trigger encoded (R-032/R-092 deferred) — hence retained TRIGGER per STOP verdict | Future migration needs a live s.3(2) trigger first (audit §10) | P3 | YES (safe as TRIGGER) |
| R-032 (PET form routing) | deferred | DEFERRED_BY_ARCHITECTURE | `:218-221` PET_FORM selector, not boolean | `test_mh_safety_hazardous_transport.py:92-97` | Form/authority selector | Composition primitive | P2 | YES |
| R-033 (GCR r.44 exempt) | deferred | DEFERRED_BY_EVIDENCE | `:222-227` UNK-016/039, UR-10 | safety suite | List quantifiers + LPG ambiguity | Evidence + quantifier | P3 | YES |
| R-034 (SMPV) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:228-230` + confirmation; UR-10 unread amendments | safety suite `:141-143` | EXISTS + 16-hr exclusion | Evidence + quantifier | P3 | YES |
| R-035 (MIDC branch) | active TRIGGER | DONE | `:505-510` APR-029 F-LOC-01 | batch-1 + safety suite | Branch guard verified | None | — | N/A |
| R-036 (MIDC BP combined) | confirmation-gated class C | CONFIRMATION_GATED | confirmation `:52` only; deps DEP-005/6/7 are readiness edges | `test_mh_workflow_lifecycle.py:132-140` | T3 SRC-043/044; CON-001 SLA conflict; UR-19 | Official confirmation | P2 | YES |
| R-037 (MIDC OC) | confirmation-gated | CONFIRMATION_GATED | confirmation `:52` only | `test_mh_fire_building.py:135-151,1019-1028` | Portal-only evidence | Official confirmation | P2 | YES |
| R-038 (MIDC water) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:188-197` + confirmation; RTS service, APR-034/035 conflation | `test_mh_utilities_water_power.py` | T3 portal only; UR-19 | Service vs approval boundary | P3 | YES |
| R-039 (tree felling) | confirmation-gated class C | CONFIRMATION_GATED | confirmation `:52` only; dual-target routing fork | `test_mh_midc_lifecycle_tail.py:121-160` | APR-036/042 routing unresolved | Official confirmation | P3 | YES |
| R-040 (change activity) | confirmation-gated class C | CONFIRMATION_GATED | confirmation `:52`; F-EXP-01 wrong semantics | `test_mh_midc_lifecycle_tail.py:167-215` | OPERATION/MODIFICATION unresolved | Official confirmation | P3 | YES |
| R-041 (non-MIDC BP) | deferred | DEFERRED_BY_ARCHITECTURE | `:115` no `construction` fact + R-080/082 composition; dual APR-038/041 | `test_mh_fire_building.py:358-370` | Lifecycle conflation | Fact + composition | P2 | YES |
| R-042 | confirmation-gated | CONFIRMATION_GATED | confirmation set only (fire renewal CON-013) | `test_mh_fire_building.py` | Fire renewal conflict | Evidence | P3 | YES |
| R-043 (CGWA MSE) | EXEMPTION (migrated) | DONE | `:516-526`, `role=EXEMPTION:525`, APR-043 comp | `test_mh_r044_exemption.py`; exception-semantics suites; 8/8 matrix live | SRC-052 T1; pilot verified SAFE_WITH_LIMITATION | None (sibling R-044 done) | — | N/A |
| R-044 (CGWA domestic) | EXEMPTION (migrated) | DONE | `:533-543`, `role=EXEMPTION:542`, APR-043 comp | `test_mh_r044_exemption.py` (truth-table + readiness + handoff) | SRC-052 T1 exemption 6; ET-038 | None | — | N/A |
| R-046 | active TRIGGER | DONE | `:547` APR-044 | batch-1 suite; UNKNOWN-token regression | v5 refs | None | — | N/A |
| R-048 (electrical) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:195` + confirmation; F-ELE-02 UNK-005; 11kV inapplicable per ET-050/101 | utilities suite | CEI RTS cites superseded 2010 regs | State threshold notification | P3 | YES |
| R-049 | confirmation-gated | CONFIRMATION_GATED | confirmation set only | residual inventory | Unresolved | Evidence | P3 | YES |
| R-050 (package marking) | deferred | DEFERRED_BY_ARCHITECTURE | `:83-84` | `test_mh_controlled_substance_cluster.py:234-237` | Marking duty, not approval | None | P3 | YES |
| R-051 (AAI height) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:238-242` + confirmation; 3D GIS OLS/CCZM absent | `test_mh_sector_specific.py:107-115` | Spatial datasets unmodeled | GIS layer (out of scope) | P3 | YES |
| R-052 (CETP) | deferred + conf. + UNKNOWN | DEFERRED_BY_EVIDENCE | `:201` + confirmation + UNKNOWN `:65`; `source_id: -` | utilities suite; ET-055 | No statutory source; estate facts absent | Evidence | P3 | YES |
| R-053 (WRD water) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:207` + confirmation; legal basis "Not researched"; UR-17 | utilities suite | T3 MAITRI only | Legal research | P3 | YES |
| R-054 (EC expansion) | deferred class D | DEFERRED_BY_ARCHITECTURE | `:159`; 6-conjunct, 4 unmodeled; partial encoding proven fail-OPEN by probe | `test_mh_r054.py` (34 tests) | T1 SRC-001 suffices (not evidence-blocked); APPLIES would invert exemption | Conjunction + holder primitives | P3 | YES |
| R-055 (consent amend/fresh) | deferred | DEFERRED_BY_ARCHITECTURE | `:267` categorical AMENDMENT/FRESH, APR-053 | `test_mh_cto_renewal.py:413-420` | Workflow layer, not predicate | Change-assessment layer | P3 | YES |
| R-056 | active TRIGGER | DONE | `:557` APR-054 | batch-1 suite | v5 refs | None | — | N/A |
| R-057 | confirmation-gated | CONFIRMATION_GATED | confirmation set only (MSME bands feed derivation) | `test_mh_derivations.py` uses bands | Derivation only | None (derivation live) | — | YES |
| R-058 | DNI | NOT_APPLICABLE | DNI set | residual inventory | Annexure not digitised (F-INC-04 never produced) | None | — | YES (permanent) |
| R-059 | hygiene DNI-as-rule | NOT_IMPLEMENTED | In NO set (allowlist-only) | `test_mh_residual_hygiene.py:90-97`; `test_mh_hygiene_closure.py:67-69` | Terminal documentary hygiene | None (intentional) | — | YES (terminal) |
| R-060 (MSIHC duty) | deferred | DEFERRED_BY_ARCHITECTURE | `:106` EXISTS unsupported | `test_mh_pack_location_cluster.py:331-332` | General duty r.4(1) | Quantifier | P3 | YES |
| R-061 (MSIHC 500m) | deferred | DEFERRED_BY_ARCHITECTURE | `:108` spatial aggregation unsupported | location suite `:334-335` | Multi-site computation | Spatial primitive | P3 | YES |
| R-062 (CTO validity) | deferred | DEFERRED_BY_ARCHITECTURE | `:230-234` lifecycle validity, not predicate; UNK-032 | safety suite `:144-148` | Grant-date fact absent | Validity layer | P3 | YES |
| R-063 (CTO outer limit) | deferred + conf. | DEFERRED_BY_ARCHITECTURE | `:273` + confirmation; SLA-036 timeline, UNK-031/GSR-11 | `test_mh_cto_renewal.py:422-429` | SLA display, not applicability | None | P3 | YES |
| R-064 | deferred | DEFERRED_BY_EVIDENCE | `:85` truncated + UNK-033 scope op | `test_mh_ec_core.py:191-194` | Scope unresolved | Evidence | P3 | YES |
| R-065/066 (controlled) | deferred | DEFERRED_BY_ARCHITECTURE | `:87-90` list quantifiers/lookup | `test_mh_controlled_substance_cluster.py` | List iteration unrepresentable | Quantifier | P3 | YES |
| R-067 | active TRIGGER | DONE | `:566` APR-055 | batch-1 suite | v5 refs | None | — | N/A |
| R-068 (drugs licence) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:243-248` + confirmation; chemicals ≠ drugs; UNK-036/UR-11 | sector suite `:117-126` | Form nos. unextracted | Evidence | P3 | YES |
| R-069 (explosives) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:249-253` + confirmation; peso_gating expert input | sector suite `:128-137` | Thresholds/geometry unextracted | Evidence | P3 | YES |
| R-070 | active TRIGGER | DONE | `:575` CMP-018 | batch-1 + labour regression | v5 refs | None | — | N/A |
| R-071 | hygiene date-gate | NOT_IMPLEMENTED | In NO set | residual `:84-86`; closure doc | Documented hygiene | None (intentional) | — | YES (terminal) |
| R-072 | hygiene DNI-twin | NOT_IMPLEMENTED | In NO set (CMP-014 DNI) | residual `:97-99` | Audit assigned-only, not blanket | None (intentional) | — | YES (terminal) |
| R-073 (BOE) | active TRIGGER | DONE | `:625` APR-023 F-BLR-06>1000 | `test_mh_pack_batch2.py` | SRC-085 T1; eff. 2025-09-23 | None | — | N/A |
| R-074 | confirmation + UNKNOWN | CONFIRMATION_GATED | confirmation `:54` + UNKNOWN `:65`, not deferred/safe-gated | `test_mh_ec_core.py:209-213` | Unresolved | Evidence | P3 | YES |
| R-075 | — (no builder) | DEFERRED_BY_ARCHITECTURE | Rejected at planning (no EC-date fact, no DATE arithmetic) | `test_mh_pack_batch2.py` pins absence | Date dimension has no fact | DATE primitive | P3 | YES |
| R-076 | hygiene deadline-facet | NOT_IMPLEMENTED | In NO set | residual `:122-124` | Owned facet (deadline engine) | None (intentional) | — | YES (terminal) |
| R-077 (CGWA OE) | active TRIGGER | DONE | `:673-688` APR-043; named trigger in comp `:770` | location suite `:98-210`; canonical GW-triple flip | SRC-052 T1 eff. 2020-09-24 | None (final architectural resolution = keep TRIGGER; composition complete) | — | N/A |
| R-078 (fire authority) | deferred | DEFERRED_BY_ARCHITECTURE | `:118` FIRE_AUTHORITY string CASE (mirrors R-047) | planning-fire + fire-building suites | Routing, not predicate | None | P3 | YES |
| R-079 (Schedule-I) | deferred | DEFERRED_BY_ARCHITECTURE | `:120` needs non-MIDC guard + R-078/R-042 | fire-building suite (no-overapply J-test) | Standalone over-applies to MIDC | Composition | P3 | YES |
| R-080 (BP authority) | deferred | DEFERRED_BY_ARCHITECTURE | `:124` BP_AUTHORITY CASE (mirrors R-047) | planning-fire + fire-building | Routing, not predicate | None | P3 | YES |
| R-081 (deemed BP) | deferred class E | DEFERRED_BY_ARCHITECTURE | `:299` DATE arithmetic over absent dates; register forbids grant | `test_mh_workflow_lifecycle.py:116-130` | Workflow consequence | DATE + timestamps | P3 | YES |
| R-082 (UDCPR) | deferred | DEFERRED_BY_ARCHITECTURE | `:126` regime selector; exclusion ≠ DOES_NOT_APPLY (ET-119) | fire-building (R-082-no-negation) | Selector, not predicate | None | P3 | YES |
| R-083 (CRZ) | active TRIGGER | DONE | `:693` LOC-CRZ | location suite `:212-244` | SRC-112 T1 eff. 2019-01-18 | None | — | N/A |
| R-084 (forest) | active TRIGGER | DONE | `:704` LOC-FOREST | location suite `:247-278` | SRC-113 T1 eff. 2023-12-01 | None | — | N/A |
| R-085 (NBWL) | deferred | DEFERRED_BY_ARCHITECTURE | `:110` EC_REQUIRED precondition has no fact | location suite `:328-329` | Cannot be inferred | EC precondition fact | P3 | YES |
| R-086 (boiler reg.) | active TRIGGER | DONE | `:638` APR-023 + NOT_REGISTERED; mirror-pins R-028 | batch2 suite | SRC-034 s.12 eff. 2025-05-01 | None | — | N/A |
| R-087 (boiler deemed) | active TRIGGER (staging) | DONE | `:659-665` APR-023, no role override = TRIGGER | batch2 suite; `test_mh_r030_exemption.py:161-183` pins APR-023/AUT-007 | SRC-034 s.45(2) eff. 2025-05-01 | Migration to EXEMPTION is the planned next task (triggers R-028/R-073/R-086 exist, no deficit) | P1 | N/A (active; migration pending) |
| R-088 | — (no builder) | DEFERRED_BY_ARCHITECTURE | No event facts | batch2 suite pins absence | Event dimension absent | Event facts | P3 | YES |
| R-089 | active TRIGGER | DONE | `:594` APR-022 | batch-1 suite | v5 refs | None | — | N/A |
| R-090 (BOCW) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:185` + confirmation; s.2(1)(h) exclusion, ET-126 UNKNOWN | labour-factory suite | Legal interpretation unresolved | Legal resolution | P3 | YES |
| R-091 (MAH join) | deferred (partial via derivation) | PARTIAL | `:112` deferred as ApprovalRule; `derive_mah_status()` live in `rules/derivations.py` (M3-M7-M9) | location suite `:337-382` | M2 identity + CON-021 thresholds unconfirmed | Identity resolution + thresholds | P2 | YES (derivation covers demo path) |
| R-092 (PET r.144 NOC) | deferred | DEFERRED_BY_ARCHITECTURE | `:235-237` needs R-032 composition | safety suite | Cannot evaluate standalone | R-032 first | P2 | YES |
| R-093 | active TRIGGER | DONE | `:604` CMP-024 | batch-1 suite | v5 refs | None | — | N/A |
| R-094 (e-waste bulk) | active TRIGGER | DONE | `:612-619` CMP-025 F-EEE-01≥1000 | `test_mh_environmental_epr.py:137-143,393-411` | EEE-producer branch correctly unmodeled | None | — | N/A |
| R-095 (ODS r.8) | deferred | DEFERRED_BY_ARCHITECTURE | `:254-258` CND-022 RULE_LOGIC, not APR-xxx | sector suite `:139-146` | Condition/registration, not approval | None | P3 | YES |
| R-096 (HW Sch-II) | active TRIGGER | DONE | `:715-717` APR-010 | location suite `:281-321` + HW-chain `:311-382` (UNK-034/[]/token bounds) | SRC-120 T2 | None | — | N/A |
| R-097 (GW deep-well) | deferred + conf. | DEFERRED_BY_EVIDENCE | `:212` + confirmation; CND-024 prohibition, not application; 80-watershed GIS absent (UR-15) | utilities suite; ET-v5-24 fail-closed | Village list unencoded | GIS + order currency | P3 | YES |
| R-098 (Mathadi) | deferred + conf. | DEFERRED_BY_ARCHITECTURE | `:292-298` + confirmation; CND-025 RULE_LOGIC, not APR-xxx | establishment `:273-285` | Board scheme data unmodeled | Area-specific data | P3 | YES |
| R-099 (fire renewal) | deferred class E | DEFERRED_BY_ARCHITECTURE | `:306` renewal/lifecycle, never APPLIES | `test_mh_workflow_lifecycle.py:124-130` | Lifecycle layer | None | P3 | YES |
| R-100/101/102 | — (no builder) | DEFERRED_BY_EVIDENCE | No licence-held fact (SSC-01..03) | batch2 suite pins absence | Licence dimension absent | Licence facts | P3 | YES |
| R-103 | — (no builder) | DEFERRED_BY_EVIDENCE | No new-licence/date facts; gas-only over-applies (ET-v5-12) | batch2 suite | Date dimension absent | Date + licence facts | P3 | YES |
| R-104 | — (no builder) | DEFERRED_BY_EVIDENCE | No licence/purpose/filling-plant facts | batch2 suite | Purpose dimension absent | Purpose facts | P3 | YES |
| R-105 (zone permiss.) | deferred | DEFERRED_BY_ARCHITECTURE | `:259-261` PS-02 planning gate; CONDITIONAL/INSUFFICIENT_DATA per ET-v5-21/22 | sector suite `:148-158` | DP/RP zoning unmodeled; composes with deferred planning rules | Zoning data | P3 | YES |

### 1B. Semantic migrations

| Item | Historical Status | Actual Current Status | Code Evidence | Test Evidence | Regulatory Evidence | Remaining Work | Priority | Safe to Leave Deferred? |
|---|---|---|---|---|---|---|---|---|
| S-R002 CLASSIFICATION | migrated | DONE | `approvals.py:391`; comp `:773-776` | ec-core `:285-355`; exception suites | Informational-only intent | None | — | N/A |
| S-R043 EXEMPTION | migrated, SAFE_WITH_LIMITATION | DONE | `:525`; APR-043 comp | 8/8 matrix; readiness/handoff proven | SRC-052 | None | — | N/A |
| S-R044 EXEMPTION | migrated | DONE | `:542`; APR-043 comp | `test_mh_r044_exemption.py` (truth-table + readiness + handoff) | SRC-052 exemption 6 | None | — | N/A |
| S-R030 EXEMPTION | STOP_UNSAFE_TO_MIGRATE, RETAIN TRIGGER (committed audit) | DONE | R-030 stays default TRIGGER; APR-026 uncomposed — code matches the STOP verdict, no migration performed | `test_mh_r030_exemption.py:235-273` proves hypothetical triggerless composition would collapse to INSUFFICIENT_DATA (falsification, not live behavior); live APR-026 contract is document-blocked | SRC-092 genuine; trigger deficit real (R-032/R-092 deferred) | Future migration per audit §10 (live trigger first) | P3 | YES |
| S-R087 EXEMPTION | planned next (active triggers exist) | NOT_IMPLEMENTED | Still TRIGGER `:659-665`; staging comment `:759` | Pins APR-023/AUT-007 (`r030:161-183`) | SRC-034 s.45(2)(f) deemed-registration | Migration under APR-023 (R-028/R-073/R-086 triggers present) | P1 | YES (safe as TRIGGER) |
| S-R077 resolution | final resolution after R-087 | DONE | TRIGGER + named in APR-043 comp `:770`; "not migrated" comment `:758-759` is stale wording, code unambiguous | location + canonical GW-triple | SRC-052 | None (keep TRIGGER) | — | N/A |
| S-R035 | stay TRIGGER per staging | DONE | Default TRIGGER `:505-510` | batch-1 + safety suites | MIDC branch guard | None | — | N/A |

### 1C. Approval compositions (all in `mh/approvals.py:767-784`, served via `pack.py:165-167,232`)

| Item | Historical Status | Actual Current Status | Code Evidence | Test Evidence | Regulatory Evidence | Remaining Work | Priority | Safe to Leave Deferred? |
|---|---|---|---|---|---|---|---|---|
| CMP-APR-043 (T:R-077 E:R-043,R-044) | implemented | DONE | `:768-772`; disjoint-validated (`models.py:463-494`) | 8/8 R-043 matrix; R-044 truth-table; canonical GW flip | All refs same-jurisdiction, roles match builders | None | — | N/A |
| CMP-APR-001 (C:R-002) | implemented | DONE | `:773-776`; composes to INSUFFICIENT_DATA by design (`applicability.py:804-814`) | ec-core `:288-323` | R-001 deferred, no trigger yet | R-003-pattern consumer (needs composition primitive) | P2 | YES (fail-closed by design) |
| APR-026 legacy (R-030 TRIGGER, uncomposed) | uncomposed (legacy priority) | DONE | No APR-026 entry in `MH_APPROVAL_COMPOSITIONS`; R-030 TRUE → APPLIES, DOC-008 blocks readiness | document-blocked contract in consistency/e2e/canonical suites | Petroleum licence duty intact (no duty erasure) | None (future trigger + migration per audit §10) | P3 | YES |
| Legacy (APR-023 ×4 TRIGGER, APR-010 ×2 TRIGGER, rest single) | preserved | DONE | `summarize_by_approval` legacy path `applicability.py:599-603` | No legacy regression (2348 green) | R-087-as-trigger yields APPLIES like any trigger (documented staging) | None | — | N/A |

### 1D. Subsystems

| Item | Historical Status | Actual Current Status | Code Evidence | Test Evidence | Regulatory Evidence | Remaining Work | Priority | Safe to Leave Deferred? |
|---|---|---|---|---|---|---|---|---|
| Fact ontology (128 MH facts) | 128 active | DONE | `rules/facts.py:455` MH_FACTS; F-BLD-02 excluded `:458-460`; UNKNOWN→None fail-closed | `test_mh_facts.py:28-35`; `test_unknown_token_fail_closed.py` | CSV↔registry exact, zero drift | Incentive-pack facts; frontend MH vocabulary | P2 | YES (core done) |
| Derivations (F-INC-01, F-PRC-03) | wired | DONE | `rules/derivations.py`; single wiring `orchestration/facts.py`; provenance on `ApplicationOrchestration.fact_provenance` | `test_mh_derivations.py` (39); `test_mh_derivation_wiring.py` (18) | R-057 bands verbatim; R-091 join; F-INC-03/04 never produced | None | — | N/A |
| Readiness/dependency engine | implemented | DONE | `dependency_engine.py:178-343` (DFS/Kahn/longest-path); MH edges DEP-009×2 only (`mh/dependencies.py:74-97`); DEP-019 YES_INFERRED deferred | 41 engine tests + MH suites; exempt-cannot-satisfy proven (`r030:384-414`, `r044:372-403`) | APR-008/009 have no batch rules → block until obtained (engine-correct) | None | — | N/A |
| Documents/readiness | implemented | DONE | `orchestration/service.py:69-266`; MH DOC-001/002/003→APR-010, DOC-008→APR-026 | canonical APR-010 READY journey | Verified URLs from sources.csv | None | — | N/A |
| Handoff (truthful bookkeeping) | implemented | DONE | Gate `handoff/service.py:54-56`; 409 on non-ready; no HTTP/polling/scraping `:1-6` | `test_mh_canonical_scenario.py:624-661`; `test_mh_api_e2e.py:610-647` | Portal/reference-only catalog; no MAITRI; no gov API claimed | None (backend) | — | N/A |
| What-If | implemented | DONE | `whatif.py:293-377` same-pack baseline+alt; no mutation `:130-192`; MH jurisdiction threaded | canonical 4 flips `:297-402`; `test_persisted_jurisdiction.py:436-471` | Deterministic diff | Frontend MH fields (below) | P1 | Backend YES |
| RAG/explanation boundary | implemented w/ PARTIAL wiring | PARTIAL | `explanation.py:1-9` never recalculates; `retrieval.py` tsvector only | E2E audit 9 PASS / 2 PARTIAL | MH SRC-xxx not DB-seeded → citations [] for MH; `explain_approval` uses request jurisdiction, not persisted pack; "Gujarat dataset" hardcode `:147,200` | Thread persisted pack into explain paths; seed MH sources for demo | P1 | YES for rules (no override possible); NO for demo polish |
| Source corpus | 22/188 loaded | DONE | `mh/sources.py:68-435`; 17 distinct refs cover all 26 active rules (missing=[]) | corpus/resolution tests; decisions-unchanged | 166 deferred by rule-absence, not by gap | None (by design) | — | N/A |
| Jurisdiction isolation | IN-GJ default; MH quarantined | DONE | `pack.py:74,123-136,200-256`; migration 010 additive; GJ 19 rules isolated | `test_persisted_jurisdiction.py` TEST-01..17; GJ↔MH contamination suites | N-2 zero verified A↔APR mappings (no translation attempted) | Execute migration 010 on staging; N-2 sign-off | P1 | YES (code done; ops pending) |
| Frontend journey (16 steps) | 9 PASS / 2 PARTIAL (backend) | PARTIAL | Login WORKING; docs WORKING; readiness WORKING (caveated); handoff WORKING; create-project/facts/assessment/dashboard/applicability/authority/deps PARTIAL-MISSING-BROKEN (GJ-only WhatIf fields, facts-form `upsertFacts` query-string bug `api.ts:92-93`, no MH UI) | `frontend_sih_demo_readiness.md` verified accurate; tsc 0 errors; build ok | No GJ leakage into MH paths (0 `IN-*` hits); omissions, not leaks | MH demo UI slice (create→facts→assess→dashboard→handoff) | P0 | NO — demo needs it |
| Canonical MH scenario | exists (backend) | DONE | `mh/scenario.py:33-362` (Sahyadri, Kurkumbh, ~40 F-* keys); 20 expected assessments; loaders immutable | `test_mh_canonical_scenario.py` (determinism ×10, what-if, handoff, traceability, API routes) | Facts strictly in 128-registry; no GJ leak | Frontend surfacing only | P1 | Backend YES |
| Evidence gaps (MH) | 3 advisory + hints | DONE | `mh/evidence.py` UR-06→APR-001, UR-11→APR-055, DOC-012→APR-043; evaluated-not-surfaced conflicts documented | gap-blocker suites; NOT_APPLICABLE preserved | Advisory only; never creates rules | None | — | N/A |

## TABLE 2 — Remaining work (dependency order)

| Priority | Task | Why Needed | Dependency | Exact Files/Components | Verification |
|---|---|---|---|---|---|
| P0 | T1. Resolve R-030 contradiction — COMPLETE (2026-10-02): reverted R-030 to TRIGGER, removed APR-026 composition, restored document-blocked expectations | — | — | `backend/app/seed/mh/approvals.py`; `test_mh_consistency_sla.py`; `test_mh_api_e2e.py`; `test_mh_canonical_scenario.py`; `test_mh_exception_semantics.py`; `mh/scenario.py` (expected outcomes only, facts untouched) | Full suite 2348 green; code matches STOP audit |
| P0 | T2. Commit the working tree (or deliberate squash) | SIH demo/fresh-session continuity depends on it; all evidence currently uncommitted | T1 (commit only green) | `git add` per paths in §0; keep `data/uploads/` ignored | `git log` shows reconciliation commit; `pytest -q` green on clean checkout |
| P0 | T3. MH demo UI slice: project create → MH facts entry → run assessment → approval dashboard → per-approval reason/authority/docs/deps → readiness → handoff | Backend demo path is complete but unreachable from UI (GJ-only fields, facts bug, no assessment entry point) | T2 | `frontend/src/components/WhatIfPanel.tsx:19-71`; `frontend/src/pages/applicant/ProjectDetailPage.tsx`; `frontend/src/lib/api.ts:92-93,97-100`; new MH assessment/dashboard components | Manual 16-step journey against canonical scenario; tsc+build |
| P1 | T4. R-087 deemed-registration migration under APR-023 | Next planned migration; triggers exist so no deficit invariant applies | T1 (composition discipline settled) | `mh/approvals.py` `_r087` + APR-023 composition; new `test_mh_r087_exemption.py` | Truth-table + readiness + handoff + GJ regression; suite green |
| P1 | T5. Thread persisted pack into regulatory explain paths + seed MH sources for demo citations | MH explanations currently return `citations:[]`; "Gujarat dataset" hardcode | T2 | `backend/app/api/regulatory.py:130-220`; `backend/app/regulatory/explanation.py:147,200`; MH source seeding | MH explanation returns traceable MH citations; E2E audit 11/11 |
| P1 | T6. Execute migration 010 on staging + N-2/resign-off pack | Live-DB path unverified; N-2 zero mappings blocks any default-flip discussion | T2 | `supabase/migrations/010_persisted_jurisdiction.sql`; staging Supabase | Backfill gates green on hosted staging |
| P2 | T7. R-013/R-014/R-015 consent-category chain (lookup + composition primitives) | Unlocks R-017 CTO + R-092 chain; biggest approval-coverage gain | T4 (composition pattern proven) | New lookup primitive in `rules/`; sector table digitization; consent-chain tests | R-013/R-014 activate with MAX-convention prohibition intact |
| P2 | T8. R-091 full rule (M2 identity + CON-021 thresholds) | Closes largest PARTIAL | Evidence: M2 resolution, thresholds | `rules/derivations.py` + `_r091` + composition | MAH derivation end-to-end |
| P2 | T9. APR-001 R-003-pattern consumer (EC category composer) | Turns APR-001 from designed-INSUFFICIENT_DATA into decisive | Composition primitive | `mh/approvals.py` + composer | EC small/large both decisive with sources |
| P3 | T10+. Engine primitives (EXISTS/aggregation/DATE/event/GIS) + R-054/R-021 class-D activations + EPR/compliance-duty layering | Future coverage; each needs its primitive first | Per-row deps in Table 1 | `rules/models.py`, `rules/applicability.py`, register digitization | Per-cluster suites; never activate without evidence |

Regulatory-evidence gaps are NOT coding tasks (T7–T10 list the code side only where a primitive is genuinely missing).

## TABLE 3 — DO NOT TOUCH (already correct; regression test listed)

| Item | Reason | Evidence | Regression test |
|---|---|---|---|
| R-002 CLASSIFICATION + APR-001 composition | Migrated, reasoned-defeat + honest-INSUFFICIENT_DATA verified | `approvals.py:379-392,773-776` | `test_mh_ec_core.py:285-355` |
| R-043/R-044 EXEMPTION + APR-043 composition | Pilots verified SAFE (8/8 matrix; readiness/handoff) | `:516-543,768-772` | `test_mh_r043` matrix; `test_mh_r044_exemption.py` |
| R-077 TRIGGER in APR-043 | Final resolution is keep-TRIGGER; stale comment only | `:673-688,770` | `test_mh_pack_location_cluster.py:98-210` |
| R-035 TRIGGER | Staging-correct branch guard | `:505-510` | batch-1 suite |
| R-018/R-096 + UNKNOWN fail-closed fix | HW chain falsification-proof; list-UNKNOWN→INSUFFICIENT_DATA | `_evaluate_leaf` `in`-branch; `:442,715` | `test_mh_hazardous_waste_authorization_chain.py:345-357` |
| 61 deferred + `_encode` fail-closed gate | Every deferred rejects before safe/confirmation checks | `:75-313,354-355` | All cluster suites pin exclusion |
| 4 hygiene (R-059/071/072/076) in no set | Terminal documentary closure; allowlist-only | Absent from all sets | `test_mh_residual_hygiene.py`; `test_mh_hygiene_closure.py` |
| Legacy aggregation for uncomposed approvals | Byte-identical GJ behavior; unmigrated approvals cannot shift | `applicability.py:599-603` | Full suite (2345 green) |
| Exempt-cannot-satisfy / NA-cannot-ready / non-ready-cannot-handoff | Proven invariants | `service.py:251-252`; `handoff/service.py:54-56` | `r030:384-414`; `r044:372-403`; canonical `:624-661` |
| GJ pack (19 rules) + IN-GJ default + persisted identity | Isolation structural; default untouched | `pack.py:74`; migration 010 | `test_persisted_jurisdiction.py`; GJ baselines |
| RAG-behind-rules boundary | Retrieval can never override applicability | `explanation.py:1-9` | E2E audit; exception suites |
| Canonical scenario facts/expectations | Frozen demo fixture; loaders immutable | `mh/scenario.py` | `test_mh_canonical_scenario.py` (×10 determinism) |

## TABLE 4 — Parallel work map

PARALLEL-SAFE (disjoint files, no shared semantics): T4 (R-087 migration) ∥ T5 (regulatory explain threading) ∥ T6 (staging migration ops) ∥ T3-frontend (UI slice, after T2). T7/T8/T9 are mutually parallel-safe with each other once T4 lands (different rules/compositions).
SEQUENTIAL / SHARED-CODE (do not parallelize): T2→everything (uncommitted state blocks all landings); any two tasks editing `mh/approvals.py` compositions or `rules/applicability.py` composition semantics (T4 vs T7 vs T9 share the §8 truth table — serialize); T5 vs T3-backend-contract (explain shape changes affect UI).

## Final output

1. EXECUTIVE STATUS: Overall — 27 DONE (26 active rules incl. R-030 as STOP-approved TRIGGER, all with code+tests+evidence) · 3 DONE (migrations R-002/R-043/R-044) · 1 PARTIAL (R-091 derivation) · 61 DEFERRED (fail-closed, safely leavable) · 11 CONFIRMATION_GATED · 3 NOT_APPLICABLE (DNI) · 4 NOT_IMPLEMENTED-terminal (hygiene) · subsystems: 9 DONE, 2 PARTIAL (RAG wiring, frontend journey) · 0 BLOCKED on correctness.
2. CURRENT RULE COUNTS: active 26 · deferred 61 · confirmation-gated 26 (set size; 15 overlap deferred, 11 confirmation-only) · DNI 3 · UNKNOWN 3 (R-015 deferred, R-052 deferred, R-074 confirmation-only) · untriaged 0 · hygiene-terminal 4 · inventory 26+61+11+3+4 = 105 exact.
3. SEMANTIC ROLE INVENTORY (from code): TRIGGER 23 · EXEMPTION 2 (R-043, R-044) · CLASSIFICATION 1 (R-002). R-030 was never migrated — it stays TRIGGER per the STOP verdict.
4. COMPLETED TASKS (proven by code + tests): fact ontology 128 + UNKNOWN fix; derivations + wiring + provenance; batch-1/batch-2/location-cluster 26 rules; 61-rule deferral gate; R-002/R-043/R-044 migrations with compositions; R-030 STOP-verdict restoration (TRIGGER, APR-026 document-blocked); readiness/dependency/docs/handoff/What-If/jurisdiction/evidence-hints/canonical-scenario; all clusters A–O audited with artifacts (proof: 2348 green).
5. PARTIAL TASKS: (a) R-091 — derivation live, ApprovalRule deferred → needs M2/threshold evidence (T8). (b) RAG/MH citations — boundary correct, MH surfacing stub → T5. (c) Frontend MH journey — backend complete, UI GJ-only → T3.
6. DEFERRED TASKS: all 61 + 11 confirmation-only + R-087-as-TRIGGER staging — each has a Table-1 row with fail-closed rationale; all safe to leave through the SIH final demo.
7. BLOCKING TASKS (real blockers only): T2 (uncommitted everything — this commit); T3 (no MH UI path for demo). Nothing else blocks correctness or demo.
8. FINAL SIH DEMO GAPS: (i) frontend cannot yet drive the MH canonical scenario end-to-end (T3); (ii) MH regulatory explanations show no citations (T5, cosmetic); (iii) staging migration (T6, ops). Backend decision path itself is demo-ready.
9. NEXT TASK (after T2 commit): T3 MH demo UI slice; T4 (R-087, triggers present) ∥ T5 (MH citations) ∥ T6 (staging migration) are parallel-safe.
10. PARALLEL TASKS: after T2 — {T4} ∥ {T5} ∥ {T6} ∥ {T3}; then {T7} ∥ {T8} ∥ {T9}.
11. DO-NOT-TOUCH LIST: Table 3 (12 entries) — especially R-002/R-043/R-044/R-077/R-035 roles, the 61-deferred gate, hygiene absence, legacy aggregation, GJ isolation, and the frozen canonical scenario.
12. CURRENT TEST STATUS: `pytest tests/ -q` → 2348 passed, 0 failed; focused hygiene/inventory 52 passed; `tsc --noEmit` 0 errors; `ruff` 20×E501 confined to two untracked test files (`test_mh_canonical_scenario.py`, `test_mh_r030_exemption.py`), none on touched lines; `vite build` per last committed record success (frontend files unmodified).
13. REGULATORY EVIDENCE STATUS: every active rule resolves (17 distinct source_refs, missing=[]); corpus 22/188 by design (166 deferred with their rules); 3 advisory MH gaps (UR-06/UR-11/DOC-012) + documented non-surfaced conflicts; N-2 zero verified A↔APR mappings (no translation attempted or allowed); Gaps that are pure evidence (WRD basis, CETP source, MSIHC col-4, Mathadi schemes, AAI GIS, drug forms) stay evidence work, not code.
14. FILES MODIFIED (this report): R-030 STOP restoration (T1: `mh/approvals.py` role/composition revert + downstream expectation restores in 4 test files + `mh/scenario.py` expected outcomes only) and this T2 status correction. Full change set vs HEAD `226879f`: exception-semantics layer, 61-rule deferral gate, 26-rule MH pack, derivations, canonical scenario, cluster audits + tests (see commit).
STOP: reconciliation + T1 + T2 complete. Next implementation task is T3 (MH demo UI slice), selected from TABLE 2.

STOP: no implementation started. Next implementation task is T1, selected from this report.
