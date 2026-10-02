# Post-Migration Falsification Audit — P0 Exception Semantics

Verification-only audit of the live P0 implementation (role model +
§8 composition + R-043 pilot + APR-001 migration). No production code,
facts, rules, schemas, APIs, frontend, or behavior modified here; one
defect hunt executed, none found. Date (UTC): 2026-09-29. Baseline
verified first: MH active 26, deferred 61, confirmation 26, facts 128,
GJ 19, DEFAULT_JURISDICTION IN-GJ, R-002 CLASSIFICATION, R-043
EXEMPTION, R-054/R-001/R-064/R-074 deferred/held as audited.

## 1. Baseline

Code-executed at audit time: 26 active (roles: 24 TRIGGER + R-002
CLASSIFICATION + R-043 EXEMPTION), 61 deferred, 26 confirmation, 3
DNI, 3 UNKNOWN, 128 facts, GJ 19 (all TRIGGER), untriaged 4
(documented hygiene: R-059/071/072/076). Suite green on entry; every
probe below re-derived from live code/pack (temp scripts, zero repo
trace) plus the pinned suites.

## 2. Role inventory

TRIGGER (24): R-007/009/011/012/018/026/028/030/035/044/046/056/067/
070/073/077/083/084/086/087/089/093/094/096. EXEMPTION (1): R-043.
CLASSIFICATION (1): R-002. GJ (19): all TRIGGER. Assignment sites in
`app/seed/mh/approvals.py`: `_encode` default + passthrough + exactly
two explicit `role=` (R-002, R-043) — verified by source scan; no
inference from name/description/predicate/approval/polarity anywhere.
Lint (`EXPECTED_ROLES` 26-map in contract tests) forces explicit
listing of any new builder. R-030/R-044/R-087/R-035/R-077 remain
explicitly TRIGGER per staging (lint-pinned, not overlooked).

## 3. Composition inventory

`MH_APPROVAL_COMPOSITIONS`: APR-043 (triggers R-044/R-077, exemptions
R-043) and APR-001 (classifications R-002, triggers empty). Verified:
both approval IDs exist; all named IDs built in-pack; groups
pairwise-disjoint (model validator); same-jurisdiction (MH seed,
served only on the IN-MH pack; GJ serves {}); no orphans (every
non-TRIGGER built rule named; every composed approval's built rules
fully named with role agreement — lint-pinned). Composition is
opt-in: approvals without entries aggregate with legacy priority
(proven: identical function branch as before; legacy-untouched pin
green).

## 4. Truth-table verification

All 16 contract rows re-proven independently against live code:
T/no-E→APPLIES; T=FALSE→no duty; T unknown→INSUFFICIENT; T+T/E-FALSE→
APPLIES; T+T/E-TRUE→DOES_NOT_APPLY+"Exempt under"; T+T/E-UNKNOWN→
CONDITIONAL; T=FALSE+E-TRUE→DOES_NOT_APPLY on trigger reason (no
exemption-generated result); T-unknown+E-TRUE→insufficient (never
APPLIES); T/E both unknown→never APPLIES; E-TRUE/FALSE/UNKNOWN
alone→never APPLIES/DNA/insufficient; C-TRUE/FALSE/UNKNOWN
alone→never APPLIES/DNA (insufficient); UNKNOWN never FALSE
(token/None/missing/list-element paths); defeat vocabulary stays
inside applies/does_not_apply/conditional/insufficient_data (no new
results). Matches §8/contract in every row.

## 5. APR-001 audit

