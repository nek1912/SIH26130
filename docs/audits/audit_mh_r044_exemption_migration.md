# Audit — R-044 EXEMPTION Migration inside APR-043

Production migration and verification audit of rule `R-044` (CGWA domestic groundwater
abstraction exemption, `APR-043`) within the Maharashtra (`IN-MH`) pack.

Following the P0 exception-role architecture and the R-043 pilot, this audit executes the
controlled semantic migration of R-044 from `TRIGGER` to `EXEMPTION` inside the existing
`APR-043` composition.

Date (UTC): 2026-09-29.
Stack: FastAPI + Python + pytest.
Jurisdiction: `IN-MH` primary; `IN-GJ` regression-only.

---

## 1. Baseline

Prior to this migration:
- `DEFAULT_JURISDICTION = "IN-GJ"`. Unchanged.
- Inventory counts: MH active 26, MH deferred 61, MH confirmation 26, MH facts 128, GJ active 19.
- Pre-migration role assignments:
  - `R-002` = `CLASSIFICATION` (APR-001)
  - `R-043` = `EXEMPTION` (APR-043)
  - `R-044` = `TRIGGER` (provisional staging candidate)
  - `R-030`, `R-087`, `R-035`, `R-077` = unmigrated `TRIGGER`
  - `R-054` = deferred (APR-052)
  - `R-001`, `R-064`, `R-074` = held/deferred
- Pre-migration APR-043 composition:
  - triggers: `["R-044", "R-077"]`
  - exemptions: `["R-043"]`
  - classifications: `[]`
- Defect in baseline:
  - R-044 (`GW_EXEMPT_DOMESTIC`) acted as a trigger. An applicant abstracting domestic groundwater
    <= 5 m³/day without qualifying for the MSE exemption (R-043) evaluated R-044 to TRUE, which
    produced `APPLIES` at approval level. Thus, qualifying for a statutory exemption paradoxically
    triggered the obligation to obtain a CGWA NOC.
- Suite status entering migration: 2239 passed backend tests, ruff clean, tsc clean.

---

## 2. R-044 Semantic Confirmation

Evidence reconstructed from official register and stored sources (`rule_register_v5.csv` and `SRC-052`):
- `rule_id`: `R-044`
- `approval_id`: `APR-043` ("CGWA NOC - groundwater abstraction")
- `authority`: `AUT-013` (Central Ground Water Authority)
- `jurisdiction`: `CENTRAL`
- `source_id`: `SRC-052` (CGWA Guidelines 2020, dated 2020-09-24, T1 source, locator "Exemptions list")
- `applicability_conditions`: `GW_EXEMPT_DOMESTIC := F-WAT-06 == 'DOMESTIC_ONLY' AND F-WAT-05 <= 5`
- `thresholds`: `5 m3/day`
- `status`: `VERIFIED_CONDITIONAL` / `IMPLEMENTATION_SAFE`

Regulatory statutory meaning:
- Under Section 1.0 (Exemptions from seeking NOC) Category 6 of the CGWA 2020 Guidelines, individual domestic
  consumers abstracting groundwater for drinking/domestic use up to 5 m³/day through dug wells, borewells,
  or tubewells are exempt from seeking a NOC.
- Semantic behavior:
  - `TRUE`: Exemption condition is satisfied. This is duty-defeat information, not a duty-creation trigger.
  - `FALSE`: Exemption condition is not met (e.g. industrial user or abstraction > 5 m³/day). This does NOT
    mean the NOC does not apply; it merely indicates this specific exemption limb is unavailable.
  - `UNKNOWN`: Missing inputs (`F-WAT-06` or `F-WAT-05`) leave the defeater unresolved.
  - R-044 must NEVER independently produce `APPLIES`.
  - R-044 belongs strictly in the `EXEMPTION` role.

---

## 3. APR-043 Composition Before and After

The APR-043 composition structure was audited:
- Before migration:
  - `triggers`: `["R-044", "R-077"]`
  - `exemptions`: `["R-043"]`
  - `classifications`: `[]`
- After migration:
  - `triggers`: `["R-077"]`
  - `exemptions`: `["R-043", "R-044"]`
  - `classifications`: `[]`

Justification:
- Both `R-043` (MSE < 10 m³/day) and `R-044` (domestic <= 5 m³/day) are parallel exemption limbs under `SRC-052`
  "Exemptions list".
- `R-077` (over-exploited assessment unit restriction under `SRC-052` para 4.1) is the genuine statutory
  trigger for NOC requirement.
- Moving R-044 into the exemption group leaves R-077 as the sole trigger. The trigger group remains valid
  and non-empty. No second composition is created.

---

## 4. Role Migration

