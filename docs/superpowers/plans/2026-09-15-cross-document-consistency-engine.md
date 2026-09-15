# Cross-Document Consistency Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a deterministic cross-document consistency engine comparing extracted fields across documents for the same application, using 18 workbook rules.

**Architecture:** Seed config defines 18 ConsistencyRule objects mapping canonical fields to document requirement keys. Engine groups extracted fields by name, compares values across documents per rule. Results persisted in new DB tables, exposed via 2 API endpoints, displayed in frontend.

**Tech Stack:** Python 3.12+, Pydantic v2, FastAPI, Supabase PostgreSQL, React + TypeScript + Tailwind v4.

## Global Constraints

- No LLM, RAG, embeddings, or OCR
- MUST MATCH comparison only — no other comparison types
- No normalization (exact string comparison)
- On-demand execution (not event-driven)
- Consistency warnings only — never legal rejection
- Reuse existing extraction, document, auth, and audit patterns
- Current stable releases only; no deprecated APIs

---

## File Structure

```
Create:
  backend/app/consistency/__init__.py
  backend/app/consistency/models.py
  backend/app/consistency/engine.py
  backend/app/seed/consistency.py
  backend/app/repositories/consistency.py
  backend/app/api/consistency.py
  backend/tests/test_consistency_engine.py
  backend/tests/test_consistency_api.py
  supabase/migrations/004_consistency.sql

Modify:
  backend/app/seed/__init__.py          (add export)
  backend/app/main.py                   (add router)
  backend/app/repositories/__init__.py  (if exists, add export)
  frontend/src/types/api.ts             (add types)
  frontend/src/lib/api.ts               (add methods)
  frontend/src/pages/staff/ApplicationDetailPage.tsx
  frontend/src/pages/applicant/ApplicationDetailPage.tsx
```

---

### Task 1: Consistency Models

**Files:**
- Create: `backend/app/consistency/__init__.py`
- Create: `backend/app/consistency/models.py`
- Test: `backend/tests/test_consistency_engine.py` (models portion)

**Interfaces:**
- Consumes: none (foundational)
- Produces: `ConsistencyOutcome`, `ConsistencyRule`, `ConsistencyFinding`, `ConsistencyResult`

- [ ] **Step 1: Create module init**

```python
# backend/app/consistency/__init__.py
"""Cross-document consistency engine."""
```

- [ ] **Step 2: Write failing model tests**

```python
# backend/tests/test_consistency_engine.py
"""Tests for cross-document consistency engine."""
from __future__ import annotations

from app.consistency.models import (
    ConsistencyFinding,
    ConsistencyOutcome,
    ConsistencyResult,
    ConsistencyRule,
)


class TestConsistencyModels:
    def test_consistency_outcome_values(self):
        assert ConsistencyOutcome.VALID == "VALID"
        assert ConsistencyOutcome.REVIEW_REQUIRED == "REVIEW_REQUIRED"
        assert ConsistencyOutcome.INSUFFICIENT_DATA == "INSUFFICIENT_DATA"

    def test_consistency_rule_creation(self):
        rule = ConsistencyRule(
            id="C01",
            canonical_field="plot_area_sqm",
            affected_systems="GIDC Plan",
            evidence_field="Land/title/GIS",
            requirement_key="MUST_MATCH",
            document_keys=["D01", "D02", "D03"],
        )
        assert rule.id == "C01"
        assert rule.document_keys == ["D01", "D02", "D03"]

    def test_consistency_finding_creation(self):
        finding = ConsistencyFinding(
            rule_id="C01",
            canonical_field="plot_area_sqm",
            outcome=ConsistencyOutcome.VALID,
            observed_values={"D01": "5000", "D02": "5000"},
            expected_relationship="MUST_MATCH across [D01, D02]",
            message="Values match",
            source_ref="Workbook Consistency_Fields C01",
        )
        assert finding.outcome == ConsistencyOutcome.VALID
        assert len(finding.observed_values) == 2

    def test_consistency_result_creation(self):
        result = ConsistencyResult(
            application_id="app-1",
            outcome=ConsistencyOutcome.VALID,
            findings=[],
            checked_at="2026-09-15T10:00:00",
            rule_version="1",
        )
        assert result.application_id == "app-1"
        assert result.outcome == ConsistencyOutcome.VALID
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_consistency_engine.py -v`
Expected: FAIL — module `app.consistency.models` not found

- [ ] **Step 4: Write models implementation**