Live-pack states: small TRUE / not-small / missing / not-small+scope
/ class-UNKNOWN → all INSUFFICIENT_DATA applicability + status, never
APPLIES, never DOES_NOT_APPLY (the Cat-A fail-OPEN and the small-unit
overstatement are both closed). R-002 TRUE is not EC-exempt; R-002
FALSE is not EC-unnecessary; R-001 (deferred, no builder) remains the
only possible trigger — unresolved stays unresolved. Synthetic
E/F/G (trigger TRUE composed with class TRUE/FALSE/UNKNOWN at unit
level): INSUFFICIENT_DATA in all three — pack-level trigger-TRUE
rows are NOT_TESTABLE until R-001 evidence lands (no builder to fire
it), covered at unit level instead. No classification result reaches
READY (status INSUFFICIENT_DATA in every live state; INSUFFICIENT ≠
READY by `_determine_status`).

## 6. APR-001 downstream dependency audit

Loaded graph contains exactly DEP-009 ×2 (APR-008/009→APR-010): zero
edges touch APR-001 (DEP-002/DEP-030 correctly unloaded). No consumer
can assume APR-001 DOES_NOT_APPLY — that verdict is now unreachable
for APR-001 (proven across all five live states). INSUFFICIENT_DATA
blocks where appropriate (dependency engine PENDING on unknown
prerequisites; existing DEP-009 BLOCKED pins green). Classification
output never satisfies a prerequisite (insufficient → blocking,
pinned at engine level with a synthetic edge test).

## 7. R-043 audit

Live-pack states: T+E-TRUE→does_not_apply/NOT_APPLICABLE with
exemption reason; T-FALSE+E-FALSE→does_not_apply on trigger reason;
T+E-UNKNOWN→conditional/insufficient_data; E-alone variants (TRUE/
FALSE/UNKNOWN with triggers unknown)→insufficient_data. TRUE alone
never APPLIES; FALSE alone never DOES_NOT_APPLY; UNKNOWN blocks
APPLIES. Defeat modifies no obtained set (signature-level: obtained
comes only from terminal sibling applications); no loaded edge
references APR-043 either side, so defeat satisfies nothing
downstream; handoff gate verified closed on defeat (`is_ready_to_
handoff("not_applicable")` False; `prepare_initiation` raises —
probed end to end).

## 8. Alternate-path audit

Traced with compositions threaded and verified live: normal
orchestration ✓, what-if (both branches) ✓, rehearse/impact
(`RehearsalInputs` field) ✓, handoffs list/initiate (pack-sourced)
✓, rehearse endpoint ✓, API orchestration/what-if endpoints ✓, pack
generation (MH serves, GJ {}) ✓, direct service calls with
compositions ✓. Raw rule-level evaluations remain exposed (by design:
rule-level TRUE is preserved — the semantic boundary lives at
aggregation, and every consumer above aggregates through it). No
evaluation caches exist (no memoization in orchestration/rules).
Approval-level status is always recomputed per call. No path yields
EXEMPTION TRUE→APPLIES or CLASSIFICATION TRUE→APPLIES when
compositions are threaded (probed on all four service paths).

## 9. Legacy fallback audit

Direct calls omitting compositions follow legacy APPLIES-first
(proven: R-002 TRUE → `applies` without compositions vs
`insufficient_data` with). Reachability: all production callers
(API orchestration/what-if/handoffs/rehearse) and all audit test
helpers thread pack compositions; GJ has no compositions by design.
`None` vs `{}` are identical (both legacy). Pack is a runtime
dataclass, never persisted/serialized to DB (no migration; no role/
composition columns anywhere in `supabase/migrations`). Residual
risk (documented, not a defect): a FUTURE direct service caller that
bypasses the pack would silently get legacy semantics — mitigation
is the role/composition lint suite plus code review, not a runtime
default (jurisdiction-agnostic layer cannot default MH data).

## 10. GJ isolation

GJ rules all TRIGGER; GJ pack serves zero compositions; GJ
evaluation runs without MH records (probed end to end); default
jurisdiction IN-GJ (code constant, untouched); no MH role leaks
(role lives on rule objects built per-pack; GJ builders are a
separate module). GJ suites green = byte-identical proof.

## 11. Test audit