In `backend/app/seed/mh/approvals.py`:
- `_r044()` builder updated:
  ```python
  def _r044() -> ApprovalRule:
      return _encode(
          "R-044", "APR-043",
          [_and(
              _leaf("F-WAT-06", "eq", "DOMESTIC_ONLY"),
              _leaf("F-WAT-05", "lte", 5),
          )],
          _refs(("SRC-052", "Exemptions list")),
          effective_from=date(2020, 9, 24),
          role=RuleRole.EXEMPTION,
      )
  ```
- `MH_APPROVAL_COMPOSITIONS["APR-043"]` updated:
  ```python
  "APR-043": ApprovalComposition(
      approval_id="APR-043",
      triggers=["R-077"],
      exemptions=["R-043", "R-044"],
  )
  ```
- Unaltered properties:
  - Predicate condition tree: unchanged
  - Fact fields (`F-WAT-06`, `F-WAT-05`): unchanged
  - Source references (`SRC-052`, "Exemptions list"): unchanged
  - Authority (`AUT-013`): unchanged
  - Effective date (`2020-09-24`): unchanged
  - Implementation status (`IMPLEMENTATION_SAFE`): unchanged.

---

## 5. Composition Safety & Multi-Exemption Semantics

Safety guarantees verified:
1. `APR-043` retains a valid, non-empty trigger: `["R-077"]`.
2. Groups are pairwise disjoint: `{"R-077"} ∩ {"R-043", "R-044"} = ∅`.
3. All referenced rules exist in the Maharashtra pack and belong to `APR-043`.
4. No orphan compositions or rules exist.

Multi-Exemption Aggregation Contract:
- Under `compose_approval_evaluations`, exemption evaluation follows "any exemption defeats" + fail-closed on unknown:
  - If trigger is `APPLIES`, any exemption evaluating to `APPLIES` defeats the duty, producing `DOES_NOT_APPLY`
    with the reason indicating the specific exempting limb.
  - If no exemption is `APPLIES`, but any exemption is `UNKNOWN` (`CONDITIONAL` or `INSUFFICIENT_DATA`),
    the approval cannot confirm applicability and produces `CONDITIONAL`.
  - Only when all exemptions evaluate to `DOES_NOT_APPLY` (all exemptions false) does the trigger apply,
    producing `APPLIES`.

---

## 6. R-043 + R-044 Interaction Matrix

Verified truth table under established trigger duty (`R-077` = `APPLIES`):

| R-043 (MSE) | R-044 (Domestic) | Composed Approval Result | Composed Explanation |
|:---|:---|:---|:---|
| `APPLIES` | `APPLIES` | `DOES_NOT_APPLY` | "Exempt under R-043: ...; trigger R-077 would otherwise apply." |
| `APPLIES` | `DOES_NOT_APPLY` | `DOES_NOT_APPLY` | "Exempt under R-043: ...; trigger R-077 would otherwise apply." |
| `DOES_NOT_APPLY` | `APPLIES` | `DOES_NOT_APPLY` | "Exempt under R-044: ...; trigger R-077 would otherwise apply." |
| `DOES_NOT_APPLY` | `DOES_NOT_APPLY` | `APPLIES` | Trigger R-077 evaluation reason (duty confirmed) |
| `INSUFFICIENT_DATA` | `DOES_NOT_APPLY` | `CONDITIONAL` | "Exemption R-043 unresolved ...; approval cannot be confirmed while a defeater is unknown." |
| `DOES_NOT_APPLY` | `INSUFFICIENT_DATA` | `CONDITIONAL` | "Exemption R-044 unresolved ...; approval cannot be confirmed while a defeater is unknown." |
| `INSUFFICIENT_DATA` | `INSUFFICIENT_DATA` | `CONDITIONAL` | Exemption unresolved; fail-closed |

Result: Deterministic, fail-closed, and legally sound in all positions.

---

## 7. R-077 Trigger Preservation

`R-077` remains strictly a `TRIGGER` and is intentionally unmigrated.
Behavior verified:
- `R-077` TRUE + `R-044` TRUE → Exemption defeat (`DOES_NOT_APPLY`).
- `R-077` TRUE + `R-044` UNKNOWN → Defeater unresolved (`CONDITIONAL`).
- `R-077` FALSE + `R-044` TRUE → No trigger duty (`DOES_NOT_APPLY` based on `R-077` reason; exemption noted).
- `R-077` UNKNOWN + `R-044` TRUE → `INSUFFICIENT_DATA` (never `APPLIES`; an exemption cannot defeat a non-established trigger).
- `R-077` UNKNOWN + `R-044` UNKNOWN → `INSUFFICIENT_DATA` (never `APPLIES`).

---

## 8. Truth-Table Verification (10 Scenarios)

