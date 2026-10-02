# Audit: MH R-087 Petroleum Rule Semantic Migration (T4)

## 1. Evidence inspected

- `rule_register_v5.csv` R-087 row: `APR-023, REGISTRATION,
  Boiler registration, AUT-007, STATEWIDE, BOILER_EXISTING :=
  F-BLR-07 == 'REGISTERED_UNDER_1923_ACT' -> deemed registered
  (s.45(2)(f)); certificate continues until date shown unless
  cancelled (s.45(2)(g)), F-BLR-07;F-BLR-08`, `SRC-034, s.45(2)`,
  `T1, 2025-04-04, HIGH, IMPLEMENTATION_SAFE, DETERMINISTIC`,
  effective `2025-05-01` EXACT_DATE.
- `rules.csv` R-087 row (same condition/source).
- `boiler_lifecycle.csv` `EXISTING_BOILER_TRANSITION`: boilers
  registered under the 1923 Act deemed registered; certificates in
  force continue until the date shown unless cancelled; `SRC-034`,
  `s.11(1) proviso; s.45(2)(b),(f),(g),(i)`, VERIFIED.
- `approvals.csv` APR-023 notes: existing 1923-Act registrations
  deemed registered; certificates continue until date shown
  (s.45(2)(f),(g)).
- `implementation_safe_rules.csv` R-087: `SRC-034, T1, s.45(2)`,
  IMPLEMENTATION_SAFE.
- Code: `backend/app/seed/mh/approvals.py` `_r087`, `_r028`,
  `_r086`, `_r073`, `MH_APPROVAL_COMPOSITIONS`;
  `backend/app/rules/applicability.py` `compose_approval_evaluations`;
  `backend/app/seed/mh/sources.py` SRC-034; `backend/app/seed/pack.py`.
- Prior audits: `audit_mh_r030_exemption_migration.md` (R-087
  disambiguation, APR-023 triggers present),
  `audit_mh_active_rule_evidence_integrity.md` (R-087 BLOCKING,
  severe inversion), `MASTER_MH_IMPLEMENTATION_STATUS.md` (S-R087
  planned next).
- R-030 (`SRC-092` Petroleum Act 1934 s.7(i), `APR-026`,
  `AUT-008/AUT-009`, F-PET-*) inspected jointly per mandate §4.

## 2. R-087 meaning

Transitional deeming provision under Boilers Act 2025 s.45(2)(f):
a boiler registered under the repealed Indian Boilers Act 1923 is
deemed registered under the 2025 Act, so no fresh s.12 registration
duty attaches. The s.45(2)(g) certificate-continuation date is
tracked in fact `F-BLR-08`; it is ongoing compliance tracking, not
an applicability input, and is correctly absent from the predicate.

## 3. Previous role

`RuleRole.TRIGGER` (seed default, no override). Under the legacy
`APR-023` aggregation, `R-087 == TRUE` produced `APPLIES` — falsely
demanding fresh registration for an already (deemed) registered
boiler. Live pre-migration probe: definition-meeting facts plus
`F-BLR-07 == 'REGISTERED_UNDER_1923_ACT'` composed to
`applies` (via `R-028`). This is the documented severe inversion.

## 4. New role

`RuleRole.EXEMPTION` (duty-defeat; interpreted only through the
explicit `APR-023` composition; never independently `APPLIES`).
Data-only role flip in `_r087`; predicate, sources, dates,
approval, authority untouched.

## 5. Exact predicate

```python
_leaf("F-BLR-07", "eq", "REGISTERED_UNDER_1923_ACT")
```

Unchanged by this migration. Verified pre-change behavior:
TRUE -> `applies`; `NOT_REGISTERED` /
`REGISTERED_UNDER_2025_ACT` -> `does_not_apply`; missing / None /
`"UNKNOWN"` -> `insufficient_data` with
`missing_inputs == ["F-BLR-07"]`; pre-2025-05-01 evaluation date ->
`does_not_apply` (not in force); missing date preserves behavior.

## 6. Source IDs

`SRC-034` (Boilers Act 2025 Gazette text, T1/OFFICIAL_PRIMARY),
citation `s.45(2)`. No source added, removed, or reworded.