Focused semantic/audit suites 277/277 (contract 29 incl. lint,
semantics-file rows+readiness+handoff, EC-core, R-054, derivation,
inventory, hygiene, consent). Full backend 2228 passed, 0 failed.
Ruff clean; tsc clean. Dangerous-path coverage: defeat→NOT_APPLICABLE
 status, UNKNOWN-defeater CONDITIONAL, classification-only
INSUFFICIENT, handoff-gate closure, DEP-009 preservation, legacy-
untouched pin, GJ regression — all pinned. Gaps (documented):
(a) handoff-initiate ENDPOINT rejection on a defeated approval is
covered at gate-unit level (`is_ready_to_handoff` + `prepare_
initiation`) but has no dedicated defeated-approval e2e case;
(b) APR-001 trigger-TRUE rows are unit-covered only (no R-001
builder exists to fire them at pack level); (c) the legacy-fallback
surface is pinned-as-legacy rather than closed (by design, §9).

## 12. Rule inventory reconciliation

105 = 26 active + 61 deferred + 26 confirmation − 15 overlap + 3 DNI
+ 4 documented-hygiene (R-059/071/072/076). No accidental status
changes (role migration touches no status set). All five staged
non-trigger candidates (R-030/R-044/R-087/R-035/R-077) confirmed
unmigrated and lint-pinned TRIGGER. R-054 deferred, unbuilt,
uncomposed. R-001/R-064/R-074 states unchanged.

## 13. Falsification matrix

1. EXEMPTION never APPLIES — PASS (rows 4/7/10 + live APR-043 probes).
2. CLASSIFICATION never APPLIES — PASS (rows 16/17 + five live
   APR-001 states).
3. UNKNOWN never FALSE — PASS (token/None/missing/list-element +
   §8 rows).
4. Defeat never grants readiness — PASS (NOT_APPLICABLE status,
   obtained untouched, handoff gate closed, no downstream edges).
5. R-002 cannot suppress EC — PASS (FALSE→insufficient, never DNA).
6. R-043 cannot create applicability — PASS (TRUE-alone→insufficient;
   defeat only with trigger TRUE).
7. R-001 remains the APR-001 trigger — PASS (sole trigger slot;
   deferred = trigger absent = honest unknown).
8. Legacy fallback cannot bypass composition — PASS with noted
   boundary (opt-in by design; all production/test paths thread it;
   direct-call surface pinned-as-legacy, §9).
9. GJ isolated — PASS (roles/compositions/jurisdiction/suites).
10. All alternate paths preserve contract — PASS (orchestration,
    what-if ×2, rehearse, handoffs, endpoints, pack, direct+comps).

## 14. Safety conclusion

**SAFE_WITH_LIMITATIONS.** Limitations: (L1) legacy fallback remains
reachable by future direct service callers bypassing the pack
(pinned, not closed — close by code review + lint, no runtime fix
available without breaking jurisdiction separation); (L2) APR-001
trigger-TRUE rows unverifiable at pack level until R-001 evidence
lands; (L3) defeated-approval handoff rejection lacks a dedicated
endpoint e2e (gate-unit covered). No additional rule activation is
recommended — infrastructure working correctly is not evidence for
any rule.

## 15. Remaining limitations

As §14, plus: exemption reason text is rule-reason-carried (no legal-
citation templating); no dedicated EXEMPT terminal status (phase-1
scope per design); EXPECTED_ROLES map must be deliberately updated
by any future migration (by design); two overlapping contract suites
(root contract file + semantics file — complementary levels, both
green, no action).

## 16. Exact next task

R-044 domestic-exemption migration (same APR-043 composition:
data-only role flip + re-pin + readiness re-proof; no composition
change). Then R-030, R-087 with fresh pins; R-077 split-or-
grandfather mini-audit last. After that: R-003-pattern named
consumption (blocked on R-001/R-003 evidence) and the hygiene
code-triage follow-up. No evidence work is unblocked by this audit.
