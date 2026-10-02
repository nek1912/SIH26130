# Implementation Audit — P0 Exception/Exemption Semantics (MH)

First production implementation of the P0 design (`audit_mh_apr001_exception_role_design.md`, canonical copy at `docs/audits/`). No redesign: roles TRIGGER/EXEMPTION/CLASSIFICATION, §8 truth table, Option A (role field + approval composition), staged migration (R-043 pilot, then APR-001/R-002), remaining five non-trigger candidates explicitly unmigrated, R-054 not activated. Implemented jointly in one working tree (role/composition infrastructure, contract tests, re-pins, readiness proofs); this record covers the union as verified green.

## 1. Design contract implemented

TRIGGER default (byte-compatible); EXEMPTION duty-defeat (TRUE never APPLIES, FALSE no-info, UNKNOWN blocks APPLIES, defeat only via explicit composition with a TRUE trigger, reason retained); CLASSIFICATION informational (never decisive alone, named-composition consumption only; R-002 migrates here, not to EXEMPTION — Cat B still attaches). GUARD/ROUTING/LIFECYCLE/WORKFLOW excluded. §8 rows implemented verbatim, including T=FALSE,E=any → no duty; T=TRUE,E=UNKNOWN → CONDITIONAL; T=UNKNOWN,E=TRUE → insufficient/blocked, never APPLIES. No invert flags, name-inference, NOT-exemptions, or LLM roles.

## 2. Semantic representation

`RuleRole` StrEnum + `ApprovalRule.role = TRIGGER` default (`app/rules/models.py`); `ApprovalComposition` (approval_id + triggers/exemptions/classifications, pairwise-disjoint validator); `_encode(..., role=TRIGGER)` passthrough (`app/seed/mh/approvals.py`); `MH_APPROVAL_COMPOSITIONS` naming APR-043 (triggers R-044/R-077, exemptions R-043) and APR-001 (classifications R-002, triggers empty) with built-ID validation; `RegulatoryPack.approval_compositions` (default {}, GJ empty). Roles are per-rule seed data, never inferred.

## 3. Composition behavior

`compose_approval_evaluations` (`app/rules/applicability.py`): named-list partition (§8 function); missing named rule → explicit unknown pressure (never silent); all-trigger composition byte-identical to legacy priority (FALSE still dominates UNKNOWN among triggers); defeat yields DOES_NOT_APPLY with "Exempt under {id}: {reason}; trigger {id} would otherwise apply." `summarize_by_approval` gains optional `compositions` (absent → legacy path untouched). No new result vocabulary; synthetic evaluations reuse `ApplicabilityEvaluation` with unioned inputs and decisive-rule provenance. Orchestration (`service.py`), What-If, rehearse (`RehearsalInputs` field), and handoffs all thread pack compositions (optional params, default None → legacy).

## 4. Compatibility proof

Defaults-green run with infrastructure in place and zero role/composition changes: full suite green, zero behavior delta (result/reason/inputs/readiness/orchestration/dependencies identical — nothing to compare because nothing moved). GJ: all 19 rules default TRIGGER, empty compositions; GJ suites green, behavior byte-identical. DB-backed `ApprovalRule` construction (`api/approvals.py`) uses the default. No API shape change (wire carries evaluations/results, never rule objects) — frontend untouched.

## 5. R-043 migration

`_r043` → `role=EXEMPTION` (predicate/sources/dates unchanged). APR-043 composition: triggers R-044/R-077 (still TRIGGER, unmigrated per staging), exemptions R-043. MICRO+domestic facts now compose to DOES_NOT_APPLY with exemption reason (was legacy APPLIES); rule-level R-043 TRUE pins stand (evaluate_rule untouched). Re-pinned deliberately: derivation orchestration/handoff/whatif/impact APR-043 expectations + reason assertion. Readiness: defeat → NOT_APPLICABLE, never READY; defeated APR-043 satisfies no downstream edge as "obtained" (obtained-set untouched; no loaded edges reference APR-043).

## 6. APR-001 migration