## 7. Effective date

`2025-05-01` (EXACT_DATE, per SRC-032 in-force record). Unchanged.

## 8. APR-026 relationship

None. `APR-026` (petroleum storage licence, `AUT-008/AUT-009`)
keeps no explicit composition and its sole active rule `R-030`
stays `TRIGGER` per the STOP verdict. `R-087` neither references
nor affects `APR-026`; no composition connects them, and none was
created.

## 9. R-030 relationship

Independent rules in different statutory regimes: `R-030` is
Petroleum Act 1934 s.7(i) Class-B storage (`F-PET-01/02/04`,
`APR-026`); `R-087` is Boilers Act 2025 s.45(2)(f)
(`F-BLR-07`, `APR-023`). Different approvals, authorities, fact
groups, sources, effective dates. They share no facts, no
approval, and no composition. The earlier grouping of the two was
a clerical prompt error (see the R-030 audit §4), not evidence.

## 10. Composition before/after

Before: `APR-023` had no composition entry (legacy priority over
`R-028, R-073, R-086, R-087`, all `TRIGGER`).

After (`MH_APPROVAL_COMPOSITIONS["APR-023"]`):

```python
ApprovalComposition(
    approval_id="APR-023",
    triggers=["R-028", "R-073", "R-086"],
    exemptions=["R-087"],
)
```

Trigger legitimacy (all `IN-MH`, all built `TRIGGER`):
`R-086` is the precise registration trigger (R-028 definition
tree + `NOT_REGISTERED`, s.12); `R-028` is the statutory boiler
definition (s.2(c)); `R-073` is the BOE heating-surface condition
(`> 1000` m2 strict, BOE Rules 2025). Triggers stay non-empty, so
the R-030 trigger-deficit invariant never applies. `APR-026`
composition status is unchanged (absent, by STOP design).

## 11. Truth table (live `APR-023` composition)

| Trigger group | R-087 | Approval verdict |
|---|---|---|
| TRUE (`R-028`) | TRUE | `DOES_NOT_APPLY` ("Exempt under R-087 … would otherwise apply") |
| TRUE (`R-028`/`R-086`) | FALSE | `APPLIES` |
| TRUE (`R-028`+`R-073`) | UNKNOWN (fact missing) | `CONDITIONAL` (defeater unresolved blocks `APPLIES`) |
| FALSE (`R-028` etc.) | TRUE/FALSE | `DOES_NOT_APPLY` (no duty) |
| UNKNOWN (no TRUE, no FALSE) | TRUE | `INSUFFICIENT_DATA` (defeat needs a duty; never `APPLIES`) |
| UNKNOWN | FALSE/UNKNOWN | `INSUFFICIENT_DATA` / `CONDITIONAL` |

All rows proven in `test_mh_r087_semantics.py`
(`TestComposedTruthTable`), including live-pack spot checks:
unregistered boiler -> `applies`; deemed boiler -> reasoned
`does_not_apply`; trigger-TRUE + missing `F-BLR-07` ->
`conditional`.

## 12. Fail-open tests

1. Missing `F-BLR-07` (or all facts) -> `insufficient_data`,
   never a false `does_not_apply`.
2. `"UNKNOWN"` / None -> `insufficient_data`, never `FALSE`.
3. `R-087 == TRUE` with unresolved trigger -> `insufficient_data`,
   never `APPLIES`.
4. N/A (no classification in this composition; `APR-001/R-002`
   untouched).
5. No triggerless composition exists: every composition with
   exemptions names non-empty triggers (`APR-023`, `APR-043`);
   `APR-001` is classifications-only by design;
   `APR-026` stays uncomposed per STOP.
6. `does_not_apply` (exempt) -> `NOT_APPLICABLE`, never `READY`.
7. Exempted `APR-023` cannot satisfy a downstream dependency
   (`_TERMINAL_STATUSES == {"approved"}`; conditional prerequisite
   blocks).
8. `conditional` / `not_applicable` rejected at handoff
   (`HandoffStateError`).

## 13. Readiness result

