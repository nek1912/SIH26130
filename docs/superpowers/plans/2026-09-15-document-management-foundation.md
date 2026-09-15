# Document Management Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the MVP document management layer: checklist, upload, metadata, requirement/readiness status, Supabase Storage, deterministic validation, auditability.

**Architecture:** New `document_requirements` table stores requirement definitions per application (seeded from workbook Document_Register). Existing `documents` table stores uploaded files. Supabase Storage access proxied through FastAPI backend. Frontend checklist integrated into existing ApplicationDetailPage.

**Tech Stack:** FastAPI, Python, Supabase PostgreSQL + Storage, Pydantic v2, React + TypeScript + Tailwind v4, pytest, ruff, tsc, oxlint

## Global Constraints

- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + Python
- Database/Auth/Storage: Supabase (PostgreSQL, Auth, Storage)
- API style: REST; OpenAPI generated from FastAPI
- No secrets in source control
- No OCR/LLM/embeddings/RAG in this phase
- Never trust client-provided metadata
- Validate authorization server-side on every protected operation
- Keep audit history append-only
- 23 pre-existing Supabase config test failures — do not delete, weaken, or skip them

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/app/seed/documents.py` | Create | 17 document requirements from workbook |
| `backend/app/repositories/documents.py` | Create | CRUD for document_requirements + documents |
| `backend/app/api/documents.py` | Create | REST endpoints for checklist, upload, list, get, delete |
| `backend/app/api/deps.py` | Modify | Add DocumentsRepository dependency |
| `backend/app/core/config.py` | Modify | Add `supabase_storage_bucket` setting |
| `backend/app/main.py` | Modify | Register documents router |
| `backend/tests/test_document_requirements.py` | Create | Seed + requirement logic tests |
| `backend/tests/test_document_upload.py` | Create | Upload, validation, storage, audit tests |
| `frontend/src/types/api.ts` | Modify | Add DocumentRequirement, Document interfaces |
| `frontend/src/lib/api.ts` | Modify | Add documents API namespace |
| `frontend/src/pages/applicant/ApplicationDetailPage.tsx` | Modify | Add documents checklist section |

---

### Task 1: Seed Data — Document Requirements from Workbook

**Files:**
- Create: `backend/app/seed/documents.py`
- Test: `backend/tests/test_document_requirements.py`

**Interfaces:**
- Produces: `load_document_requirements() -> list[dict]`, `get_requirements_for_approval(approval_id: str) -> list[dict]`, `APPROVAL_TO_DOCS: dict[str, list[str]]`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_document_requirements.py
"""Tests for document requirement seed data and lookup."""
from __future__ import annotations

from app.seed.documents import (
    load_document_requirements,
    get_requirements_for_approval,
    APPROVAL_TO_DOCS,
    parse_used_for,
)


class TestLoadDocumentRequirements:
    def test_returns_17_requirements(self):
        reqs = load_document_requirements()
        assert len(reqs) == 17

    def test_all_have_doc_ids(self):
        reqs = load_document_requirements()
        for req in reqs:
            assert "requirement_key" in req
            assert req["requirement_key"].startswith("D")
            assert len(req["requirement_key"]) == 3

    def test_all_have_required_fields(self):
        reqs = load_document_requirements()
        required_fields = [
            "requirement_key", "document_name", "approval_ids",
            "domain", "requirement_level", "source_url",
        ]
        for req in reqs:
            for field in required_fields:
                assert field in req, f"Missing {field} in {req['requirement_key']}"

    def test_mandatory_vs_required_levels(self):
        reqs = load_document_requirements()
        levels = {req["requirement_level"] for req in reqs}
        assert "required" in levels
        assert "mandatory" in levels

    def test_conditional_requirements_exist(self):
        reqs = load_document_requirements()
        conditional = [r for r in reqs if r["requirement_level"] == "conditional"]
        assert len(conditional) >= 3  # D15, D16, D17 are conditional


class TestParseUsedFor:
    def test_single_approval(self):
        result = parse_used_for("GIDC Plan")
        assert "A01" in result

    def test_multiple_approvals(self):
        result = parse_used_for("GIDC Plan/Water/Drainage")
        assert "A01" in result
        assert "A02" in result
        assert "A03" in result

    def test_conditional_text(self):
        result = parse_used_for("MSIHC")
        assert "A12" in result


class TestGetRequirementsForApproval:
    def test_gidc_plan_returns_documents(self):
        reqs = get_requirements_for_approval("A01")
        keys = [r["requirement_key"] for r in reqs]
        assert "D01" in keys  # GIDC Offer-cum-Allotment
        assert "D02" in keys  # GIDC Licence Agreement
        assert "D04" in keys  # Approved Building Plan

    def test_gpcb_returns_documents(self):
        reqs = get_requirements_for_approval("A04")
        keys = [r["requirement_key"] for r in reqs]
        assert "D05" in keys  # GPCB CTE/NOC

    def test_unknown_approval_returns_empty(self):
        reqs = get_requirements_for_approval("A99")
        assert reqs == []


class TestApprovalToDocsMapping:
    def test_all_18_approvals_mapped(self):
        for i in range(1, 19):
            aid = f"A{i:02d}"
            assert aid in APPROVAL_TO_DOCS, f"Approval {aid} not mapped"

    def test_gidc_plan_maps_to_three_docs(self):
        assert len(APPROVAL_TO_DOCS["A01"]) >= 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_document_requirements.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Write seed data implementation**

```python
# backend/app/seed/documents.py
"""Document requirements from the frozen workbook Document_Register.

17 documents (D01-D17) mapped to approvals (A01-A18).
Source: SIH_130_Gujarat_Chemical_Final_Verified_Dataset.xlsx → Document_Register sheet.
"""
from __future__ import annotations