```python
# backend/app/consistency/models.py
"""Cross-document consistency models.

Defines rules and results for comparing extracted field values
across documents belonging to the same application.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ConsistencyOutcome(StrEnum):
    """Outcome of a cross-document consistency check."""
    VALID = "VALID"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ConsistencyRule(BaseModel):
    """A single cross-document consistency rule from the workbook."""
    id: str = Field(..., description="Rule ID (e.g. C01)")
    canonical_field: str = Field(..., description="Canonical field name to compare")
    affected_systems: str = Field(..., description="Affected approval systems (informational)")
    evidence_field: str = Field(..., description="Evidence field description (informational)")
    requirement_key: str = Field(..., description="Comparison type (MUST_MATCH)")
    document_keys: list[str] = Field(..., description="Document requirement keys to compare")


class ConsistencyFinding(BaseModel):
    """A single field-level consistency finding."""
    rule_id: str = Field(..., description="Consistency rule ID")
    canonical_field: str = Field(..., description="Canonical field name")
    outcome: ConsistencyOutcome = Field(..., description="Consistency outcome")
    observed_values: dict[str, Any] = Field(
        default_factory=dict,
        description="Observed values keyed by document requirement key",
    )
    expected_relationship: str = Field(
        ..., description="Expected relationship (e.g. MUST_MATCH across [D01, D02])"
    )
    message: str = Field("", description="Human-readable finding message")
    source_ref: str = Field("", description="Source reference")


class ConsistencyResult(BaseModel):
    """Full consistency check result for an application."""
    application_id: str = Field(..., description="Application ID")
    outcome: ConsistencyOutcome = Field(
        ..., description="Overall outcome (worst-case across findings)"
    )
    findings: list[ConsistencyFinding] = Field(
        default_factory=list, description="Field-level findings"
    )
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the check"
    )
    rule_version: str = Field("1", description="Version of consistency rules used")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_consistency_engine.py::TestConsistencyModels -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/consistency/__init__.py backend/app/consistency/models.py backend/tests/test_consistency_engine.py
git commit -m "feat(consistency): add data models for cross-document consistency engine"
```

---

### Task 2: Seed Config

**Files:**
- Create: `backend/app/seed/consistency.py`
- Modify: `backend/app/seed/__init__.py` (add export)

**Interfaces:**
- Consumes: `ConsistencyRule` from Task 1
- Produces: `load_consistency_rules()` function, `CONSISTENCY_RULES` list

- [ ] **Step 1: Write seed config tests**

Append to `backend/tests/test_consistency_engine.py`:

```python
from app.seed.consistency import CONSISTENCY_RULES, load_consistency_rules


class TestConsistencySeed:
    def test_load_returns_all_18_rules(self):
        rules = load_consistency_rules()
        assert len(rules) == 18

    def test_rule_ids_are_c01_through_c18(self):
        rules = load_consistency_rules()
        ids = [r.id for r in rules]
        expected = [f"C{i:02d}" for i in range(1, 19)]
        assert ids == expected

    def test_all_rules_are_must_match(self):
        rules = load_consistency_rules()
        assert all(r.requirement_key == "MUST_MATCH" for r in rules)

    def test_multi_doc_rules_have_multiple_keys(self):
        rules = load_consistency_rules()
        multi_doc = [r for r in rules if len(r.document_keys) > 1]
        assert len(multi_doc) >= 10  # at least 10 rules compare multiple docs

    def test_document_keys_are_valid_format(self):
        rules = load_consistency_rules()
        for rule in rules:
            for key in rule.document_keys:
                assert key.startswith("D"), f"Invalid doc key {key} in rule {rule.id}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_consistency_engine.py::TestConsistencySeed -v`
Expected: FAIL — module `app.seed.consistency` not found

- [ ] **Step 3: Write seed config implementation**