`_r002` → `role=CLASSIFICATION` (predicate/sources/dates unchanged). APR-001 composition: triggers [] (R-001 deferred), classifications [R-002]. Small-unit facts (and not-small facts) now compose to INSUFFICIENT_DATA — the EC audit's fail-OPEN defect (large unit → "EC does not apply") and overstatement (small → "EC applies") are both closed to honest unknown with R-001/R-003 still deferred. R-003 consumes nothing yet (still deferred — no invented composition consumer). Re-pinned deliberately: EC-core small/large approval-level tests, derivation R-002 orchestration test, consistency/SLA, sources/portals, and e2e APR-001 expectations (statuses/blockers unchanged; rule-level R-002 boundary pins stand).

## 7. Readiness impact

Defeat surfaces as `does_not_apply` → `_determine_status` → NOT_APPLICABLE (existing mapping, unchanged): defeat can never reach READY, so `prepare_initiation`'s READY-only handoff gate stays closed for exempted approvals — the pre-migration hole (exemption TRUE → applies → READY → handoff) is shut. UNKNOWN defeater → CONDITIONAL → INSUFFICIENT_DATA status (non-READY). Classification-only → INSUFFICIENT_DATA (non-READY). DEP-009 BLOCKED behavior for APR-010 preserved (existing pins green). `does_not_apply` prerequisites satisfy downstream edges as "not needed" (pre-existing dependency semantics, unchanged) — with no loaded edges touching APR-001/APR-043/APR-052, the defeated approvals affect no graph paths.

## 8. Test matrix

19-row contract (`test_mh_exception_role_contract.py`: 25 tests incl. legacy-untouched pin) + direct compose-level duplicate coverage (`test_mh_exception_semantics.py`, parallel session) + role lint (EXPECTED_ROLES 26-map; non-trigger ⊆ composed; composed sets exact vs built rules with role agreement; pack serves seed dict; GJ empty) + migration re-pins (EC-core, derivation ×4, consistency, sources, e2e) + pre-existing readiness pins. 19-row mapping: rows 1-3/legacy trigger behavior; 4-9 exemption polarity; 10-15 combination matrix; 16-17 classification; 18-19 readiness protection. Full suite: 2225 passed, 0 failed at record time.

## 9. Remaining non-trigger rules

Explicitly unmigrated per staging (still default TRIGGER, legacy behavior, pinned by the EXPECTED_ROLES lint so a future migration must update the map deliberately): R-030 (Class-B exemption), R-044 (domestic exemption), R-087 (deemed-registered), R-035 (branch guard, TRIGGER-compatible), R-077 (collapsed trigger+block, needs split-or-grandfather mini-audit). R-044 shares APR-043's composition as an unmigrated trigger — its eventual EXEMPTION migration needs no composition change.

## 10. R-054 status

Not activated (missing facts unresolved, per its audit). Receives no semantic infrastructure beyond the generally available roles/composition (behavior-neutral for it: no builder, no composition entry, no evaluation path). Its future migration fits EXEMPTION + Form-I else-routing when evidence lands.

## 11. Known limitations

Two parallel sessions implemented convergently in one tree (role/composition data + readiness/handoff proofs vs infra/contract/re-pins here); union verified green but cross-review the seam (`compose_approval_evaluations` single implementation — no duplication occurred). `roles` parameter was removed from `summarize_by_approval` during implementation (named lists suffice; lint covers consistency). Unnamed rules of a composed approval are ignored at runtime (lint enforces exact coverage instead). Exemption reason text is register-agnostic (rule_id + rule reason; no legal-citation templating). No dedicated EXEMPT terminal status (DOES_NOT_APPLY+reason suffices for phase 1; open question 2 in design).

## 12. Next migration candidate

R-044 (domestic exemption, same APR-043 composition — data-only role flip + re-pin, no composition change; smallest possible next step). Then R-030, R-087 with fresh pins; R-077 split-or-grandfather decision last. After that: R-003-pattern named consumption (needs R-001/R-003 evidence, still deferred) and the hygiene code-triage follow-up — all blocked on evidence, not on this infrastructure.