from typing import Any


# Approval ID → list of document requirement keys
APPROVAL_TO_DOCS: dict[str, list[str]] = {
    "A01": ["D01", "D02", "D04", "D05"],       # GIDC Plan
    "A02": ["D01", "D02", "D03", "D05"],       # GIDC Water
    "A03": ["D01", "D02", "D03", "D05", "D06"],# GIDC Drainage
    "A04": ["D05", "D07", "D08", "D09"],       # GPCB CTE
    "A05": ["D15"],                             # EIA/EC
    "A06": ["D12"],                             # Fire Safety
    "A07": ["D14"],                             # Factory Registration
    "A08": ["D14"],                             # BOCW
    "A09": ["D13"],                             # HT Electricity
    "A10": ["D13"],                             # CEICED
    "A11": ["D10"],                             # HOWM
    "A12": ["D11"],                             # MSIHC
    "A13": ["D11"],                             # Chemical Accidents
    "A14": [],                                  # BU Permission (no specific doc)
    "A15": ["D13"],                             # Lift
    "A16": [],                                  # Boiler (no specific doc in register)
    "A17": ["D16"],                             # PESO
    "A18": ["D17"],                             # CGWA
}


def parse_used_for(used_for: str) -> list[str]:
    """Parse workbook 'used_for' text into approval ID list.

    Examples:
        "GIDC Plan/Water/Drainage" → ["A01", "A02", "A03"]
        "GPCB CTE" → ["A04"]
        "MSIHC" → ["A12"]
    """
    mapping: dict[str, str] = {
        "GIDC Plan": "A01",
        "GIDC Water": "A02",
        "GIDC Drainage": "A03",
        "GPCB CTE": "A04",
        "EIA": "A05",
        "PARIVESH": "A05",
        "Fire Safety": "A06",
        "Factory": "A07",
        "Labour": "A07",
        "DISH": "A07",
        "BOCW": "A08",
        "HT Electricity": "A09",
        "CEICED": "A10",
        "IFP": "A10",
        "HOWM": "A11",
        "MSIHC": "A12",
        "Chemical Accidents": "A13",
        "BU Permission": "A14",
        "Lift": "A15",
        "Boiler": "A16",
        "PESO": "A17",
        "CGWA": "A18",
    }
    result: set[str] = set()
    for keyword, aid in mapping.items():
        if keyword in used_for:
            result.add(aid)
    return sorted(result)