```python
# backend/app/seed/consistency.py
"""Cross-document consistency rules from the frozen workbook.

Consistency_Fields Sheet
========================

18 canonical fields that MUST MATCH across affected systems/documents.
Each rule maps a canonical field to the document requirement keys
that should carry that field's value.

Source: SIH_130_Gujarat_Chemical_Final_Verified_Dataset.xlsx → Consistency_Fields
"""
from __future__ import annotations

from app.consistency.models import ConsistencyRule


CONSISTENCY_RULES: list[ConsistencyRule] = [
    ConsistencyRule(
        id="C01",
        canonical_field="plot_area_sqm",
        affected_systems="GIDC Plan",
        evidence_field="Land/title/GIS",
        requirement_key="MUST_MATCH",
        document_keys=["D01", "D02", "D03"],
    ),
    ConsistencyRule(
        id="C02",
        canonical_field="builtup_area_sqm",
        affected_systems="GIDC Plan / BU",
        evidence_field="Architectural drawings",
        requirement_key="MUST_MATCH",
        document_keys=["D04"],
    ),
    ConsistencyRule(
        id="C03",
        canonical_field="production_capacity",
        affected_systems="GPCB / EC",
        evidence_field="Process/product schedule",
        requirement_key="MUST_MATCH",
        document_keys=["D08", "D09"],
    ),
    ConsistencyRule(
        id="C04",
        canonical_field="product_names",
        affected_systems="GPCB / EC / factory",
        evidence_field="Product list",
        requirement_key="MUST_MATCH",
        document_keys=["D08", "D09"],
    ),
    ConsistencyRule(
        id="C05",
        canonical_field="raw_materials",
        affected_systems="GPCB / factory / MSIHC",
        evidence_field="Material list",
        requirement_key="MUST_MATCH",
        document_keys=["D09", "D14"],
    ),
    ConsistencyRule(
        id="C06",
        canonical_field="hazardous_chemical_max_quantity",
        affected_systems="MSIHC / GPCB / PESO",
        evidence_field="Storage inventory",
        requirement_key="MUST_MATCH",
        document_keys=["D11", "D16"],
    ),
    ConsistencyRule(
        id="C07",
        canonical_field="fresh_water_requirement",
        affected_systems="GIDC Water / GPCB / EC",
        evidence_field="Water balance",
        requirement_key="MUST_MATCH",
        document_keys=["D07"],
    ),
    ConsistencyRule(
        id="C08",
        canonical_field="effluent_generation",
        affected_systems="GIDC Drainage / GPCB / EC",
        evidence_field="Water balance + ETP",
        requirement_key="MUST_MATCH",
        document_keys=["D06", "D07"],
    ),
    ConsistencyRule(
        id="C09",
        canonical_field="ETP_capacity",
        affected_systems="GIDC Drainage / GPCB",
        evidence_field="ETP drawing",
        requirement_key="MUST_MATCH",
        document_keys=["D06"],
    ),
    ConsistencyRule(
        id="C10",
        canonical_field="hazardous_waste_quantity",
        affected_systems="GPCB / HOWM",
        evidence_field="Waste inventory",
        requirement_key="MUST_MATCH",
        document_keys=["D10"],
    ),
    ConsistencyRule(
        id="C11",
        canonical_field="power_demand_kVA",
        affected_systems="DISCOM / GERC / CEICED",
        evidence_field="Load list / estimate",
        requirement_key="MUST_MATCH",
        document_keys=["D13"],
    ),
    ConsistencyRule(
        id="C12",
        canonical_field="DG_capacity",
        affected_systems="DISCOM / CEICED / PESO if applicable",
        evidence_field="DG datasheet",
        requirement_key="MUST_MATCH",
        document_keys=["D13", "D16"],
    ),
    ConsistencyRule(
        id="C13",
        canonical_field="building_height",
        affected_systems="GIDC / Fire / BU / Lift",
        evidence_field="Architectural drawings",
        requirement_key="MUST_MATCH",
        document_keys=["D04", "D12"],
    ),
    ConsistencyRule(
        id="C14",
        canonical_field="worker_count",
        affected_systems="Factory / labour",
        evidence_field="Manpower plan",
        requirement_key="MUST_MATCH",
        document_keys=["D14"],
    ),
    ConsistencyRule(
        id="C15",
        canonical_field="plot_or_survey_identifier",
        affected_systems="GIDC / land / EC",
        evidence_field="All land documents",
        requirement_key="MUST_MATCH",
        document_keys=["D01", "D02", "D03"],
    ),
    ConsistencyRule(
        id="C16",
        canonical_field="applicant/company_name",
        affected_systems="All portals",
        evidence_field="Corporate documents",
        requirement_key="MUST_MATCH",
        document_keys=[
            "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09",
            "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17",
        ],
    ),
    ConsistencyRule(
        id="C17",
        canonical_field="address",
        affected_systems="All authorities",
        evidence_field="Registered/site address",
        requirement_key="MUST_MATCH",
        document_keys=[
            "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09",
            "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17",
        ],
    ),
    ConsistencyRule(
        id="C18",
        canonical_field="legal_entity_type",
        affected_systems="IFP / labour / company docs",
        evidence_field="Constitution documents",
        requirement_key="MUST_MATCH",
        document_keys=["D14"],
    ),
]


def load_consistency_rules() -> list[ConsistencyRule]:
    """Return all cross-document consistency rules from the workbook."""
    return list(CONSISTENCY_RULES)
```

- [ ] **Step 4: Update seed __init__.py**

```python
# Add to backend/app/seed/__init__.py:
from app.seed.consistency import (
    load_consistency_rules as load_consistency_rules,
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_consistency_engine.py::TestConsistencySeed -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/seed/consistency.py backend/app/seed/__init__.py
git commit -m "feat(consistency): add 18 workbook consistency rules seed config"
```

---

### Task 3: Consistency Engine

**Files:**
- Create: `backend/app/consistency/engine.py`
- Modify: `backend/tests/test_consistency_engine.py` (add engine tests)

**Interfaces:**
- Consumes: `ConsistencyRule`, `ConsistencyFinding`, `ConsistencyResult`, `ConsistencyOutcome` from Task 1; `ExtractedField` from extraction models
- Produces: `check_application_consistency()` function

- [ ] **Step 1: Write failing engine tests**

Append to `backend/tests/test_consistency_engine.py`:

```python
from app.consistency.engine import check_application_consistency
from app.extraction.models import ExtractedField


def _make_field(doc_id: str, app_id: str, field_name: str, value: str | None) -> ExtractedField:
    """Helper to create an ExtractedField for testing."""
    return ExtractedField(
        document_id=doc_id,
        application_id=app_id,
        field_name=field_name,
        field_value=value,
        field_type="string",
    )


# Mapping from document_id to requirement_key for testing
DOC_REQ_MAP = {
    "doc-D01": "D01",
    "doc-D02": "D02",
    "doc-D03": "D03",
    "doc-D04": "D04",
    "doc-D05": "D05",
    "doc-D06": "D06",
    "doc-D07": "D07",
    "doc-D08": "D08",
    "doc-D09": "D09",
    "doc-D10": "D10",
    "doc-D11": "D11",
    "doc-D12": "D12",
    "doc-D13": "D13",
    "doc-D14": "D14",
    "doc-D15": "D15",
    "doc-D16": "D16",
    "doc-D17": "D17",
}


RULES = [
    ConsistencyRule(
        id="C01", canonical_field="plot_area_sqm",
        affected_systems="GIDC Plan", evidence_field="Land/title/GIS",
        requirement_key="MUST_MATCH", document_keys=["D01", "D02"],
    ),
    ConsistencyRule(
        id="C02", canonical_field="builtup_area_sqm",
        affected_systems="GIDC Plan / BU", evidence_field="Architectural drawings",
        requirement_key="MUST_MATCH", document_keys=["D04"],
    ),
]


class TestConsistencyEngine:
    def test_all_identical_values_returns_valid(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        assert result.outcome == ConsistencyOutcome.VALID
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID

    def test_mismatched_values_returns_review_required(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "4800"),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        assert result.outcome == ConsistencyOutcome.REVIEW_REQUIRED
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.REVIEW_REQUIRED
        assert "D01" in c01.observed_values
        assert "D02" in c01.observed_values

    def test_no_values_returns_insufficient_data(self):
        fields = []
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        assert result.outcome == ConsistencyOutcome.INSUFFICIENT_DATA
        assert all(f.outcome == ConsistencyOutcome.INSUFFICIENT_DATA for f in result.findings)

    def test_single_document_has_value_returns_valid(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID

    def test_partial_values_matching_returns_valid(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID

    def test_empty_string_treated_as_no_value(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", ""),
            _make_field("doc-D02", "app-1", "plot_area_sqm", ""),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.INSUFFICIENT_DATA

    def test_single_doc_rule_always_valid(self):
        fields = [
            _make_field("doc-D04", "app-1", "builtup_area_sqm", "2000"),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        c02 = [f for f in result.findings if f.rule_id == "C02"][0]
        assert c02.outcome == ConsistencyOutcome.VALID

    def test_mixed_outcomes_worst_case(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "4800"),
            _make_field("doc-D04", "app-1", "builtup_area_sqm", "2000"),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        assert result.outcome == ConsistencyOutcome.REVIEW_REQUIRED

    def test_empty_fields_all_insufficient_data(self):
        result = check_application_consistency("app-1", [], RULES, DOC_REQ_MAP)
        assert len(result.findings) == 2
        assert all(f.outcome == ConsistencyOutcome.INSUFFICIENT_DATA for f in result.findings)

    def test_deterministic_finding_order(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D04", "app-1", "builtup_area_sqm", "2000"),
        ]
        result1 = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        result2 = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        assert [f.rule_id for f in result1.findings] == [f.rule_id for f in result2.findings]

    def test_null_field_value_treated_as_no_value(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", None),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
        ]
        result = check_application_consistency("app-1", fields, RULES, DOC_REQ_MAP)
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_consistency_engine.py::TestConsistencyEngine -v`
Expected: FAIL — `check_application_consistency` not found

- [ ] **Step 3: Write engine implementation**

```python
# backend/app/consistency/engine.py
"""Deterministic cross-document consistency engine.

Compares extracted field values across documents belonging to the
same application using the workbook's Consistency_Fields rules.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.consistency.models import (
    ConsistencyFinding,
    ConsistencyOutcome,
    ConsistencyResult,
    ConsistencyRule,
)
from app.extraction.models import ExtractedField


def check_application_consistency(
    application_id: str,
    extracted_fields: list[ExtractedField],
    rules: list[ConsistencyRule],
    doc_req_map: dict[str, str],
) -> ConsistencyResult:
    """Compare extracted field values across documents for each consistency rule.

    Args:
        application_id: The application being checked.
        extracted_fields: All extracted fields for this application.
        rules: Consistency rules to evaluate.
        doc_req_map: Mapping from document_id to requirement_key (e.g. "doc-uuid" -> "D01").

    Returns:
        ConsistencyResult with per-rule findings and aggregated outcome.
    """
    # Group extracted fields by canonical field name → {req_key: value}
    fields_by_name: dict[str, dict[str, Any]] = {}
    for field in extracted_fields:
        if field.field_name not in fields_by_name:
            fields_by_name[field.field_name] = {}
        req_key = doc_req_map.get(field.document_id)
        if req_key:
            # Only keep non-empty values
            if field.field_value is not None and field.field_value != "":
                fields_by_name[field.field_name][req_key] = field.field_value

    findings: list[ConsistencyFinding] = []

    for rule in rules:
        # Collect values from the rule's document_keys
        field_values = fields_by_name.get(rule.canonical_field, {})
        observed: dict[str, Any] = {}
        for dk in rule.document_keys:
            if dk in field_values:
                observed[dk] = field_values[dk]

        # Determine outcome
        non_empty = {k: v for k, v in observed.items() if v is not None and v != ""}

        if len(non_empty) == 0:
            outcome = ConsistencyOutcome.INSUFFICIENT_DATA
            message = f"No extracted values found for {rule.canonical_field} in any of {rule.document_keys}"
        elif len(non_empty) == 1:
            outcome = ConsistencyOutcome.VALID
            key = list(non_empty.keys())[0]
            message = f"Only one document ({key}) has a value for {rule.canonical_field}; nothing to compare"
        else:
            values = list(non_empty.values())
            if all(v == values[0] for v in values):
                outcome = ConsistencyOutcome.VALID
                message = f"All {len(non_empty)} documents agree on {rule.canonical_field}"
            else:
                outcome = ConsistencyOutcome.REVIEW_REQUIRED
                message = (
                    f"Documents disagree on {rule.canonical_field}: "
                    + ", ".join(f"{k}={v}" for k, v in non_empty.items())
                )

        findings.append(
            ConsistencyFinding(
                rule_id=rule.id,
                canonical_field=rule.canonical_field,
                outcome=outcome,
                observed_values=observed,
                expected_relationship=f"{rule.requirement_key} across {rule.document_keys}",
                message=message,
                source_ref=f"Workbook Consistency_Fields {rule.id}",
            )
        )

    # Aggregate: worst outcome across all findings
    outcome_priority = {
        ConsistencyOutcome.VALID: 0,
        ConsistencyOutcome.INSUFFICIENT_DATA: 1,
        ConsistencyOutcome.REVIEW_REQUIRED: 2,
    }
    worst = ConsistencyOutcome.VALID
    for f in findings:
        if outcome_priority[f.outcome] > outcome_priority[worst]:
            worst = f.outcome

    return ConsistencyResult(
        application_id=application_id,
        outcome=worst,
        findings=findings,
        checked_at=datetime.utcnow(),
        rule_version="1",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_consistency_engine.py -v`
