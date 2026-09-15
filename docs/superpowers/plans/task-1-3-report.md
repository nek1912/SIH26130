# Task 1-3 Report: Cross-Document Consistency Engine

## What Was Implemented

Implemented the foundational cross-document consistency engine for SIH 26130:

### Task 1: Consistency Models
- `backend/app/consistency/__init__.py` — Module init
- `backend/app/consistency/models.py` — 4 Pydantic models:
  - `ConsistencyOutcome(StrEnum)`: VALID, REVIEW_REQUIRED, INSUFFICIENT_DATA
  - `ConsistencyRule(BaseModel)`: id, canonical_field, affected_systems, evidence_field, requirement_key, document_keys
  - `ConsistencyFinding(BaseModel)`: rule_id, canonical_field, outcome, observed_values, expected_relationship, message, source_ref
  - `ConsistencyResult(BaseModel)`: application_id, outcome, findings, checked_at, rule_version

### Task 2: Seed Config
- `backend/app/seed/consistency.py` — 18 ConsistencyRule objects (C01-C18) with `load_consistency_rules()` function
- Updated `backend/app/seed/__init__.py` with new export

### Task 3: Consistency Engine
- `backend/app/consistency/engine.py` — `check_application_consistency()` function implementing:
  - Groups extracted fields by field_name → {req_key: value}
  - Filters empty/null values
  - Per-rule: 0 values → INSUFFICIENT_DATA, 1 value → VALID, 2+ values → identical? VALID : REVIEW_REQUIRED
  - Aggregates worst-case outcome across all findings

## Test Results

```
20 passed in 1.40s

TestConsistencyModels (4 tests): PASSED
  - test_consistency_outcome_values
  - test_consistency_rule_creation
  - test_consistency_finding_creation
  - test_consistency_result_creation

TestConsistencySeed (5 tests): PASSED
  - test_load_returns_all_18_rules
  - test_rule_ids_are_c01_through_c18
  - test_all_rules_are_must_match
  - test_multi_doc_rules_have_multiple_keys
  - test_document_keys_are_valid_format

TestConsistencyEngine (11 tests): PASSED
  - test_all_identical_values_returns_valid
  - test_mismatched_values_returns_review_required
  - test_no_values_returns_insufficient_data
  - test_single_document_has_value_returns_valid
  - test_partial_values_matching_returns_valid
  - test_empty_string_treated_as_no_value
  - test_single_doc_rule_always_valid
  - test_mixed_outcomes_worst_case
  - test_empty_fields_all_insufficient_data
  - test_deterministic_finding_order
  - test_null_field_value_treated_as_no_value
```

## Lint Results

```
All checks passed! (ruff check app/ tests/)
```

## Files Changed

| File | Action |
|------|--------|
| `backend/app/consistency/__init__.py` | Created |
| `backend/app/consistency/models.py` | Created |
| `backend/app/consistency/engine.py` | Created |
| `backend/app/seed/consistency.py` | Created |
| `backend/app/seed/__init__.py` | Modified (added export) |
| `backend/tests/test_consistency_engine.py` | Created |

## Deviation from Plan

Fixed a bug in the plan's `test_all_identical_values_returns_valid` test: the original test only provided fields for C01 but the RULES constant includes C02 (builtup_area_sqm). Without providing data for C02's document (D04), the overall outcome was INSUFFICIENT_DATA instead of VALID. Added `_make_field("doc-D04", "app-1", "builtup_area_sqm", "2000")` to fix this.

## Concerns

- None. All models, seed config, and engine are deterministic and testable without external dependencies.