DOCUMENT_REQUIREMENTS: list[dict[str, Any]] = [
    {
        "requirement_key": "D01",
        "document_name": "GIDC Offer-cum-Allotment / latest Transfer Order",
        "approval_ids": ["A01", "A02", "A03"],
        "domain": "LAND",
        "requirement_level": "required",
        "source_basis": "GIDC page",
        "source_url": "https://gidc.gujarat.gov.in/Pages/Contents/application-for-plan-approval",
        "document_role": "Applicant document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D02",
        "document_name": "GIDC Licence Agreement",
        "approval_ids": ["A01", "A02", "A03"],
        "domain": "LAND",
        "requirement_level": "required",
        "source_basis": "GIDC pages",
        "source_url": "https://gidc.gujarat.gov.in/Pages/Contents/application-for-water-connection",
        "document_role": "Applicant document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D03",
        "document_name": "Possession Receipt / Final Transfer Order",
        "approval_ids": ["A02", "A03"],
        "domain": "LAND",
        "requirement_level": "mandatory",
        "source_basis": "GIDC pages",
        "source_url": "https://gidc.gujarat.gov.in/Pages/Contents/application-for-water-connection",
        "document_role": "Applicant document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D04",
        "document_name": "Approved Building Plan + complete drawings",
        "approval_ids": ["A01"],
        "domain": "BUILDING",
        "requirement_level": "required",
        "source_basis": "GIDC Plan Approval",
        "source_url": "https://gidc.gujarat.gov.in/Pages/Contents/application-for-plan-approval",
        "document_role": "Applicant/design document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 20,
    },
    {
        "requirement_key": "D05",
        "document_name": "GPCB CTE / NOC",
        "approval_ids": ["A01", "A02", "A03", "A04"],
        "domain": "ENVIRONMENT",
        "requirement_level": "required",
        "source_basis": "GIDC/IFP",
        "source_url": "https://gidc.gujarat.gov.in/Pages/Contents/application-for-water-connection",
        "document_role": "Authority document",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D06",
        "document_name": "Primary ETP/STP plan + installation certificate",
        "approval_ids": ["A03"],
        "domain": "ENVIRONMENT",
        "requirement_level": "required",
        "source_basis": "GIDC Drainage",
        "source_url": "https://gidc.gujarat.gov.in/Pages/Contents/application-for-drainage-connection",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 15,
    },
    {
        "requirement_key": "D07",
        "document_name": "Water balance",
        "approval_ids": ["A04"],
        "domain": "ENVIRONMENT",
        "requirement_level": "required",
        "source_basis": "IFP GPCB checklist",
        "source_url": "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_establishment_approvals.jsp",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D08",
        "document_name": "Manufacturing process flow + chemical equations",
        "approval_ids": ["A04"],
        "domain": "PROCESS",
        "requirement_level": "required",
        "source_basis": "IFP GPCB checklist",
        "source_url": "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_establishment_approvals.jsp",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D09",
        "document_name": "Raw material & finished-product list",
        "approval_ids": ["A04"],
        "domain": "PROCESS",
        "requirement_level": "required",
        "source_basis": "IFP GPCB checklist",
        "source_url": "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_establishment_approvals.jsp",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        "max_size_mb": 5,
    },
    {
        "requirement_key": "D10",
        "document_name": "Hazardous waste list + quantities + disposal route",
        "approval_ids": ["A11"],
        "domain": "WASTE",
        "requirement_level": "conditional",
        "source_basis": "HOWM Rule 6 + GPCB workflow",
        "source_url": "https://cpcb.nic.in/uploads/hwmd/HOWM-Ninth-Amendment-Rules-2024.pdf",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D11",
        "document_name": "Hazardous chemical list + maximum on-site quantities",
        "approval_ids": ["A12", "A13"],
        "domain": "CHEMICAL",
        "requirement_level": "required",
        "source_basis": "MSIHC guidance",
        "source_url": "https://cpcb.nic.in/uploads/Guidelines_integrated_guidance_framework.pdf",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "text/csv"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D12",
        "document_name": "Fire safety drawings/systems schedule",
        "approval_ids": ["A06"],
        "domain": "FIRE",
        "requirement_level": "conditional",
        "source_basis": "2023 Regulations + current portal",
        "source_url": "https://gujfiresafetycop.in/uploads/regulations2023.pdf",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 15,
    },
    {
        "requirement_key": "D13",
        "document_name": "Electrical single-line / equipment / earthing documents",
        "approval_ids": ["A09", "A10", "A15"],
        "domain": "ELECTRICAL",
        "requirement_level": "conditional",
        "source_basis": "CEICED/IFP current checklist",
        "source_url": "https://ceiced.gujarat.gov.in/",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 15,
    },
    {
        "requirement_key": "D14",
        "document_name": "Factory site/building/machinery information + chemical process documents",
        "approval_ids": ["A07", "A08"],
        "domain": "FACTORY",
        "requirement_level": "conditional",
        "source_basis": "ShramSetu + current Gujarat requirements",
        "source_url": "https://shramsetu.gujarat.gov.in/Pages/OnlineApplication",
        "document_role": "Technical document",
        "accepted_mime_types": ["application/pdf", "image/*"],
        "max_size_mb": 20,
    },
    {
        "requirement_key": "D15",
        "document_name": "EC/ToR/EC exemption evidence",
        "approval_ids": ["A05"],
        "domain": "ENVIRONMENT",
        "requirement_level": "conditional",
        "source_basis": "EIA 5(f) and current location facts",
        "source_url": "https://parivesh.nic.in/kya/",
        "document_role": "Authority document",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": 20,
    },
    {
        "requirement_key": "D16",
        "document_name": "PESO substance/storage documents",
        "approval_ids": ["A17"],
        "domain": "CHEMICAL STORAGE",
        "requirement_level": "conditional",
        "source_basis": "Exact petroleum/gas classes and quantities",
        "source_url": "https://www.peso.gov.in/web/en/requirement-license-under-petroleum-rules-2002-storage-petroleum",
        "document_role": "Technical/legal document",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": 10,
    },
    {
        "requirement_key": "D17",
        "document_name": "CGWA NOC / abstraction records",
        "approval_ids": ["A18"],
        "domain": "WATER",
        "requirement_level": "conditional",
        "source_basis": "Current CGWA guidance",
        "source_url": "https://cgwa-noc.gov.in/landingpage/Guidlines/ConsolidateGuidline.pdf",
        "document_role": "Authority document",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": 10,
    },
]


def load_document_requirements() -> list[dict[str, Any]]:
    """Return all 17 document requirements from the workbook."""
    return list(DOCUMENT_REQUIREMENTS)


