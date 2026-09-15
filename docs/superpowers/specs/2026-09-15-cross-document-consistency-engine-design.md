# Cross-Document Consistency Engine — Design Spec

**Date:** 2026-09-15
**Phase:** 3E (also referenced as Phase 5 in earlier roadmap)
**Status:** Approved

## Goal

Implement a deterministic cross-document consistency engine that compares extracted fields across documents belonging to the same application, using the 18 rules from the workbook's Consistency_Fields sheet.

## Constraints

- No LLM, no RAG, no embeddings, no OCR
- All 18 workbook rules say MUST MATCH — no other comparison types needed
- No normalization (exact string comparison)
- On-demand execution (not event-driven)
- Consistency warnings only — never convert to legal rejection
- Reuse existing extraction, document, auth, and audit patterns

## Data Models

```python
# backend/app/consistency/models.py

class ConsistencyOutcome(str, Enum):
    VALID = "VALID"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class ConsistencyRule(BaseModel):
    id: str                    # "C01"
    canonical_field: str       # "plot_area_sqm"
    affected_systems: str      # "GIDC Plan" (informational)
    evidence_field: str        # "Land/title/GIS" (informational)
    requirement_key: str       # "MUST_MATCH"
    document_keys: list[str]   # ["D01", "D02"]

class ConsistencyFinding(BaseModel):
    rule_id: str
    canonical_field: str
    outcome: ConsistencyOutcome
    observed_values: dict[str, Any]  # {req_key: value}
    expected_relationship: str       # "MUST_MATCH across [D01, D02]"
    message: str
    source_ref: str

class ConsistencyResult(BaseModel):
    application_id: str
    outcome: ConsistencyOutcome      # worst-case across all findings
    findings: list[ConsistencyFinding]
    checked_at: datetime
    rule_version: str
```

## Engine Logic

```python
# backend/app/consistency/engine.py

def check_application_consistency(
    application_id: str,
    extracted_fields: list[ExtractedField],
    rules: list[ConsistencyRule],
) -> ConsistencyResult:
    """
    1. Group extracted_fields by field_name → {req_key: value}
       (requires mapping document_id → requirement_key via documents table)
    2. For each ConsistencyRule:
       a. Collect values from rule's document_keys
       b. Filter out None/empty values
       c. 0 values → INSUFFICIENT_DATA
       d. 1 value → VALID
       e. 2+ values → all identical? VALID : REVIEW_REQUIRED
    3. Aggregate: worst outcome across all rules
    4. Return ConsistencyResult
    """
```

## Seed Config

```python
# backend/app/seed/consistency.py

CONSISTENCY_RULES = [
    # C01-C18 mapped to document requirement keys
    # C01: plot_area_sqm → D01, D02, D03
    # C02: builtup_area_sqm → D04
    # C03: production_capacity → D08, D09
    # C04: product_names → D08, D09
    # C05: raw_materials → D09, D14
    # C06: hazardous_chemical_max_quantity → D11, D16
    # C07: fresh_water_requirement → D07
    # C08: effluent_generation → D06, D07
    # C09: ETP_capacity → D06
    # C10: hazardous_waste_quantity → D10
    # C11: power_demand_kVA → D13
    # C12: DG_capacity → D13, D16
    # C13: building_height → D04, D12
    # C14: worker_count → D14
    # C15: plot_or_survey_identifier → D01, D02, D03
    # C16: applicant/company_name → D01-D17 (all)
    # C17: address → D01-D17 (all)
    # C18: legal_entity_type → D14
]
```

## Database Schema

```sql
-- supabase/migrations/004_consistency.sql

create type consistency_outcome as enum ('VALID', 'REVIEW_REQUIRED', 'INSUFFICIENT_DATA');

create table consistency_results (
  id                  uuid primary key default gen_random_uuid(),
  application_id      uuid not null references applications(id) on delete cascade,
  outcome             consistency_outcome not null,
  checked_at          timestamptz not null default now(),
  rule_version        text not null default '1',
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create table consistency_findings (
  id                  uuid primary key default gen_random_uuid(),
  result_id           uuid not null references consistency_results(id) on delete cascade,
  application_id      uuid not null references applications(id) on delete cascade,
  rule_id             text not null,
  canonical_field     text not null,
  outcome             consistency_outcome not null,
  observed_values     jsonb not null default '{}',
  expected_relationship text not null,
  message             text not null default '',
  source_ref          text not null default '',
  created_at          timestamptz not null default now()
);

create index idx_consistency_results_app on consistency_results(application_id);
create index idx_consistency_findings_app on consistency_findings(application_id);
create index idx_consistency_findings_result on consistency_findings(result_id);
```

## API Endpoints

```
POST /applications/{app_id}/consistency/check
  - Runs consistency check, stores/replaces result, returns ConsistencyResult
  - Auth: APPLICATION_VIEW_OWN/TEAM/ALL + ownership

GET /applications/{app_id}/consistency
  - Returns latest consistency result + findings
  - 404 if no check run
  - Auth: APPLICATION_VIEW_OWN/TEAM/ALL + ownership
```

## Frontend Changes

- Extend `staff/ApplicationDetailPage.tsx` and `applicant/ApplicationDetailPage.tsx`
- Add "Consistency" section below document checklist
- Overall outcome badge + "Run Check" button
- Findings table with color-coded rows
- Add API methods and TypeScript types

## Testing

**Engine tests (~11):**
- All identical → VALID
- Mismatch → REVIEW_REQUIRED
- No values → INSUFFICIENT_DATA
- Single doc → VALID
- Partial values, matching → VALID
- Empty strings → no value
- All 18 rules for known scenario
- Mixed outcomes → worst-case
- Single-doc rules → VALID
- Empty fields → all INSUFFICIENT_DATA
- Deterministic ordering

**API tests (~7):**
- POST creates result + findings
- GET returns latest
- GET 404 when none
- Re-run replaces
- 401 unauthenticated
- 403 wrong user
- 404 not found

## File Structure

```
backend/app/consistency/
  __init__.py
  models.py          # ConsistencyOutcome, ConsistencyRule, ConsistencyFinding, ConsistencyResult
  engine.py          # check_application_consistency()

backend/app/seed/
  consistency.py     # CONSISTENCY_RULES list, load_consistency_rules()

backend/app/repositories/
  consistency.py     # ConsistencyRepository (create/find for application)

backend/app/api/
  consistency.py     # 2 endpoints

backend/tests/
  test_consistency_engine.py    # ~11 tests
  test_consistency_api.py       # ~7 tests

frontend/src/types/api.ts      # Add ConsistencyResult, ConsistencyFinding, ConsistencyOutcome
frontend/src/lib/api.ts        # Add checkConsistency(), getConsistency()
frontend/src/pages/staff/ApplicationDetailPage.tsx   # Add consistency section
frontend/src/pages/applicant/ApplicationDetailPage.tsx  # Add consistency section

supabase/migrations/004_consistency.sql
```