Expected: All tests pass (4 model + 5 seed + 11 engine = 20 total)

- [ ] **Step 5: Commit**

```bash
git add backend/app/consistency/engine.py backend/tests/test_consistency_engine.py
git commit -m "feat(consistency): implement deterministic consistency engine"
```

---

### Task 4: Database Migration

**Files:**
- Create: `supabase/migrations/004_consistency.sql`

**Interfaces:**
- Consumes: existing `applications` table (from migration 001)
- Produces: `consistency_results`, `consistency_findings` tables, `consistency_outcome` enum

- [ ] **Step 1: Write migration file**

```sql
-- supabase/migrations/004_consistency.sql
-- Cross-document consistency engine tables

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

- [ ] **Step 2: Verify migration syntax**

Run: `cd backend && python -c "print('Migration file created')"` (no runtime SQL check needed — Supabase applies migrations)

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/004_consistency.sql
git commit -m "feat(consistency): add database migration for consistency tables"
```

---

### Task 5: Consistency Repository

**Files:**
- Create: `backend/app/repositories/consistency.py`

**Interfaces:**
- Consumes: `BaseRepository` pattern from `app.repositories.base`
- Produces: `ConsistencyRepository` with `create_result()`, `create_findings()`, `get_latest_result()`, `delete_findings_for_result()`, `delete_previous_results()`

- [ ] **Step 1: Write repository tests**

Create `backend/tests/test_consistency_api.py`:

```python
"""Tests for consistency repository and API endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.consistency.models import (
    ConsistencyFinding,
    ConsistencyOutcome,
    ConsistencyResult,
)
from app.repositories.consistency import ConsistencyRepository


class TestConsistencyRepository:
    def _make_repo(self) -> ConsistencyRepository:
        mock_client = MagicMock()
        return ConsistencyRepository(mock_client)

    def test_create_result_calls_insert(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [{"id": "result-1", "application_id": "app-1"}]
        repo.client.table.return_value.insert.return_value.execute.return_value = mock_result

        result = repo.create_result("app-1", "VALID", "2026-09-15T10:00:00", "1")
        assert result["id"] == "result-1"
        repo.client.table.assert_called_with("consistency_results")

    def test_create_findings_calls_insert(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [{"id": "finding-1"}]
        repo.client.table.return_value.insert.return_value.execute.return_value = mock_result

        findings_data = [{"result_id": "r1", "rule_id": "C01", "canonical_field": "plot_area_sqm"}]
        result = repo.create_findings(findings_data)
        assert len(result) == 1
        repo.client.table.assert_called_with("consistency_findings")

    def test_get_latest_result_returns_none_when_empty(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = []
        repo.client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result

        result = repo.get_latest_result("app-1")
        assert result is None

    def test_get_latest_result_returns_data(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [{"id": "r1", "application_id": "app-1", "outcome": "VALID"}]
        repo.client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result

        result = repo.get_latest_result("app-1")
        assert result is not None
        assert result["id"] == "r1"

    def test_list_findings_for_result(self):
        repo = self._make_repo()
        mock_result = MagicMock()
        mock_result.data = [{"id": "f1", "rule_id": "C01"}, {"id": "f2", "rule_id": "C02"}]
        repo.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result

        findings = repo.list_findings_for_result("r1")
        assert len(findings) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_consistency_api.py::TestConsistencyRepository -v`
Expected: FAIL — module `app.repositories.consistency` not found

- [ ] **Step 3: Write repository implementation**