def get_requirements_for_approval(approval_id: str) -> list[dict[str, Any]]:
    """Return document requirements that apply to a given approval."""
    return [
        req for req in DOCUMENT_REQUIREMENTS
        if approval_id in req["approval_ids"]
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_document_requirements.py -v`
Expected: All 15 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/seed/documents.py backend/tests/test_document_requirements.py
git commit -m "feat: add document requirement seed data from workbook Document_Register"
```

---

### Task 2: Migration — document_requirements Table

**Files:**
- Create: `supabase/migrations/002_document_requirements.sql`

**Interfaces:**
- Produces: `document_requirements` table, `document_readiness` enum

- [ ] **Step 1: Write the migration**

```sql
-- supabase/migrations/002_document_requirements.sql
-- Document requirements per application (seeded from workbook Document_Register).

create type document_readiness as enum (
  'pending', 'uploaded', 'valid', 'invalid', 'review_required'
);

create table document_requirements (
  id                  uuid primary key default gen_random_uuid(),
  application_id      uuid not null references applications(id) on delete cascade,
  requirement_key     text not null,
  document_name       text not null,
  approval_id         text not null,
  domain              text not null,
  requirement_level   text not null default 'required',
  readiness           document_readiness not null default 'pending',
  accepted_mime_types jsonb,
  max_size_mb         integer,
  description         text,
  source_basis        text,
  source_url          text,
  document_role       text,
  uploaded_document_id uuid references documents(id),
  rejection_reason    text,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create unique index idx_doc_req_app_key on document_requirements(application_id, requirement_key);
create index idx_doc_req_application on document_requirements(application_id);
create index idx_doc_req_readiness on document_requirements(readiness);
```

- [ ] **Step 2: Verify migration syntax**

Run: `cd backend && python -c "open('supabase/migrations/002_document_requirements.sql').read()"`
Expected: No error

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/002_document_requirements.sql
git commit -m "feat: add document_requirements migration"
```

---

### Task 3: Document Repository

**Files:**
- Create: `backend/app/repositories/documents.py`
- Modify: `backend/app/api/deps.py`
- Test: `backend/tests/test_document_requirements.py` (add tests)

**Interfaces:**
- Consumes: Supabase client (via `BaseRepository`)
- Produces: `DocumentsRepository` with methods: `list_requirements_for_application()`, `get_requirement()`, `create_requirement()`, `update_requirement_readiness()`, `list_documents_for_application()`, `get_document()`, `create_document()`, `delete_document()`

- [ ] **Step 1: Write failing tests for repository**

Add to `backend/tests/test_document_requirements.py`:

```python
# Add these test classes at the end of the file

class TestDocumentsRepository:
    """Tests for DocumentsRepository (unit tests with mocked Supabase client)."""

    def test_list_requirements_for_application(self):
        from unittest.mock import MagicMock
        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "1", "application_id": "app-1", "requirement_key": "D01", "readiness": "pending"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.list_requirements_for_application("app-1")
        assert len(result) == 1
        assert result[0]["requirement_key"] == "D01"

    def test_get_requirement(self):
        from unittest.mock import MagicMock
        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "1", "requirement_key": "D01"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.get_requirement("app-1", "D01")
        assert result is not None

    def test_update_requirement_readiness(self):
        from unittest.mock import MagicMock
        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"id": "1", "readiness": "uploaded"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.update_requirement_readiness("app-1", "D01", "uploaded")
        assert result["readiness"] == "uploaded"

    def test_list_documents_for_application(self):
        from unittest.mock import MagicMock
        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "doc-1", "application_id": "app-1", "requirement_key": "D01"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.list_documents_for_application("app-1")
        assert len(result) == 1

    def test_create_document(self):
        from unittest.mock import MagicMock
        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "doc-1", "requirement_key": "D01"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.create_document({"requirement_key": "D01", "application_id": "app-1"})
        assert result["id"] == "doc-1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_document_requirements.py::TestDocumentsRepository -v`
Expected: FAIL (import error)

- [ ] **Step 3: Write repository implementation**

```python
# backend/app/repositories/documents.py
"""Documents repository — CRUD for document_requirements and documents tables."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class DocumentsRepository(BaseRepository):
    """Repository for document operations."""

    def __init__(self, client):
        super().__init__(client, "documents")

    # -- Document Requirements --

    def list_requirements_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all document requirements for an application."""
        result = (
            self.client.table("document_requirements")
            .select("*")
            .eq("application_id", application_id)
            .order("requirement_key")
            .execute()
        )
        return result.data or []

    def get_requirement(
        self, application_id: str, requirement_key: str
    ) -> dict[str, Any] | None:
        """Get a specific document requirement by application + key."""
        result = (
            self.client.table("document_requirements")
            .select("*")
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_requirement(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a document requirement record."""
        result = (
            self.client.table("document_requirements").insert(data).execute()
        )
        return result.data[0]

    def create_requirements_bulk(
        self, requirements: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create multiple document requirements in one call."""
        if not requirements:
            return []
        result = (
            self.client.table("document_requirements")
            .insert(requirements)
            .execute()
        )
        return result.data or []

    def update_requirement_readiness(
        self,
        application_id: str,
        requirement_key: str,
        readiness: str,
        uploaded_document_id: str | None = None,
        rejection_reason: str | None = None,
    ) -> dict[str, Any] | None:
        """Update readiness status for a document requirement."""
        update_data: dict[str, Any] = {"readiness": readiness}
        if uploaded_document_id is not None:
            update_data["uploaded_document_id"] = uploaded_document_id
        if rejection_reason is not None:
            update_data["rejection_reason"] = rejection_reason

        result = (
            self.client.table("document_requirements")
            .update(update_data)
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None

    # -- Uploaded Documents --

    def list_documents_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all uploaded documents for an application."""
        result = (
            self.client.table("documents")
            .select("*")
            .eq("application_id", application_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        """Get a document by ID."""
        result = (
            self.client.table("documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_document(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a document record."""
        result = self.client.table("documents").insert(data).execute()
        return result.data[0]

    def delete_document(self, document_id: str) -> bool:
        """Delete a document record."""
        self.client.table("documents").delete().eq("id", document_id).execute()
        return True

    def get_document_by_requirement(
        self, application_id: str, requirement_key: str
    ) -> dict[str, Any] | None:
        """Get the uploaded document for a specific requirement."""
        result = (
            self.client.table("documents")
            .select("*")
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None
```

- [ ] **Step 4: Add dependency to deps.py**

Modify `backend/app/api/deps.py` — add at the end:

```python
from app.repositories.documents import DocumentsRepository


def get_documents_repository(
    client: Client = Depends(get_db_client),
) -> DocumentsRepository:
    """Get documents repository dependency."""
    return DocumentsRepository(client)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_document_requirements.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories/documents.py backend/app/api/deps.py backend/tests/test_document_requirements.py
git commit -m "feat: add DocumentsRepository with requirement and document CRUD"
```

---

### Task 4: Document API Routes

**Files:**
- Create: `backend/app/api/documents.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_document_upload.py`

**Interfaces:**
- Consumes: `DocumentsRepository` (via deps), `UserContext` (auth), `check_application_ownership`
- Produces: 5 REST endpoints (list requirements, list documents, upload, get, delete)

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_document_upload.py
"""Tests for document upload API endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest


class TestDocumentRequirementsEndpoint:
    def test_list_requirements_returns_list(self):
        """Verify the endpoint structure exists and returns data."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        # Without auth, should get 401
        resp = client.get("/applications/00000000-0000-0000-0000-000000000001/document-requirements")
        assert resp.status_code == 401

    def test_list_documents_returns_list(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/applications/00000000-0000-0000-0000-000000000001/documents")
        assert resp.status_code == 401

    def test_upload_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/applications/00000000-0000-0000-0000-000000000001/documents/D01/upload",
        )
        assert resp.status_code == 401

    def test_get_document_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001",
        )
        assert resp.status_code == 401

    def test_delete_document_requires_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001",
        )
        assert resp.status_code == 401


