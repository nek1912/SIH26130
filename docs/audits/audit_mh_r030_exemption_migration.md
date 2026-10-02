# Audit: MH R-030 Petroleum Class-B Exemption Migration

## 1. Executive Summary

- **Task**: Controlled semantic migration of rule `R-030` (Petroleum Class-B exemption) and evaluation of sibling rule `R-087` under approval `APR-024`.
- **Verdict**: **STOP_UNSAFE_TO_MIGRATE (RETAIN UNMIGRATED / REQUIRE TRIGGER ENCODING)**.
- **Key Finding**:
  1. **Approval ID Disambiguation**: The prompt candidate `APR-024` does not exist in the Maharashtra or Gujarat regulatory datasets. The true statutory target of `R-030` is `APR-026` (*Petroleum storage licence (Form XII/XIII District Authority; Form XV/XVI PESO) + Rule 144 NOC*, authority `AUT-008 / AUT-009`).
  2. **Sibling Rule Disambiguation**: `R-087` is **NOT** a petroleum rule, **NOT** an exemption to `APR-024`/`APR-026`, and **NOT** a sibling of `R-030`. `R-087` encodes transitional deemed registration under the *Boilers Act 2025* s.45(2)(f) (`F-BLR-07 == 'REGISTERED_UNDER_1923_ACT'`), targeting `APR-023` (*Boiler registration*, authority `AUT-007`). Its presence in the prompt derives from a clerical error in `audit_mh_r044_exemption_migration.md` §14.
  3. **Missing Statutory Trigger**: In the active Maharashtra regulatory pack, `R-030` is the **sole** active rule targeting `APR-026`. There is **no active statutory trigger** encoded for `APR-026` (the general obligation to obtain a petroleum licence under *Petroleum Act 1934* s.3(2) is unmodeled as an active `ApprovalRule`; candidate rules `R-029` is `DO_NOT_IMPLEMENT`, `R-031` is unencoded, `R-032` is deferred form routing, `R-092` is deferred DA NOC, and `R-100` is deferred licence renewal).
  4. **Invariant Violation**: Section 5 of the mandate requires that after migration, `APR-024 triggers: MUST remain non-empty`, and Section 14 Criterion 3 requires `APR-024 retains a legitimate TRIGGER`. Migrating `R-030` to `RuleRole.EXEMPTION` today would leave the petroleum approval triggerless (`triggers = []`). In `compose_approval_evaluations`, an approval with zero triggers and one exemption collapses to `INSUFFICIENT_DATA` unconditionally, erasing the statutory licence obligation for all facilities and breaking downstream e2e test contracts (e.g. `test_c_apr026_document_blocked`).
  5. **Safety Disposition**: Pursuant to Section 2 ("*STOP if the evidence does not establish the required exemption/trigger relationship*") and Section 3 ("*and the relevant petroleum approval composition must retain a real TRIGGER. If NO: STOP and document why the migration is not safe*"), `R-030` and `R-087` remain unmigrated as `RuleRole.TRIGGER`. 38 dedicated safety and falsification tests have been added to prove all boundaries, verify fail-closed semantics, and document the architectural prerequisite for future activation.

---

## 2. Regulatory Evidence Base

| Dimension | Rule R-030 | Rule R-087 |
|:---|:---|:---|
| **Statutory Law** | Petroleum Act 1934 s.7(i) | Boilers Act 2025 s.45(2)(f) |
| **Administrative Source** | PESO SOP exemptions table | Central Boiler Board / MAITRI |
| **Source IDs** | `SRC-092` (Petroleum Act), `SRC-017` (PESO SOP) | `SRC-034` (Boilers Act 2025) |
| **True Approval Target** | `APR-026` (Petroleum storage licence) | `APR-023` (Boiler registration) |
| **Competent Authority** | `AUT-008` (District Authority) / `AUT-009` (PESO) | `AUT-007` (Directorate of Steam Boilers) |
| **Effective Date** | 2002 (YEAR_ONLY window omitted) | 2025-05-01 |
| **Statutory Text** | "a person need not obtain a licence for the transport or storage of (i) petroleum Class B, if the total quantity in his possession at any one place does not exceed 2,500 L and none of it is contained in a receptacle exceeding 1,000 L" | "any boiler or boiler component registered under the Indian Boilers Act, 1923 shall be deemed to be registered under this Act" |
| **Role Type** | Statutory Exemption (duty-defeat) | Transitional Deeming (status classification) |

---

## 3. Predicate Boundaries & Threshold Verification