```python
# backend/app/repositories/consistency.py
"""Consistency repository — CRUD for consistency_results and consistency_findings."""
from __future__ import annotations

from typing import Any

from app.repositories.base import BaseRepository


class ConsistencyRepository(BaseRepository):
    """Repository for cross-document consistency operations."""

    def __init__(self, client):
        super().__init__(client, "consistency_results")

    def create_result(
        self,
        application_id: str,
        outcome: str,
        checked_at: str,
        rule_version: str,
    ) -> dict[str, Any]:
        """Create a consistency result record."""
        result = (
            self.client.table("consistency_results")
            .insert({
                "application_id": application_id,
                "outcome": outcome,
                "checked_at": checked_at,
                "rule_version": rule_version,
            })
            .execute()
        )
        return result.data[0]

    def create_findings(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Create multiple consistency findings in one call."""
        if not findings:
            return []
        result = (
            self.client.table("consistency_findings")
            .insert(findings)
            .execute()
        )
        return result.data or []

    def get_latest_result(self, application_id: str) -> dict[str, Any] | None:
        """Get the most recent consistency result for an application."""
        result = (
            self.client.table("consistency_results")
            .select("*")
            .eq("application_id", application_id)
            .order("checked_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_findings_for_result(self, result_id: str) -> list[dict[str, Any]]:
        """List all findings for a consistency result."""
        result = (
            self.client.table("consistency_findings")
            .select("*")
            .eq("result_id", result_id)
            .execute()
        )
        return result.data or []

    def delete_findings_for_result(self, result_id: str) -> None:
        """Delete all findings for a consistency result."""
        self.client.table("consistency_findings").delete().eq(
            "result_id", result_id
        ).execute()

    def delete_previous_results(self, application_id: str) -> None:
        """Delete all previous consistency results for an application (for re-run)."""
        # Get existing results
        existing = (
            self.client.table("consistency_results")
            .select("id")
            .eq("application_id", application_id)
            .execute()
        )
        for row in (existing.data or []):
            self.delete_findings_for_result(row["id"])
        self.client.table("consistency_results").delete().eq(
            "application_id", application_id
        ).execute()

    def get_extracted_fields_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """Get all extracted fields for an application."""
        result = (
            self.client.table("extracted_fields")
            .select("*")
            .eq("application_id", application_id)
            .execute()
        )
        return result.data or []

    def get_document_req_map(self, application_id: str) -> dict[str, str]:
        """Get mapping from document_id to requirement_key for an application."""
        result = (
            self.client.table("documents")
            .select("id, requirement_key")
            .eq("application_id", application_id)
            .execute()
        )
        return {row["id"]: row["requirement_key"] for row in (result.data or [])}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_consistency_api.py::TestConsistencyRepository -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/consistency.py backend/tests/test_consistency_api.py
git commit -m "feat(consistency): add consistency repository with CRUD operations"
```

---

### Task 6: API Endpoints

**Files:**
- Create: `backend/app/api/consistency.py`
- Modify: `backend/app/main.py` (add router)
- Modify: `backend/tests/test_consistency_api.py` (add endpoint tests)

**Interfaces:**
- Consumes: `ConsistencyRepository` from Task 5; `check_application_consistency` from Task 3; auth dependencies from `app.auth.dependencies`
- Produces: `POST /applications/{app_id}/consistency/check`, `GET /applications/{app_id}/consistency`

- [ ] **Step 1: Write failing API tests**

Append to `backend/tests/test_consistency_api.py`:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.consistency import router
from app.auth.models import SystemRole, UserContext