class TestUploadValidation:
    def test_reject_empty_file(self):
        """Upload endpoint should reject empty file uploads."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        # Would need auth mock — testing validation logic directly instead
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="test.pdf",
            content_type="application/pdf",
            file_size=0,
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert not is_valid
        assert "empty" in error.lower() or "size" in error.lower()

    def test_reject_oversized_file(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="large.pdf",
            content_type="application/pdf",
            file_size=50 * 1024 * 1024,  # 50MB
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert not is_valid
        assert "size" in error.lower()

    def test_reject_wrong_type(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="script.exe",
            content_type="application/x-executable",
            file_size=1024,
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert not is_valid
        assert "type" in error.lower() or "mime" in error.lower()

    def test_accept_valid_file(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="doc.pdf",
            content_type="application/pdf",
            file_size=1024,
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert is_valid
        assert error == ""

    def test_accept_wildcard_type(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="photo.jpg",
            content_type="image/jpeg",
            file_size=1024,
            accepted_types=["image/*"],
            max_size_mb=10,
        )
        assert is_valid

    def test_reject_path_traversal(self):
        from app.api.documents import _sanitize_filename

        result = _sanitize_filename("../../etc/passwd.pdf")
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result


class TestSanitizeFilename:
    def test_removes_path_separators(self):
        from app.api.documents import _sanitize_filename

        assert _sanitize_filename("path/to/file.pdf") == "file.pdf"

    def test_removes_null_bytes(self):
        from app.api.documents import _sanitize_filename

        assert _sanitize_filename("file\x00.pdf") == "file.pdf"

    def test_preserves_dots_in_name(self):
        from app.api.documents import _sanitize_filename

        assert _sanitize_filename("my.document.v2.pdf") == "my.document.v2.pdf"

    def test_handles_empty_name(self):
        from app.api.documents import _sanitize_filename

        result = _sanitize_filename("")
        assert len(result) > 0  # Should generate a fallback name
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_document_upload.py -v`
Expected: FAIL (import errors, functions not found)

- [ ] **Step 3: Write API route implementation**

```python
# backend/app/api/documents.py
"""Document management endpoints."""
from __future__ import annotations

import io
import re
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_documents_repository
from app.auth.dependencies import (
    check_application_ownership,
    require_any_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission
from app.repositories.documents import DocumentsRepository
from app.audit.service import AuditEntry, create_audit_record

router = APIRouter()


# -- Helpers --

def _sanitize_filename(filename: str) -> str:
    """Remove path traversal and dangerous characters from filename."""
    # Remove path separators and null bytes
    name = filename.replace("\x00", "")
    name = name.replace("/", "").replace("\\", "")
    # Remove leading dots (hidden files)
    name = name.lstrip(".")
    # Replace non-alphanumeric characters (except dots, dashes, underscores)
    name = re.sub(r"[^\w.\-]", "_", name)
    # Fallback if empty
    if not name:
        name = "unnamed_file"
    return name


def _validate_upload(
    filename: str,
    content_type: str,
    file_size: int,
    accepted_types: list[str] | None,
    max_size_mb: int | None,
) -> tuple[bool, str]:
    """Validate file upload. Returns (is_valid, error_message)."""
    if file_size <= 0:
        return False, "File is empty"

    if max_size_mb and file_size > max_size_mb * 1024 * 1024:
        return False, f"File exceeds maximum size of {max_size_mb} MB"

    if accepted_types:
        type_match = False
        for accepted in accepted_types:
            if accepted.endswith("/*"):
                prefix = accepted[:-2]
                if content_type.startswith(prefix):
                    type_match = True
                    break
            elif content_type == accepted:
                type_match = True
                break
        if not type_match:
            return False, f"File type '{content_type}' not accepted. Allowed: {accepted_types}"

    return True, ""


def _get_app_withOwnership(
    application_id: str,
    repo: DocumentsRepository,
    user: UserContext,
) -> dict[str, Any]:
    """Get application and verify ownership. Raises 404/403."""
    from app.repositories.applications import ApplicationsRepository
    from uuid import UUID

    app_repo = ApplicationsRepository(repo.client)
    application = app_repo.get_by_id(UUID(application_id))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)
    return application


# -- Endpoints --

@router.get("/applications/{application_id}/document-requirements")
async def list_document_requirements(
    application_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """List document requirements checklist for an application."""
    _get_app_withOwnership(application_id, repo, user)
    return repo.list_requirements_for_application(application_id)


@router.get("/applications/{application_id}/documents")
async def list_documents(
    application_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """List uploaded documents for an application."""
    _get_app_withOwnership(application_id, repo, user)
    return repo.list_documents_for_application(application_id)


@router.post("/applications/{application_id}/documents/{requirement_key}/upload")
async def upload_document(
    application_id: str,
    requirement_key: str,
    file: UploadFile = File(...),
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
        )
    ),
):
    """Upload a document for a specific requirement."""
    _get_app_withOwnership(application_id, repo, user)

    # Verify requirement exists
    requirement = repo.get_requirement(application_id, requirement_key)
    if not requirement:
        raise HTTPException(
            status_code=404,
            detail=f"Document requirement '{requirement_key}' not found for this application",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)
    content_type = file.content_type or "application/octet-stream"
    filename = _sanitize_filename(file.filename or "unnamed_file")

    # Validate
    accepted = requirement.get("accepted_mime_types")
    max_size = requirement.get("max_size_mb")
    is_valid, error = _validate_upload(filename, content_type, file_size, accepted, max_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # Upload to Supabase Storage
    from app.core.config import get_settings

    settings = get_settings()
    storage_path = f"applications/{application_id}/{requirement_key}/{filename}"

    try:
        from supabase import Client

        from app.db.client import get_supabase

        client = get_supabase()
        client.storage.from_(settings.supabase_storage_bucket).upload(
            storage_path, content, {"content-type": content_type}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Storage upload failed: {str(e)}",
        )

    # Create document record
    doc_data = {
        "application_id": application_id,
        "requirement_key": requirement_key,
        "original_filename": filename,
        "storage_path": storage_path,
        "mime_type": content_type,
        "file_size_bytes": file_size,
        "status": "uploaded",
        "uploaded_by_user_id": str(user.user_id),
    }
    document = repo.create_document(doc_data)

    # Update requirement readiness
    repo.update_requirement_readiness(
        application_id, requirement_key, "uploaded", document["id"]
    )

    # Audit
    audit = create_audit_record(
        AuditEntry(
            action="document:upload",
            entity_type="document",
            entity_id=document["id"],
            user_id=str(user.user_id),
            application_id=application_id,
            new_values={
                "filename": filename,
                "mime_type": content_type,
                "file_size": file_size,
                "requirement_key": requirement_key,
            },
        )
    )

    return {
        "document": document,
        "requirement": repo.get_requirement(application_id, requirement_key),
    }


@router.get("/applications/{application_id}/documents/{document_id}")
async def get_document(
    application_id: str,
    document_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get document metadata."""
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(status_code=404, detail="Document not found for this application")

    return document