Live orchestration (`orchestrate_application`, `APR-023`):
unregistered definition-meeting boiler -> `applies` / `ready`;
deemed-registered boiler -> `does_not_apply` / `not_applicable`;
no-boiler canonical facts (`F-BLR-04 == False`) ->
`does_not_apply` / `not_applicable` (canonical expectation
preserved); empty facts -> `insufficient_data` /
`insufficient_data`. No readiness logic duplicated in the rule.

## 14. Dependency result

`APR-023` has no pack dependency edges (pack edges are
`DEP-009 x2` on `APR-010` only), so readiness above is direct.
`evaluate_readiness` gates verified: `does_not_apply` ->
`NOT_APPLICABLE`; `conditional` prerequisite -> downstream
`BLOCKED`; exemption verdicts never enter the obtained set.

## 15. Handoff result

`is_ready_to_handoff("ready") is True`;
`conditional` / `not_applicable` return `False` and
`prepare_initiation` raises `HandoffStateError`. A deemed
(exempted) boiler approval cannot pass handoff.

## 16. Alternate execution paths

All use the same pack composition: direct `evaluate_rule`
(rule-level, role-independent); `summarize_by_approval` with pack
compositions; full `orchestrate_application`;
`run_whatif_assessment` (`NOT_REGISTERED` -> `applies` flips to
`REGISTERED_UNDER_1923_ACT` -> `does_not_apply`);
`rehearse_impact` (`SRC-034` metadata change lists `APR-023`
affected); handoff gates; regulatory pack serving. Each path
covered by a dedicated test.

## 17. Jurisdiction isolation

`IN-GJ`: 19 rules, `approval_compositions == {}`, all roles
`trigger`, `DEFAULT_JURISDICTION == "IN-GJ"`; `R-030`/`R-087`
absent from GJ. `IN-MH`: 26 rules, 61 deferred, 128 facts,
`MH_INCLUDED_RULE_IDS` exact. No GJ source/reference leakage;
`R-002/R-043/R-044/R-030/R-035/R-077` untouched.

## 18. Test results

- New: `backend/tests/test_mh_r087_semantics.py`, 62 tests, pass.
- Re-pinned (deliberate, not weakened): `EXPECTED_ROLES`
  `R-087 -> exemption` + `APR-023` in the served-composition set
  (`test_mh_exception_role_contract.py`); `R-087` removed from the
  unmigrated-trigger pins and added to the non-trigger sets
  (`test_mh_exception_semantics.py`, `test_mh_r044_exemption.py`).
- Focused files: 171 + 62 pass.
- Full: `2423 passed, 0 failed` (2348 baseline + 62 new + 13
  concurrent T3 demo-contract tests in untracked
  `test_api_mh_demo_contract.py`, not owned by this task).
- Ruff: touched files clean; repo-wide 20 x E501 confined to
  pre-existing `test_mh_canonical_scenario.py` /
  `test_mh_r030_exemption.py` lines (none on touched lines).

## 19. Safety classification

`SAFE_MIGRATION` (Case A): evidence establishes the EXEMPTION
role (T1 `SRC-034` s.45(2)(f)); valid triggers exist; no
triggerless composition; truth table, readiness, dependency,
handoff, What-If/rehearsal, and GJ isolation all pass; `R-030`
remains `TRIGGER`; full suite green.

## 20. Remaining limitation

1. `R-087` defeats only the 1923-deemed status. A boiler with
   `F-BLR-07 == 'REGISTERED_UNDER_2025_ACT'` still composes to
   `APPLIES` via `R-028` even though no fresh registration is due;
   no rule encodes the 2025-registered defeat, and none was
   invented here.
2. `R-073` (BOE personnel condition) rides in the registration
   triggers per the v5 `APR-023` grouping; a deemed-registered
   large-surface boiler therefore composes to `does_not_apply`
   for the whole approval, including its BOE limb. Personnel-duty
   separation is future work, not a migration blocker.
3. `F-BLR-08` (certificate-continuation date) remains untracked
   for applicability by evidence design (s.45(2)(g) compliance
   tracking).

Exact next task: T5 (thread persisted pack into regulatory explain
paths + seed MH sources for demo citations), parallel-safe with
T3/T6. No T5/T6 work started here. No frontend files touched. No
commit made.
