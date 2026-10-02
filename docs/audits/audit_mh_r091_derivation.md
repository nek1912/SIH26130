# Audit: R-091 MAH-Derivation Closure (T7 — outcome B)

Date: 2026-10-02. Verdict: **GAP_CLOSURE — R-091 stays PARTIAL by
evidence, not by effort.** No code semantics changed; 9 regression
pins added (`test_mh_r091.py`). No rule, role, composition, GJ,
frontend, or migration changes.

## 1. Original gap

`derive_mah_status()` implements only M3/M7/M9 of the v5
`msihc_mapping_steps` M1..M9 over applicant-supplied F-HAZ-01 +
F-HAZ-02 (exact-name col-3 join). Open: M2 identity resolution,
CON-021 threshold confirmation, M5 Part II class derivation, M8 500 m
aggregation, and an ApprovalRule encoding under APR-012.

## 2. Statutory basis (verified, no inference)

- MSIHC Rules 1989: r.2(ja)/r.2(n) definitions, Schedules 1–3
  (SRC-016 T1; SRC-134 T2 schedules text).
- Amendment chain (msihc_amendment_chain.csv): AM-0 (1989, principal)
  through AM-4 (S.O. 57(E) 2000-01-19, Sch 1 substituted) VERIFIED;
  AM-5 (2000→2026): no later amendment identified
  (VERIFIED_CONDITIONAL); UNK-035 OPEN (consolidated text unread).
- R-091 register row: `MAH_DERIVED := M1..M9; TRUE if any resolved
  chemical/class aggregate >= col 3; FALSE only if all resolved; else
  UNKNOWN`, type DERIVE, target APR-012 (REPORT), effective 1989-11-27,
  VERIFIED_CONDITIONAL.
- Threshold evidence: v4 resolved the HSPCB-scan extraction conflict
  (1989 Gazette + India Code agree); per-cell gating stands (V5-0270:
  only VERIFIED* cells usable; blocked S1-TOX / S2-18 col 4 / S3P1-111
  → UNKNOWN, never FALSE).

## 3. Implemented subset (proven, tested)

M3 (Sch 2 isolated-storage match) + M4 (Sch 3 Part I named match) via
exact-name join + M7 (max quantity t) + M9 outcome with fail-closed
UNKNOWN (unmapped/unknown/missing never FALSE; TRUE dominates; empty
inventory FALSE). Consumer today: R-002 CLASSIFICATION only
(informational, never decisive). Provenance via FactProvenance.

## 4. Evidence still missing (each maps to a STOP condition)

1. **M2 identity**: schedules contain no CAS; resolution needs an
   external identity service, explicitly unselected
   (REQUIRES_OFFICIAL_CONFIRMATION). ET-v5-08 (CAS match) correctly
   yields UNKNOWN without applicant mapping.
2. **M5 class derivation**: S1-TOX bands blocked (signs contradictory,
   kept blocked not repaired); property→class needs the toxic limb, so
   no partial class logic was encoded. ET-128 correctly UNKNOWN.
3. **M8 aggregation**: conditional on installation/distance evidence
   (F-HAZ-04 shape has it, join semantics undefined) + spatial
   computation (R-061 deferred architecture). Per-entry comparison is
   the documented partial; no edge test demands summation.
4. **APR-012 encoding**: lifecycle home has no authority/docs/edges in
   pack and its real duties (R-019/R-020/R-021) are unencodable
   (EXISTS/aggregation/Sch-5); encoding DERIVE-as-TRIGGER would conflate
   layers and risk false clearance.
5. **Runtime threshold table**: applicant mapping is the designed input
   ("mapping must be supplied"); baking 200+ cells into code adds a
   version-freeze liability for zero decision gain.
6. **Post-2000 currency** (UNK-035) and the M9 threshold-verification
   flag (mapping carries no verification status): nothing to surface.

## 5. Downstream impact (the 10 cases)

1. Qualifying (above col 3) → TRUE — tested (`test_above_col3_is_mah`).
2. Non-qualifying (all resolved below) → FALSE — tested.
3. Missing quantity → UNKNOWN — tested.
4. Missing identity/classification → UNKNOWN — tested.
5. Multiple chemicals (TRUE dominates; empty → FALSE) — tested.
6. Exact col-3 boundary (`>=`) → TRUE — tested.
7. Unknown schedule membership → UNKNOWN (ET-127) — tested.
8. Unknown aggregation → per-entry M8 limitation, pinned in
   `test_mh_r091.py`; cannot flip any approval (sole consumer is
   informational R-002; R-019/20/21 deferred; no APR-012 rule exists).
9. Wrong jurisdiction → JURISDICTION_MISMATCH — tested.
10. Effective date → no date dimension; R-091 in force since 1989-11-27,
    so every realistic evaluation is in-window; nothing to test.

Missing input can never produce APPLIES downstream: pinned
structurally (`test_fprc03_consumers_are_classification_only`,
`test_no_active_rule_targets_apr012`).

## 6. Implementation decision

**B — do not implement.** Every extension path requires inference,
an unselected external service, an unverifiable table, deferred
spatial architecture, or layer conflation. The proven subset stays;
the remainder stays explicitly unresolved (deferred R-091 + R-019 +
R-020 + R-021 + R-061, open UNK-035).

## 7. Code changes

- `backend/tests/test_mh_r091.py` (new, 9 tests): deferred gate,
  no-APR-012, classification-only consumer, downstream deferrals,
  derived-only spec, F-HAZ-04 unconsumed, M8 limitation pin.
- Zero production-code changes.

## 8. Jurisdiction

IN-MH only (derivation rejects IN-GJ; no GJ test/rule touched).
DEFAULT_JURISDICTION untouched. GJ suite green.

## 9. Limitations

- Multi-entry same-chemical split quantities evaluate per-entry
  (documented M8 limitation, fail direction unresolvable without
  installation/distance evidence).
- Applicant-supplied mapping values are trusted as inputs (GIGO at
  the fact layer, same as all facts); the v5 threshold table is
  evidence, not a runtime cross-check.
- R-091 full closure needs, in order: M2 identity source selection,
  S1-TOX band resolution, R-061 spatial support + F-HAZ-04 join
  semantics, UNK-035 currency read, then APR-012 lifecycle work
  (R-019/20/21 prerequisites).

Next task: T6 staging execution (ops) or T7 consent chain — not R-091
rework without new primary evidence.