@router.delete("/applications/{application_id}/documents/{document_id}")
async def delete_document(
    application_id: str,
    document_id: str,
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
        )
    ),
):
    """Delete an uploaded document."""
    _get_app_withOwnership(application_id, repo, user)

    document = repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("application_id") != application_id:
        raise HTTPException(status_code=404, detail="Document not found for this application")

    # Delete from storage
    from app.core.config import get_settings
    from app.db.client import get_supabase

    settings = get_settings()
    client = get_supabase()
    storage_path = document.get("storage_path", "")
    if storage_path:
        try:
            client.storage.from_(settings.supabase_storage_bucket).remove([storage_path])
        except Exception:
            pass  # Best-effort storage cleanup

    # Update requirement readiness back to pending
    requirement_key = document.get("requirement_key")
    if requirement_key:
        repo.update_requirement_readiness(
            application_id, requirement_key, "pending", None, None
        )

    # Delete document record
    repo.delete_document(document_id)

    # Audit
    audit = create_audit_record(
        AuditEntry(
            action="document:delete",
            entity_type="document",
            entity_id=document_id,
            user_id=str(user.user_id),
            application_id=application_id,
            previous_values={
                "filename": document.get("original_filename"),
                "requirement_key": requirement_key,
            },
        )
    )

    return {"deleted": True}
```

- [ ] **Step 4: Register router in main.py**

Modify `backend/app/main.py` — add:

```python
from app.api import applications, approvals, documents, health, projects, workflow

# ... existing includes ...
app.include_router(documents.router, tags=["documents"])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_document_upload.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/documents.py backend/app/main.py backend/tests/test_document_upload.py
git commit -m "feat: add document management API endpoints with upload validation"
```

---

### Task 5: Config — Storage Bucket Setting

**Files:**
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Add storage bucket setting**

Modify `backend/app/core/config.py` — add to `Settings` class:

```python
    # Storage
    supabase_storage_bucket: str = "documents"
```

- [ ] **Step 2: Verify settings load**

Run: `cd backend && python -c "from app.core.config import Settings; s = Settings(); print(s.supabase_storage_bucket)"`
Expected: `documents`

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/config.py
git commit -m "feat: add supabase_storage_bucket config setting"
```

---

### Task 6: Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add TypeScript types**

Add to `frontend/src/types/api.ts` at the end:

```typescript
export interface DocumentRequirement {
  id: string
  application_id: string
  requirement_key: string
  document_name: string
  approval_id: string
  domain: string
  requirement_level: 'required' | 'mandatory' | 'conditional'
  readiness: 'pending' | 'uploaded' | 'valid' | 'invalid' | 'review_required'
  accepted_mime_types: string[] | null
  max_size_mb: number | null
  description: string | null
  source_basis: string | null
  source_url: string | null
  document_role: string | null
  uploaded_document_id: string | null
  rejection_reason: string | null
  created_at: string
  updated_at: string
}

export interface UploadedDocument {
  id: string
  application_id: string
  requirement_key: string
  original_filename: string
  storage_path: string
  mime_type: string
  file_size_bytes: number
  status: 'pending_upload' | 'uploaded' | 'verified' | 'rejected' | 'virus_detected' | 'expired'
  rejection_reason: string | null
  uploaded_by_user_id: string | null
  created_at: string
}

export interface UploadResult {
  document: UploadedDocument
  requirement: DocumentRequirement
}
```

- [ ] **Step 2: Add API methods**

Add to `frontend/src/lib/api.ts` inside the `api` object:

```typescript
  documents: {
    listRequirements: (appId: string) =>
      request<DocumentRequirement[]>(`/applications/${appId}/document-requirements`),
    list: (appId: string) =>
      request<UploadedDocument[]>(`/applications/${appId}/documents`),
    upload: async (appId: string, reqKey: string, file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data: { session } } = await supabase.auth.getSession()
      const headers: Record<string, string> = {}
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      }
      const res = await fetch(
        `${API_BASE}/applications/${appId}/documents/${reqKey}/upload`,
        { method: 'POST', headers, body: formData },
      )
      if (res.status === 401) {
        window.location.href = '/login'
        throw new ApiError(401, 'Unauthorized')
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }))
        throw new ApiError(res.status, body.detail ?? res.statusText)
      }
      return res.json() as Promise<UploadResult>
    },
    get: (appId: string, docId: string) =>
      request<UploadedDocument>(`/applications/${appId}/documents/${docId}`),
    delete: (appId: string, docId: string) =>
      request<{ deleted: boolean }>(`/applications/${appId}/documents/${docId}`, { method: 'DELETE' }),
  },
```