All 10 required contract rows were executed against live pack rules and local composition tests:
1. Trigger TRUE + both exemptions FALSE → `APPLIES` (`R-077`).
2. Trigger TRUE + R-043 TRUE + R-044 FALSE → `DOES_NOT_APPLY` ("Exempt under R-043").
3. Trigger TRUE + R-043 FALSE + R-044 TRUE → `DOES_NOT_APPLY` ("Exempt under R-044").
4. Trigger TRUE + both exemptions TRUE → `DOES_NOT_APPLY` (first evaluated exemption in order).
5. Trigger TRUE + R-043 UNKNOWN + R-044 FALSE → `CONDITIONAL` (R-043 unresolved).
6. Trigger TRUE + R-043 FALSE + R-044 UNKNOWN → `CONDITIONAL` (R-044 unresolved).
7. Trigger TRUE + both exemptions UNKNOWN → `CONDITIONAL`.
8. Trigger FALSE + any exemption states → `DOES_NOT_APPLY` on trigger reason.
9. Trigger UNKNOWN + exemption TRUE → `INSUFFICIENT_DATA` (exemption holds but no trigger established).
10. Trigger UNKNOWN + exemptions UNKNOWN → `INSUFFICIENT_DATA`.

---

## 9. Readiness / Dependency / Handoff Proof

Path traced live: `R-077` + `R-043`/`R-044` → `compose_approval_evaluations` → `_determine_status` → orchestration → readiness engine → handoff gate.
Proofs:
1. Exemption defeat yields `DOES_NOT_APPLY` (`NOT_APPLICABLE` orchestration status), which is NEVER `READY`.
2. Exemption defeat does not enter the `obtained_approvals` set (`_TERMINAL_STATUSES` strictly `frozenset({"approved"})`).
3. An `UNKNOWN` defeater yields `CONDITIONAL` (`PENDING_EVALUATION`), which BLOCKS downstream dependencies (`ReadinessStatus.BLOCKED`).
4. Handoff gate (`is_ready_to_handoff`) rejects `NOT_APPLICABLE`, `CONDITIONAL`, and `INSUFFICIENT_DATA`.
   Calling `prepare_initiation` on any non-ready status raises `HandoffStateError`.

---

## 10. Alternate-Path Verification

All ingestion and evaluation pathways were tested to ensure uniform consumption of the updated composition:
- Baseline Orchestration: Consumes `MH_APPROVAL_COMPOSITIONS`.
- What-If Service: Strips overrides, derives facts, and threads `approval_compositions`.
  - Override to `F-WAT-06 = "INDUSTRIAL"` removes the domestic exemption and produces `APPLIES` when `R-077` holds.
- Regulatory Impact & Rehearsal: Consumes `approval_compositions` from pack. Metadata changes correctly evaluate baseline APR-043 defeat.
- Handoff Service: Uses orchestrated verdicts with composition.
- API Endpoints: Handoff, Rehearsal, and Orchestration endpoints all consume pack compositions.
- Direct Rule Evaluation: Per-rule evaluation continues to return raw evaluation (`evaluate_rule(R-044)` returns `applies` when facts match; composition provides the semantic boundary).

---

## 11. Regression Results

- Full backend test suite: **2287 passed**, 0 failed (including 39 dedicated new tests in `test_mh_r044_exemption.py`).
- Ruff linter: `ruff check backend/` clean (all checks passed).
- Frontend TypeScript: `npx tsc --noEmit` clean (0 errors).
- Default jurisdiction: `IN-GJ` unchanged.
- Gujarat pack: 19 rules, all `TRIGGER`, zero compositions, byte-identical.

---

## 12. Counts and Inventory

- Maharashtra Active Rules: 26 (unchanged).
- Maharashtra Deferred Rules: 61 (unchanged).
- Maharashtra Confirmation Rules: 26 (unchanged).
- Maharashtra Fact Registry: 128 (unchanged).
- Gujarat Active Rules: 19 (unchanged).
- Untriaged ApprovalRule candidates: 0 (unchanged).
- Zero new regulatory facts, sources, or evidence items added.

---

## 13. Safety Classification

**`SAFE_TO_RETAIN`**

Rationale:
- R-044 is proven by official statutory evidence (`SRC-052`) to be an exemption.
- APR-043 retains an active trigger (`R-077`).
- Multi-exemption semantics are deterministic, fail-closed, and prevent duty defeat from manufacturing readiness.
- The previous defect where domestic groundwater users were marked as requiring a CGWA NOC is fully closed.
- Downstream readiness, dependency, and handoff protections are proven secure.

---

## 14. Remaining Staged Candidates

With R-044 completed, the remaining non-trigger candidates staged for controlled migration are:
- `R-030`: Petroleum Class-B storage exemption (APR-024)
- `R-087`: Petroleum Class-A/B bulk exemption (APR-024)
- `R-035`: MIDC branch guard (APR-029)
- `R-077`: CGWA Over-exploited unit restriction (to be reviewed for split-or-retain mini-audit)

Deferred rules remain untouched:
- `R-054`: EC expansion exemption (deferred)
- `R-001`, `R-064`, `R-074`: held/deferred.

---

## 15. Exact Next Task

Next scheduled controlled migration:
**`R-030` Petroleum Class-B Exemption Migration** (inside `APR-024` composition with sibling `R-087`).