class TestConsistencyAPI:
    def _make_client(self, user: UserContext | None = None) -> TestClient:
        app = FastAPI()
        app.include_router(router)

        if user:
            def override_get_user():
                return user
            app.dependency_overrides[get_current_user] = override_get_user

        return TestClient(app)

    def test_post_check_returns_200(self):
        user = UserContext(
            user_id="user-1", email="test@test.com",
            role=SystemRole.APPLICANT, raw_claims={},
        )
        client = self._make_client(user)

        with patch("app.api.consistency.get_supabase") as mock_sb, \
             patch("app.api.consistency.check_application_consistency") as mock_check, \
             patch("app.api.consistency.check_application_ownership") as mock_own:
            mock_own.return_value = None
            mock_repo = MagicMock()
            mock_repo.get_extracted_fields_for_application.return_value = []
            mock_repo.get_document_req_map.return_value = {}
            mock_repo.delete_previous_results.return_value = None
            mock_repo.create_result.return_value = {"id": "r1"}
            mock_repo.create_findings.return_value = []
            mock_sb.return_value = mock_repo

            mock_check.return_value = ConsistencyResult(
                application_id="app-1",
                outcome=ConsistencyOutcome.VALID,
                findings=[],
            )

            response = client.post("/applications/app-1/consistency/check")
            assert response.status_code == 200

    def test_get_returns_404_when_no_check(self):
        user = UserContext(
            user_id="user-1", email="test@test.com",
            role=SystemRole.APPLICANT, raw_claims={},
        )
        client = self._make_client(user)

        with patch("app.api.consistency.get_supabase") as mock_sb, \
             patch("app.api.consistency.check_application_ownership") as mock_own:
            mock_own.return_value = None
            mock_repo = MagicMock()
            mock_repo.get_latest_result.return_value = None
            mock_sb.return_value = mock_repo

            response = client.get("/applications/app-1/consistency")
            assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_consistency_api.py::TestConsistencyAPI -v`
Expected: FAIL — module `app.api.consistency` not found

- [ ] **Step 3: Write API implementation**

```python
# backend/app/api/consistency.py
"""API endpoints for cross-document consistency checks."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import (
    check_application_ownership,
    get_current_user,
    require_any_permission,
)
from app.auth.models import UserContext
from app.consistency.engine import check_application_consistency
from app.consistency.models import ConsistencyOutcome
from app.core.config import get_settings
from app.db.client import get_supabase
from app.repositories.consistency import ConsistencyRepository
from app.seed.consistency import load_consistency_rules
from auth.permissions import Permission

router = APIRouter()


@router.post("/applications/{app_id}/consistency/check")
async def run_consistency_check(
    app_id: str,
    user: UserContext = Depends(get_current_user),
    _perm: None = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
    _own: None = Depends(check_application_ownership),
):
    """Run a cross-document consistency check for an application."""
    sb = get_supabase()
    repo = ConsistencyRepository(sb)

    # Get extracted fields and document mapping
    fields_data = repo.get_extracted_fields_for_application(app_id)
    doc_map = repo.get_document_req_map(app_id)

    # Convert to ExtractedField models
    from app.extraction.models import ExtractedField
    fields = [ExtractedField(**f) for f in fields_data]

    # Run engine
    rules = load_consistency_rules()
    result = check_application_consistency(app_id, fields, rules, doc_map)

    # Persist: delete previous, store new
    repo.delete_previous_results(app_id)
    now = datetime.utcnow().isoformat()
    result_row = repo.create_result(
        app_id, result.outcome.value, now, result.rule_version
    )

    findings_data = [
        {
            "result_id": result_row["id"],
            "application_id": app_id,
            "rule_id": f.rule_id,
            "canonical_field": f.canonical_field,
            "outcome": f.outcome.value,
            "observed_values": f.observed_values,
            "expected_relationship": f.expected_relationship,
            "message": f.message,
            "source_ref": f.source_ref,
        }
        for f in result.findings
    ]
    repo.create_findings(findings_data)

    return {
        "application_id": result.application_id,
        "outcome": result.outcome.value,
        "findings": [
            {
                "rule_id": f.rule_id,
                "canonical_field": f.canonical_field,
                "outcome": f.outcome.value,
                "observed_values": f.observed_values,
                "expected_relationship": f.expected_relationship,
                "message": f.message,
                "source_ref": f.source_ref,
            }
            for f in result.findings
        ],
        "checked_at": now,
        "rule_version": result.rule_version,
    }


@router.get("/applications/{app_id}/consistency")
async def get_consistency(
    app_id: str,
    user: UserContext = Depends(get_current_user),
    _perm: None = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
    _own: None = Depends(check_application_ownership),
):
    """Get the latest consistency check result for an application."""
    sb = get_supabase()
    repo = ConsistencyRepository(sb)

    result_row = repo.get_latest_result(app_id)
    if not result_row:
        raise HTTPException(status_code=404, detail="No consistency check found")

    findings = repo.list_findings_for_result(result_row["id"])

    return {
        "application_id": result_row["application_id"],
        "outcome": result_row["outcome"],
        "findings": [
            {
                "rule_id": f["rule_id"],
                "canonical_field": f["canonical_field"],
                "outcome": f["outcome"],
                "observed_values": f["observed_values"],
                "expected_relationship": f["expected_relationship"],
                "message": f["message"],
                "source_ref": f["source_ref"],
            }
            for f in findings
        ],
        "checked_at": result_row["checked_at"],
        "rule_version": result_row["rule_version"],
    }
```

- [ ] **Step 4: Add router to main.py**

Add to `backend/app/main.py` imports and include:
```python
from app.api.consistency import router as consistency_router
app.include_router(consistency_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_consistency_api.py -v`
Expected: All tests pass (5 repo + 2 API = 7)

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/consistency.py backend/app/main.py backend/tests/test_consistency_api.py
git commit -m "feat(consistency): add API endpoints for consistency checks"
```

---

### Task 7: Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/api.ts` (add types)
- Modify: `frontend/src/lib/api.ts` (add methods)

**Interfaces:**
- Consumes: existing API client patterns
- Produces: TypeScript types + API methods for frontend

- [ ] **Step 1: Add TypeScript types**

Append to `frontend/src/types/api.ts`:

```typescript
export type ConsistencyOutcome = "VALID" | "REVIEW_REQUIRED" | "INSUFFICIENT_DATA";

export interface ConsistencyFinding {
  rule_id: string;
  canonical_field: string;
  outcome: ConsistencyOutcome;
  observed_values: Record<string, unknown>;
  expected_relationship: string;
  message: string;
  source_ref: string;
}

export interface ConsistencyResult {
  application_id: string;
  outcome: ConsistencyOutcome;
  findings: ConsistencyFinding[];
  checked_at: string;
  rule_version: string;
}
```

- [ ] **Step 2: Add API methods**

Append to `frontend/src/lib/api.ts`:

```typescript
export async function checkConsistency(appId: string): Promise<ConsistencyResult> {
  const res = await fetch(`${API_BASE}/applications/${appId}/consistency/check`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`Consistency check failed: ${res.status}`);
  return res.json();
}

export async function getConsistency(appId: string): Promise<ConsistencyResult | null> {
  const res = await fetch(`${API_BASE}/applications/${appId}/consistency`, {
    headers: authHeaders(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Get consistency failed: ${res.status}`);
  return res.json();
}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/lib/api.ts
git commit -m "feat(consistency): add frontend types and API client methods"
```

---

### Task 8: Frontend UI — Staff Application Detail

**Files:**
- Modify: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `checkConsistency()`, `getConsistency()` from Task 7; `ConsistencyResult`, `ConsistencyFinding` types
- Produces: Consistency section in staff application detail page

- [ ] **Step 1: Add consistency state and handlers**

Add to the component's state:
```typescript
const [consistency, setConsistency] = useState<ConsistencyResult | null>(null);
const [consistencyLoading, setConsistencyLoading] = useState(false);
```

Add handler:
```typescript
const handleRunConsistency = async () => {
  setConsistencyLoading(true);
  try {
    const result = await checkConsistency(id!);
    setConsistency(result);
  } catch (err) {
    console.error("Consistency check failed", err);
  } finally {
    setConsistencyLoading(false);
  }
};

useEffect(() => {
  getConsistency(id!).then(setConsistency).catch(() => {});
}, [id]);
```

- [ ] **Step 2: Add consistency section JSX**

Add after the document section:
```tsx
{/* Consistency Section */}
<div className="mt-6 border-t pt-4">
  <div className="flex items-center justify-between mb-3">
    <h3 className="text-lg font-semibold">Cross-Document Consistency</h3>
    <button
      onClick={handleRunConsistency}
      disabled={consistencyLoading}
      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
    >
      {consistencyLoading ? "Checking..." : "Run Check"}
    </button>
  </div>

  {consistency && (
    <div>
      <div className="mb-2">
        <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${
          consistency.outcome === "VALID" ? "bg-green-100 text-green-800" :
          consistency.outcome === "REVIEW_REQUIRED" ? "bg-yellow-100 text-yellow-800" :
          "bg-gray-100 text-gray-800"
        }`}>
          {consistency.outcome}
        </span>
        <span className="ml-2 text-xs text-gray-500">
          Checked: {new Date(consistency.checked_at).toLocaleString()}
        </span>
      </div>

      {consistency.findings.length > 0 ? (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-1">Rule</th>
              <th className="text-left py-1">Field</th>
              <th className="text-left py-1">Status</th>
              <th className="text-left py-1">Message</th>
            </tr>
          </thead>
          <tbody>
            {consistency.findings.map((f) => (
              <tr key={f.rule_id} className="border-b">
                <td className="py-1">{f.rule_id}</td>
                <td className="py-1">{f.canonical_field}</td>
                <td className="py-1">
                  <span className={`inline-block px-1.5 py-0.5 text-xs rounded ${
                    f.outcome === "VALID" ? "bg-green-50 text-green-700" :
                    f.outcome === "REVIEW_REQUIRED" ? "bg-yellow-50 text-yellow-700" :
                    "bg-gray-50 text-gray-700"
                  }`}>
                    {f.outcome}
                  </span>
                </td>
                <td className="py-1 text-gray-600">{f.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="text-sm text-gray-500">No findings.</p>
      )}
    </div>
  )}
</div>
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npx tsc --noEmit && npx vite build`
Expected: 0 errors, build success

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/staff/ApplicationDetailPage.tsx
git commit -m "feat(consistency): add consistency section to staff application detail"
```

---

### Task 9: Frontend UI — Applicant Application Detail

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`

**Interfaces:**
- Same as Task 8

- [ ] **Step 1: Add consistency section (same pattern as Task 8)**

Copy the same state, handlers, and JSX from Task 8 into the applicant detail page. The only difference is the styling should match the applicant page's existing patterns.

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit && npx vite build`
Expected: 0 errors, build success

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/applicant/ApplicationDetailPage.tsx
git commit -m "feat(consistency): add consistency section to applicant application detail"
```

---

### Task 10: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run full backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests pass, 0 failures

- [ ] **Step 2: Run backend lint**

Run: `cd backend && python -m ruff check app/ tests/`
Expected: Clean

- [ ] **Step 3: Run frontend checks**

Run: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`
Expected: 0 errors, build success

- [ ] **Step 4: Update ARCHITECTURE.md**

Add Phase 3E section to ARCHITECTURE.md with:
- Files created
- Implementation summary
- Test count
- Known limitations

- [ ] **Step 5: Update PRD.md**

Update "Next engineering step" line.

- [ ] **Step 6: Commit documentation**

```bash
git add ARCHITECTURE.md PRD.md
git commit -m "docs: update architecture and PRD for Phase 3E consistency engine"
```