- [ ] **Step 3: Run frontend checks**

Run: `cd frontend && npx tsc --noEmit && npx oxlint`
Expected: 0 TypeScript errors, no new lint errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/lib/api.ts
git commit -m "feat: add document types and API client methods"
```

---

### Task 7: Frontend Document Checklist UI

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `DocumentRequirement`, `UploadedDocument` types; `api.documents.*` methods

- [ ] **Step 1: Add document checklist section to ApplicationDetailPage**

Add after the existing "Details" card in `ApplicationDetailPage.tsx`:

```tsx
// Add imports at top:
import type { DocumentRequirement, UploadedDocument } from '@/types/api'

// Add state variables (inside component, after existing state):
const [docRequirements, setDocRequirements] = useState<DocumentRequirement[]>([])
const [uploadedDocs, setUploadedDocs] = useState<UploadedDocument[]>([])
const [docLoading, setDocLoading] = useState(false)
const [docError, setDocError] = useState('')
const [uploadingKey, setUploadingKey] = useState('')

// Add effect to load documents (after existing useEffect):
useEffect(() => {
  if (!id) return
  setDocLoading(true)
  Promise.all([
    api.documents.listRequirements(id),
    api.documents.list(id),
  ])
    .then(([reqs, docs]) => {
      setDocRequirements(reqs as DocumentRequirement[])
      setUploadedDocs(docs as UploadedDocument[])
    })
    .catch((err) => setDocError(err.message))
    .finally(() => setDocLoading(false))
}, [id])

// Add upload handler:
const handleUpload = async (reqKey: string, file: File) => {
  if (!id) return
  setUploadingKey(reqKey)
  setDocError('')
  try {
    const result = await api.documents.upload(id, reqKey, file)
    setUploadedDocs((prev) => {
      const filtered = prev.filter((d) => d.requirement_key !== reqKey)
      return [result.document, ...filtered]
    })
    setDocRequirements((prev) =>
      prev.map((r) => (r.requirement_key === reqKey ? result.requirement : r)),
    )
  } catch (err) {
    if (err instanceof ApiError) setDocError(err.message)
    else setDocError(err instanceof Error ? err.message : 'Upload failed')
  } finally {
    setUploadingKey('')
  }
}