Rule `R-030` predicate:
```python
AndNode([
    _leaf("F-PET-01", "eq", "B"),
    _leaf("F-PET-02", "lte", 2500),
    _leaf("F-PET-04", "lte", 1000),
])
```

Tested boundaries:
- **Class B + Within Limits**: `F-PET-01='B', F-PET-02=2000 L, F-PET-04=500 L` -> Rule evaluates `APPLIES` (exemption criteria met).
- **Class B Exact Boundary**: `F-PET-01='B', F-PET-02=2500 L, F-PET-04=1000 L` -> Rule evaluates `APPLIES` (exact `<=` verified).
- **Class B Above Quantity**: `F-PET-01='B', F-PET-02=2501 L, F-PET-04=1000 L` -> Rule evaluates `DOES_NOT_APPLY` (exemption lost).
- **Class B Above Receptacle**: `F-PET-01='B', F-PET-02=2000 L, F-PET-04=1001 L` -> Rule evaluates `DOES_NOT_APPLY` (exemption lost).
- **Class B Fractional Thresholds**: `F-PET-02=2500.5 L` -> `DOES_NOT_APPLY`; `F-PET-04=1000.5 L` -> `DOES_NOT_APPLY`.
- **Non-Class B**: Class A, Class C, NOT_PETROLEUM -> `DOES_NOT_APPLY`.
- **Missing Facts**: Missing `F-PET-01`, `F-PET-02`, or `F-PET-04` -> Fails closed to `INSUFFICIENT_DATA`.
- **Unknown Facts**: `F-PET-02='UNKNOWN'` or `F-PET-04='UNKNOWN'` -> Fails closed to `INSUFFICIENT_DATA`.

---

## 4. Inspection of Sibling Rule R-087

Pursuant to Section 4 of the instructions:
1. **What statutory condition does R-087 represent?**
   It represents transitional deemed registration under the *Boilers Act 2025* s.45(2)(f). Existing boilers registered under the 1923 Act are deemed registered under the 2025 Act (`F-BLR-07 == 'REGISTERED_UNDER_1923_ACT'`).
2. **Is it the actual approval trigger?**
   No. For `APR-023` (Boilers), the trigger is `R-086` (`R-028` boiler definition met AND `F-BLR-07 == 'NOT_REGISTERED'`). For petroleum approvals (`APR-024`/`APR-026`), `R-087` has zero statutory relation.
3. **Is it itself an exemption?**
   In the boiler domain (`APR-023`), `R-087` operates as a transition/deeming provision that relieves an existing boiler holder from fresh registration under s.12. In the petroleum domain, it is completely inapplicable.
4. **Is it a classification/guard?**
   It is a statutory transitional status rule, referencing the boiler fact group `BLR` (`F-BLR-07`).
5. **Does APR-024 already have a valid trigger independent of R-030?**
   No. `APR-024` does not exist, and `APR-026` has no active trigger rule.

**Conclusion**: `R-087` cannot be composed with `R-030`. It remains untouched in `APR-023`.

---

## 5. Composition Status: Before and After

### Prompt Expectation vs Actual Codebase Reality

| Component | Prompt Candidate | Actual Active Pack | Disposition |
|:---|:---|:---|:---|
| **Approval Code** | `APR-024` | `APR-026` | Corrected to `APR-026` (`APR-024` unencoded/nonexistent) |
| **R-030 Role** | `RuleRole.EXEMPTION` | `RuleRole.TRIGGER` | Retained as `TRIGGER` (Blocked by missing trigger) |
| **R-087 Role** | Sibling exemption | `RuleRole.TRIGGER` in `APR-023` | Preserved untouched in `APR-023` |
| **Triggers** | Expected non-empty | None exist in active pack | Invariant `triggers MUST remain non-empty` fails |
| **Approval Composition** | Composed | Uncomposed (legacy priority) | Kept uncomposed to preserve system invariants |

---

## 6. Falsification Analysis: Why Triggerless Migration is Unsafe

If `R-030` were migrated to `RuleRole.EXEMPTION` and composed under `APR-026` without a trigger:
```python
ApprovalComposition(
    approval_id="APR-026",
    triggers=[],
    exemptions=["R-030"],
)
```
1. **Mathematical Collapse**: Under `compose_approval_evaluations` lines 802-810:
   ```python
   # No triggers at all: classifications/exemptions alone decide nothing -> INSUFFICIENT_DATA
   ```
   The approval would return `INSUFFICIENT_DATA` for every possible project fact combination.