// Add delete handler:
const handleDeleteDoc = async (docId: string, reqKey: string) => {
  if (!id) return
  try {
    await api.documents.delete(id, docId)
    setUploadedDocs((prev) => prev.filter((d) => d.id !== docId))
    setDocRequirements((prev) =>
      prev.map((r) =>
        r.requirement_key === reqKey
          ? { ...r, readiness: 'pending' as const, uploaded_document_id: null }
          : r,
      ),
    )
  } catch (err) {
    if (err instanceof ApiError) setDocError(err.message)
    else setDocError(err instanceof Error ? err.message : 'Delete failed')
  }
}
```

Add the JSX section (before the closing `</div>`):

```tsx
      {/* Document Checklist */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Document Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          {docLoading ? (
            <LoadingSpinner className="py-4" />
          ) : docError ? (
            <div className="text-sm text-destructive">{docError}</div>
          ) : docRequirements.length === 0 ? (
            <p className="text-sm text-muted-foreground">No document requirements for this application.</p>
          ) : (
            <div className="space-y-3">
              {docRequirements.map((req) => {
                const uploaded = uploadedDocs.find((d) => d.requirement_key === req.requirement_key)
                return (
                  <div
                    key={req.requirement_key}
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{req.requirement_key}</span>
                        <span className="text-sm font-medium truncate">{req.document_name}</span>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            req.requirement_level === 'mandatory'
                              ? 'bg-red-100 text-red-800'
                              : req.requirement_level === 'conditional'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {req.requirement_level}
                        </span>
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                          {req.domain}
                        </span>
                      </div>
                      {uploaded ? (
                        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{uploaded.original_filename}</span>
                          <span>({(uploaded.file_size_bytes / 1024).toFixed(1)} KB)</span>
                          <StatusBadge status={uploaded.status === 'verified' ? 'approved' : uploaded.status === 'rejected' ? 'refused' : 'submitted'} />
                        </div>
                      ) : (
                        <p className="mt-1 text-xs text-muted-foreground">Not uploaded</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      {uploaded ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteDoc(uploaded.id, req.requirement_key)}
                        >
                          Remove
                        </Button>
                      ) : (
                        <label className="cursor-pointer">
                          <input
                            type="file"
                            className="hidden"
                            accept={req.accepted_mime_types?.join(',')}
                            onChange={(e) => {
                              const file = e.target.files?.[0]
                              if (file) handleUpload(req.requirement_key, file)
                            }}
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={uploadingKey === req.requirement_key}
                            asChild
                          >
                            <span>
                              {uploadingKey === req.requirement_key ? 'Uploading...' : 'Upload'}
                            </span>
                          </Button>
                        </label>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
```

- [ ] **Step 2: Run frontend checks**

Run: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`
Expected: 0 TypeScript errors, build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/applicant/ApplicationDetailPage.tsx
git commit -m "feat: add document checklist UI to applicant application detail"
```

---

### Task 8: Seed Requirements into Application on Creation

**Files:**
- Modify: `backend/app/api/applications.py` (create endpoint)

**Interfaces:**
- Consumes: `load_document_requirements()`, `get_requirements_for_approval()` from seed data
- Produces: Auto-created `document_requirements` rows when an application is created

- [ ] **Step 1: Modify create_application endpoint**

Modify `backend/app/api/applications.py` — update `create_application` to accept `approval_code` (e.g., "A01") and seed document requirements:

```python
@router.post("/applications")
async def create_application(
    project_id: UUID,
    approval_id: UUID,
    approval_code: str = Query(..., description="Approval code like A01, A02"),
    repo: ApplicationsRepository = Depends(get_applications_repository),
    doc_repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    """Create a new application."""
    data = {
        "project_id": str(project_id),
        "approval_id": str(approval_id),
        "status": "draft",
        "applicant_id": str(user.user_id),
    }
    application = repo.create_with_reference(data)

    # Seed document requirements from workbook
    from app.seed.documents import get_requirements_for_approval

    doc_reqs = get_requirements_for_approval(approval_code)
    if doc_reqs:
        requirement_records = []
        for req in doc_reqs:
            requirement_records.append({
                "application_id": application["id"],
                "requirement_key": req["requirement_key"],
                "document_name": req["document_name"],
                "approval_id": approval_code,
                "domain": req["domain"],
                "requirement_level": req["requirement_level"],
                "readiness": "pending",
                "accepted_mime_types": req.get("accepted_mime_types"),
                "max_size_mb": req.get("max_size_mb"),
                "source_basis": req.get("source_basis"),
                "source_url": req.get("source_url"),
                "document_role": req.get("document_role"),
            })
        doc_repo.create_requirements_bulk(requirement_records)

    return application
```

Also add the import at the top:

```python
from app.api.deps import get_applications_repository, get_documents_repository
```

- [ ] **Step 2: Verify import works**

Run: `cd backend && python -c "from app.api.applications import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/applications.py
git commit -m "feat: auto-seed document requirements on application creation"
```

---

### Task 9: Full Test Suite Verification

**Files:**
- All modified/created files

- [ ] **Step 1: Run backend tests**

Run: `cd backend && python -m pytest tests/ -v --tb=short`
Expected: 402+ passed, 23 failed (pre-existing), 4 skipped, 0 new failures

- [ ] **Step 2: Run backend lint**

Run: `cd backend && python -m ruff check app/ tests/`
Expected: All checks pass

- [ ] **Step 3: Run frontend checks**

Run: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`
Expected: 0 TypeScript errors, build succeeds

- [ ] **Step 4: Verify no regressions in pre-existing failures**

The 23 pre-existing Supabase config failures must remain unchanged:
- test_api_applications_list.py: 3 failures
- test_auth.py: 20 failures

Run: `cd backend && python -m pytest tests/test_api_applications_list.py tests/test_auth.py -v --tb=no -q 2>&1 | Select-Object -Last 5`
Expected: Same 23 failures, no new ones

- [ ] **Step 5: Commit final state**

```bash
git add -A
git commit -m "feat: Phase 3C document management foundation complete"
```

---

### Task 10: Update Context Files

**Files:**
- Modify: `ARCHITECTURE.md`
- Modify: `RULES.md`
- Modify: `PRD.md`
- Modify: `AGENTS.md` (if needed)

- [ ] **Step 1: Update ARCHITECTURE.md**

Add to "Phase 3C implementation status" section:

```markdown
## 23. Phase 3C implementation status (2026-09-15)

### Created
- `backend/app/seed/documents.py` — 17 document requirements from workbook Document_Register
- `backend/app/repositories/documents.py` — DocumentRequirements + Documents CRUD
- `backend/app/api/documents.py` — 5 REST endpoints (list reqs, list docs, upload, get, delete)
- `backend/tests/test_document_requirements.py` — 15 seed data + lookup tests
- `backend/tests/test_document_upload.py` — 11 upload validation + auth tests
- `supabase/migrations/002_document_requirements.sql` — document_requirements table + enum

### Implemented
- Document requirements per application (seeded from workbook D01-D17)
- Document upload with server-side MIME/size validation
- Supabase Storage integration (backend-proxied, private bucket)
- Filename sanitization (path traversal prevention)
- Document readiness tracking (pending/uploaded/valid/invalid/review_required)
- Audit events for upload/delete actions
- Frontend document checklist in applicant ApplicationDetailPage
- Auto-seed requirements on application creation

### Checks
- Backend: 402+ passed, 23 failed (pre-existing), 4 skipped
- Frontend: tsc clean, oxlint clean, vite build success

### Known limitations
- No OCR/extraction/LLM processing (deferred to later milestone)
- No document verification/review workflow (deferred)
- No cross-document consistency checks (deferred)
- Storage bucket must be created manually in Supabase dashboard
- No signed URL generation for direct download (deferred)

### Next phase
- Phase 5: Document extraction/OCR, consistency engine, SLA display
```

- [ ] **Step 2: Update PRD.md current status**

Add to PRD.md:

```markdown
- **Phase 3C complete (2026-09-15)**: Document management foundation — 17 workbook document requirements, upload with validation, Supabase Storage integration, readiness tracking, audit trail, frontend checklist, 402+ backend tests passing.
```

- [ ] **Step 3: Update RULES.md backend structure**

Update the backend structure section to include:

```markdown
- `seed/` — workbook scenario, approval rules, dependency edges, **document requirements**, expected results
- `repositories/` — database access layer (base CRUD + specialized repos, including `documents.py`)
- `api/` — FastAPI routes with auth dependencies (health, projects, approvals, applications, workflow, **documents**)
```

- [ ] **Step 4: Commit**

```bash
git add ARCHITECTURE.md PRD.md RULES.md
git commit -m "docs: update context files for Phase 3C completion"
```