2. **Duty Erasure**: A facility storing 50,000 L of petroleum Class B would receive `INSUFFICIENT_DATA` instead of `APPLIES`, destroying the statutory requirement for a PESO/District Authority licence.
3. **Downstream Breakage**: Tests expecting `APR-026` to apply on petroleum facts (e.g. `test_c_apr026_document_blocked` in `test_mh_api_e2e.py`) would immediately fail.

---

## 7. §8 Composed Truth Table (Hypothetical Verification)

In `test_mh_r030_exemption.py`, a hypothetical legitimate trigger (`R-PET-TRIG`) was composed with `R-030` as an exemption to prove the full §8 contract:

| Row | Trigger Evaluation | R-030 Evaluation | Composed Verdict | Reason / Consequence |
|:---:|:---|:---|:---|:---|
| 1 | `APPLIES` | `APPLIES` | `DOES_NOT_APPLY` | "Exempt under R-030... trigger would otherwise apply." |
| 2 | `APPLIES` | `DOES_NOT_APPLY` | `APPLIES` | Approval attaches; exemption lost due to volume/receptacle limits |
| 3 | `APPLIES` | `INSUFFICIENT_DATA` | `CONDITIONAL` | Defeater unresolved blocks `APPLIES`; never ignored |
| 4 | `DOES_NOT_APPLY` | `APPLIES` | `DOES_NOT_APPLY` | Trigger not met; exemption also holds |
| 5 | `DOES_NOT_APPLY` | `DOES_NOT_APPLY` | `DOES_NOT_APPLY` | Trigger not met; no approval duty |
| 6 | `INSUFFICIENT_DATA` | `APPLIES` | `INSUFFICIENT_DATA` | Defeat requires duty; no trigger established |
| 7 | `INSUFFICIENT_DATA` | `DOES_NOT_APPLY` | `INSUFFICIENT_DATA` | Unknown trigger remains fail-closed |
| 8 | `INSUFFICIENT_DATA` | `INSUFFICIENT_DATA` | `INSUFFICIENT_DATA` | Double unknown remains fail-closed |

All 8 rows evaluated exactly per the established specification.

---

## 8. Fail-Open, Readiness, Dependency, and Handoff Verification

- **Exemption Alone Never APPLIES**: Verified that an exemption evaluated in isolation or with an unresolved trigger never produces `APPLIES`.
- **Readiness Gate**: Verified that an exempt approval (`DOES_NOT_APPLY`) evaluates to `ReadinessStatus.NOT_APPLICABLE` and never `READY`.
- **Unresolved Gate**: Verified that missing facts (`INSUFFICIENT_DATA`) evaluate to `ReadinessStatus.PENDING_EVALUATION` and never `READY`.
- **Dependency Gate**: Verified that an exemption defeat cannot satisfy downstream dependencies (`_TERMINAL_STATUSES` strictly `{approved}`).
- **Handoff Gate**: Verified that `is_ready_to_handoff("not_applicable")` and `is_ready_to_handoff("conditional")` return `False`, and `prepare_initiation` raises `HandoffStateError`.

---

## 9. Test Suite & Verification Results

- **New Tests Added**: 38 dedicated tests in `backend/tests/test_mh_r030_exemption.py`.
- **Focused Test Run**: 38 passed in 1.28s.
- **Full Backend Suite**: 2325 passed in 37.89s (2287 baseline + 38 new).
- **Ruff Lint**: Clean.
- **Frontend TypeScript**: Clean.
- **Gujarat Isolation**: Clean (byte-identical, 19 rules, empty compositions, default jurisdiction preserved).

---

## 10. Safety Classification & Next Engineering Steps

- **Classification**: **STOP_UNSAFE_TO_MIGRATE (RETAIN UNMIGRATED)**.
- **Prerequisite for Future Migration**:
  1. Author and verify a statutory trigger rule for petroleum storage licensing (e.g. storage of petroleum Class A/B/C above threshold or general storage duty under Petroleum Act 1934 s.3(2)).
  2. Associate the trigger rule with `APR-026`.
  3. Once a legitimate trigger is active in `load_mh_approval_rules()`, migrate `R-030` to `RuleRole.EXEMPTION` with composition `ApprovalComposition(approval_id="APR-026", triggers=[trigger_id], exemptions=["R-030"])`.
- **Exact Next Migration Task**:
  Controlled semantic audit and migration of `R-087` (*Boilers Act 2025 s.45(2) deemed registration*) under `APR-023` (*Boiler registration*), where active sibling trigger rules `R-028`, `R-073`, and `R-086` are already active.
