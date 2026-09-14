# Phase 2A: Database + API Foundation Implementation Plan

> **Status: COMPLETE** (2026-09-14)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the database access layer and minimal FastAPI API boundary for the Gujarat Industrial Approval Intelligence MVP.

**Architecture:** Create a thin Supabase client wrapper, repository layer for database operations, and FastAPI routes that delegate to domain services. No ORM, no complex abstractions.

**Tech Stack:** FastAPI, Pydantic v2, supabase-py, python-dateutil, pytest

## Global Constraints
- Python >=3.11
- FastAPI >=0.115, <1
- Pydantic >=2.9, <3
- supabase-py (latest stable)
- No secrets in source control
- Domain logic stays in existing pure modules
- Tests use mocks/test doubles, not real Supabase connections

---

## File Structure

```
backend/
├── pyproject.toml                    # Add supabase, uvicorn dependencies
├── app/
│   ├── core/
│   │   └── config.py                 # Settings class with env vars
│   ├── db/
│   │   ├── __init__.py
│   │   └── client.py                 # Supabase client factory
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── projects.py               # Project CRUD
│   │   ├── project_facts.py          # Project facts CRUD
│   │   ├── approvals.py              # Approvals read
│   │   ├── obligations.py            # Obligations read
│   │   ├── sources.py                # Sources read
│   │   └── applications.py           # Applications CRUD
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                   # Dependency injection
│   │   ├── health.py                 # Health check endpoint
│   │   ├── projects.py               # Project endpoints
│   │   ├── facts.py                  # Project facts endpoints
│   │   ├── approvals.py              # Approvals/obligations endpoints
│   │   └── applications.py           # Applications endpoints
│   └── main.py                       # FastAPI app creation
└── tests/
    ├── test_api_health.py
    ├── test_api_projects.py
    ├── test_repositories.py
    └── test_integration.py
```

---

## Task 1: Update Dependencies

**Files:**
- Modify: `backend/pyproject.toml`

**Interfaces:**
- Consumes: None
- Produces: None (dependency update only)

- [ ] **Step 1: Add supabase and uvicorn to dependencies**

```toml
[project]
dependencies = [
  "fastapi>=0.115,<1",
  "pydantic>=2.9,<3",
  "python-dateutil>=2.9,<3",
  "supabase>=2.0,<3",
  "uvicorn[standard]>=0.30,<1",
]
```

- [ ] **Step 2: Install updated dependencies**

Run: `cd D:\SIH\backend && pip install -e .`

- [ ] **Step 3: Verify installation**

Run: `cd D:\SIH\backend && python -c "import supabase; import uvicorn; print('OK')"`

---

## Task 2: Implement Configuration

**Files:**
- Modify: `backend/app/core/config.py`

**Interfaces:**
- Consumes: Environment variables (SUPABASE_URL, SUPABASE_KEY, etc.)
- Produces: `Settings` class with Pydantic BaseSettings

- [ ] **Step 1: Write the Settings class**

```python
"""Application settings — loaded from environment at startup."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str | None = None

    # App
    app_name: str = "SIH 26130 Gujarat MVP"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
```

- [ ] **Step 2: Add pydantic-settings to dependencies**

Update `pyproject.toml`:
```toml
dependencies = [
  "fastapi>=0.115,<1",
  "pydantic>=2.9,<3",
  "pydantic-settings>=2.0,<3",
  "python-dateutil>=2.9,<3",
  "supabase>=2.0,<3",
  "uvicorn[standard]>=0.30,<1",
]
```

- [ ] **Step 3: Install and verify**

Run: `cd D:\SIH\backend && pip install -e . && python -c "from app.core.config import Settings; print('OK')"`

---

## Task 3: Implement Supabase Client

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/client.py`

**Interfaces:**
- Consumes: `Settings` from `app.core.config`
- Produces: `get_supabase()` function returning Supabase Client

- [ ] **Step 1: Create db/__init__.py**

```python
"""Database access layer."""
```

- [ ] **Step 2: Create db/client.py**

```python
"""Supabase client factory."""

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """Get cached Supabase client."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)
```

- [ ] **Step 3: Verify import**

Run: `cd D:\SIH\backend && python -c "from app.db.client import get_supabase; print('OK')"`

---

## Task 4: Create Repository Base

**Files:**
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/base.py`

**Interfaces:**
- Consumes: Supabase Client
- Produces: Base repository class with common methods

- [ ] **Step 1: Create repositories/__init__.py**

```python
"""Repository layer for database operations."""
```

- [ ] **Step 2: Create repositories/base.py**

```python
"""Base repository with common database operations."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from supabase import Client

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, client: Client, table_name: str):
        self.client = client
        self.table_name = table_name

    def get_by_id(self, id: UUID) -> dict[str, Any] | None:
        """Get a record by ID."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("id", str(id))
            .execute()
        )
        return result.data[0] if result.data else None

    def get_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Get all records with pagination."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record."""
        result = (
            self.client.table(self.table_name)
            .insert(data)
            .execute()
        )
        return result.data[0]

    def update(self, id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        """Update a record by ID."""
        result = (
            self.client.table(self.table_name)
            .update(data)
            .eq("id", str(id))
            .execute()
        )
        return result.data[0] if result.data else None

    def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        result = (
            self.client.table(self.table_name)
            .delete()
            .eq("id", str(id))
            .execute()
        )
        return True
```

---

## Task 5: Create Project Repository

**Files:**
- Create: `backend/app/repositories/projects.py`

**Interfaces:**
- Consumes: BaseRepository
- Produces: ProjectRepository with project-specific queries

- [ ] **Step 1: Create repositories/projects.py**

```python
"""Project repository for database operations."""

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository):
    """Repository for project operations."""

    def __init__(self, client):
        super().__init__(client, "projects")

    def get_by_applicant(self, applicant_id: UUID) -> list[dict[str, Any]]:
        """Get all projects for an applicant."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("applicant_id", str(applicant_id))
            .execute()
        )
        return result.data

    def get_with_facts(self, project_id: UUID) -> dict[str, Any] | None:
        """Get project with its facts."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        facts_result = (
            self.client.table("project_facts")
            .select("*")
            .eq("project_id", str(project_id))
            .execute()
        )
        project["facts"] = facts_result.data[0] if facts_result.data else None
        return project
```

---

## Task 6: Create Other Repositories

**Files:**
- Create: `backend/app/repositories/project_facts.py`
- Create: `backend/app/repositories/approvals.py`
- Create: `backend/app/repositories/obligations.py`
- Create: `backend/app/repositories/sources.py`
- Create: `backend/app/repositories/applications.py`

**Interfaces:**
- Consumes: BaseRepository
- Produces: Specialized repositories for each entity

- [ ] **Step 1: Create project_facts.py**

```python
"""Project facts repository."""

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class ProjectFactsRepository(BaseRepository):
    """Repository for project facts operations."""

    def __init__(self, client):
        super().__init__(client, "project_facts")

    def get_by_project(self, project_id: UUID) -> dict[str, Any] | None:
        """Get facts for a project."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("project_id", str(project_id))
            .execute()
        )
        return result.data[0] if result.data else None

    def upsert(self, project_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update facts for a project."""
        data["project_id"] = str(project_id)
        result = (
            self.client.table(self.table_name)
            .upsert(data)
            .execute()
        )
        return result.data[0]
```

- [ ] **Step 2: Create approvals.py**

```python
"""Approvals repository."""

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class ApprovalsRepository(BaseRepository):
    """Repository for approvals operations."""

    def __init__(self, client):
        super().__init__(client, "approvals")

    def get_active(self) -> list[dict[str, Any]]:
        """Get all active approvals."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("active", True)
            .execute()
        )
        return result.data

    def get_with_rules(self, approval_id: UUID) -> dict[str, Any] | None:
        """Get approval with its rules."""
        approval = self.get_by_id(approval_id)
        if not approval:
            return None

        rules_result = (
            self.client.table("approval_rules")
            .select("*")
            .eq("approval_id", str(approval_id))
            .execute()
        )
        approval["rules"] = rules_result.data
        return approval
```

- [ ] **Step 3: Create obligations.py**

```python
"""Obligations repository."""

from typing import Any

from app.repositories.base import BaseRepository


class ObligationsRepository(BaseRepository):
    """Repository for obligations operations."""

    def __init__(self, client):
        super().__init__(client, "obligations")

    def get_all_active(self) -> list[dict[str, Any]]:
        """Get all obligations."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .execute()
        )
        return result.data

    def get_by_canonical_id(self, canonical_id: str) -> dict[str, Any] | None:
        """Get obligation by canonical ID."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("canonical_id", canonical_id)
            .execute()
        )
        return result.data[0] if result.data else None
```

- [ ] **Step 4: Create sources.py**

```python
"""Sources repository."""

from typing import Any

from app.repositories.base import BaseRepository


class SourcesRepository(BaseRepository):
    """Repository for sources operations."""

    def __init__(self, client):
        super().__init__(client, "sources")

    def get_by_jurisdiction(self, jurisdiction: str) -> list[dict[str, Any]]:
        """Get sources by jurisdiction."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("jurisdiction", jurisdiction)
            .execute()
        )
        return result.data
```

- [ ] **Step 5: Create applications.py**

```python
"""Applications repository."""

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class ApplicationsRepository(BaseRepository):
    """Repository for applications operations."""

    def __init__(self, client):
        super().__init__(client, "applications")

    def get_by_project(self, project_id: UUID) -> list[dict[str, Any]]:
        """Get all applications for a project."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("project_id", str(project_id))
            .execute()
        )
        return result.data

    def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get applications by status."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", status)
            .execute()
        )
        return result.data

    def create_with_reference(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create application with auto-generated reference number."""
        import uuid
        data["reference_number"] = f"APP-{uuid.uuid4().hex[:8].upper()}"
        return self.create(data)
```

---

## Task 7: Create API Dependencies

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`

**Interfaces:**
- Consumes: Supabase client, repositories
- Produces: FastAPI dependency functions

- [ ] **Step 1: Create api/__init__.py**

```python
"""API layer for FastAPI routes."""
```

- [ ] **Step 2: Create api/deps.py**

```python
"""FastAPI dependencies for dependency injection."""

from functools import lru_cache

from supabase import Client

from app.db.client import get_supabase
from app.repositories.applications import ApplicationsRepository
from app.repositories.approvals import ApprovalsRepository
from app.repositories.obligations import ObligationsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.sources import SourcesRepository


@lru_cache
def get_db_client() -> Client:
    """Get Supabase client dependency."""
    return get_supabase()


def get_project_repository(client: Client = None) -> ProjectRepository:
    """Get project repository dependency."""
    if client is None:
        client = get_db_client()
    return ProjectRepository(client)


def get_project_facts_repository(client: Client = None) -> ProjectFactsRepository:
    """Get project facts repository dependency."""
    if client is None:
        client = get_db_client()
    return ProjectFactsRepository(client)


def get_approvals_repository(client: Client = None) -> ApprovalsRepository:
    """Get approvals repository dependency."""
    if client is None:
        client = get_db_client()
    return ApprovalsRepository(client)


def get_obligations_repository(client: Client = None) -> ObligationsRepository:
    """Get obligations repository dependency."""
    if client is None:
        client = get_db_client()
    return ObligationsRepository(client)


def get_sources_repository(client: Client = None) -> SourcesRepository:
    """Get sources repository dependency."""
    if client is None:
        client = get_db_client()
    return SourcesRepository(client)


def get_applications_repository(client: Client = None) -> ApplicationsRepository:
    """Get applications repository dependency."""
    if client is None:
        client = get_db_client()
    return ApplicationsRepository(client)
```

---

## Task 8: Create Health Check Endpoint

**Files:**
- Create: `backend/app/api/health.py`

**Interfaces:**
- Consumes: None
- Produces: Health check response

- [ ] **Step 1: Create api/health.py**

```python
"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

---

## Task 9: Create Project Endpoints

**Files:**
- Create: `backend/app/api/projects.py`

**Interfaces:**
- Consumes: ProjectRepository, ProjectFactsRepository
- Produces: Project CRUD endpoints

- [ ] **Step 1: Create api/projects.py**

```python
"""Project endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_project_repository, get_project_facts_repository
from app.repositories.projects import ProjectRepository
from app.repositories.project_facts import ProjectFactsRepository

router = APIRouter()


@router.post("/projects")
async def create_project(
    name: str,
    description: str | None = None,
    applicant_id: UUID = None,
    repo: ProjectRepository = Depends(get_project_repository),
):
    """Create a new project."""
    data = {"name": name, "description": description}
    if applicant_id:
        data["applicant_id"] = str(applicant_id)
    return repo.create(data)


@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    repo: ProjectRepository = Depends(get_project_repository),
):
    """Get a project by ID."""
    project = repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/facts")
async def get_project_facts(
    project_id: UUID,
    repo: ProjectFactsRepository = Depends(get_project_facts_repository),
):
    """Get facts for a project."""
    facts = repo.get_by_project(project_id)
    if not facts:
        raise HTTPException(status_code=404, detail="Project facts not found")
    return facts


@router.post("/projects/{project_id}/facts")
async def upsert_project_facts(
    project_id: UUID,
    entity_type: str,
    sector: str,
    jurisdictions: list[str] = [],
    headcount: int = 0,
    annual_turnover_inr: float = 0,
    repo: ProjectFactsRepository = Depends(get_project_facts_repository),
):
    """Create or update project facts."""
    data = {
        "entity_type": entity_type,
        "sector": sector,
        "jurisdictions": jurisdictions,
        "headcount": headcount,
        "annual_turnover_inr": annual_turnover_inr,
    }
    return repo.upsert(project_id, data)
```

---

## Task 10: Create Approvals/Obligations Endpoints

**Files:**
- Create: `backend/app/api/approvals.py`

**Interfaces:**
- Consumes: ApprovalsRepository, ObligationsRepository
- Produces: Read-only endpoints for approvals and obligations

- [ ] **Step 1: Create api/approvals.py**

```python
"""Approvals and obligations endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_approvals_repository, get_obligations_repository
from app.repositories.approvals import ApprovalsRepository
from app.repositories.obligations import ObligationsRepository
from app.rules.engine import evaluate_applicability
from app.rules.models import EntityProfile, Obligation

router = APIRouter()


@router.get("/approvals")
async def list_approvals(
    repo: ApprovalsRepository = Depends(get_approvals_repository),
):
    """List all active approvals."""
    return repo.get_active()


@router.get("/approvals/{approval_id}")
async def get_approval(
    approval_id: UUID,
    repo: ApprovalsRepository = Depends(get_approvals_repository),
):
    """Get an approval with its rules."""
    approval = repo.get_with_rules(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.get("/obligations")
async def list_obligations(
    repo: ObligationsRepository = Depends(get_obligations_repository),
):
    """List all obligations."""
    return repo.get_all_active()


@router.post("/obligations/applicable")
async def get_applicable_obligations(
    entity_type: str,
    sector: str,
    jurisdictions: list[str] = [],
    headcount: int = 0,
    annual_turnover_inr: float = 0,
    repo: ObligationsRepository = Depends(get_obligations_repository),
):
    """Get obligations applicable to an entity profile."""
    profile = EntityProfile(
        entity_type=entity_type,
        sector=sector,
        jurisdictions=jurisdictions,
        headcount=headcount,
        annual_turnover_inr=annual_turnover_inr,
    )
    obligations = repo.get_all_active()
    obligation_models = [Obligation(**o) for o in obligations]
    results = evaluate_applicability(obligation_models, profile)
    return [r.model_dump() for r in results]
```

---

## Task 11: Create Applications Endpoints

**Files:**
- Create: `backend/app/api/applications.py`

**Interfaces:**
- Consumes: ApplicationsRepository
- Produces: Application CRUD endpoints

- [ ] **Step 1: Create api/applications.py**

```python
"""Applications endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_applications_repository
from app.repositories.applications import ApplicationsRepository

router = APIRouter()


@router.post("/applications")
async def create_application(
    project_id: UUID,
    approval_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
):
    """Create a new application."""
    data = {
        "project_id": str(project_id),
        "approval_id": str(approval_id),
        "status": "draft",
    }
    return repo.create_with_reference(data)


@router.get("/applications/{application_id}")
async def get_application(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
):
    """Get an application by ID."""
    application = repo.get_by_id(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("/projects/{project_id}/applications")
async def list_project_applications(
    project_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
):
    """List all applications for a project."""
    return repo.get_by_project(project_id)
```

---

## Task 12: Create FastAPI App

**Files:**
- Create: `backend/app/main.py`

**Interfaces:**
- Consumes: All API routers
- Produces: FastAPI application instance

- [ ] **Step 1: Create app/main.py**

```python
"""FastAPI application for Gujarat Industrial Approval Intelligence."""

from fastapi import FastAPI

from app.api import health, projects, approvals, applications

app = FastAPI(
    title="SIH 26130 Gujarat MVP",
    description="Gujarat Industrial Approval Intelligence API",
    version="0.1.0",
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(projects.router, tags=["projects"])
app.include_router(approvals.router, tags=["approvals"])
app.include_router(applications.router, tags=["applications"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Gujarat Industrial Approval Intelligence API"}
```

---

## Task 13: Write Repository Tests

**Files:**
- Create: `backend/tests/test_repositories.py`

**Interfaces:**
- Consumes: Repository classes with mocked Supabase client
- Produces: Tests for repository operations

- [ ] **Step 1: Create test_repositories.py**

```python
"""Tests for repository layer with mocked Supabase client."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.repositories.base import BaseRepository
from app.repositories.projects import ProjectRepository
from app.repositories.project_facts import ProjectFactsRepository


@pytest.fixture
def mock_client():
    """Create a mock Supabase client."""
    client = MagicMock()
    client.table.return_value = MagicMock()
    return client


class TestBaseRepository:
    """Tests for BaseRepository."""

    def test_get_by_id(self, mock_client):
        """Test get_by_id returns record."""
        repo = BaseRepository(mock_client, "test_table")
        mock_result = MagicMock()
        mock_result.data = [{"id": "123", "name": "test"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_id("123")
        assert result == {"id": "123", "name": "test"}

    def test_get_by_id_not_found(self, mock_client):
        """Test get_by_id returns None when not found."""
        repo = BaseRepository(mock_client, "test_table")
        mock_result = MagicMock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_id("123")
        assert result is None


class TestProjectRepository:
    """Tests for ProjectRepository."""

    def test_get_by_applicant(self, mock_client):
        """Test get_by_applicant returns projects."""
        repo = ProjectRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "123", "name": "test"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_applicant("applicant-123")
        assert len(result) == 1
        assert result[0]["name"] == "test"
```

---

## Task 14: Write API Tests

**Files:**
- Create: `backend/tests/test_api_health.py`
- Create: `backend/tests/test_api_projects.py`

**Interfaces:**
- Consumes: FastAPI TestClient with mocked dependencies
- Produces: Tests for API endpoints

- [ ] **Step 1: Create test_api_health.py**

```python
"""Tests for health check endpoint."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root():
    """Test root endpoint."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
```

- [ ] **Step 2: Create test_api_projects.py**

```python
"""Tests for project endpoints."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def mock_project_repo():
    """Mock project repository."""
    with patch("app.api.projects.get_project_repository") as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


def test_create_project(mock_project_repo):
    """Test create project endpoint."""
    mock_project_repo.create.return_value = {
        "id": str(uuid4()),
        "name": "Test Project",
    }

    client = TestClient(app)
    response = client.post("/projects?name=Test+Project")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"


def test_get_project_not_found(mock_project_repo):
    """Test get project returns 404 when not found."""
    mock_project_repo.get_by_id.return_value = None

    client = TestClient(app)
    response = client.get(f"/projects/{uuid4()}")
    assert response.status_code == 404
```

---

## Task 15: Write Integration Test

**Files:**
- Create: `backend/tests/test_integration.py`

**Interfaces:**
- Consumes: All components with mocked Supabase
- Produces: Integration test for applicability flow

- [ ] **Step 1: Create test_integration.py**

```python
"""Integration test for applicability evaluation flow."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.rules.engine import evaluate_applicability
from app.rules.models import EntityProfile, Obligation


def test_applicability_evaluation():
    """Test that applicability evaluation works end-to-end."""
    # Create a mock obligation
    obligation = Obligation(
        canonical_id="test-obl-1",
        instrument_id="instrument-1",
        section="3",
        type="filing",
        summary="Test obligation",
        applicability_conditions=[
            {"field": "sector", "op": "eq", "value": "chemicals"}
        ],
        frequency="annual",
        deadline_rule={"kind": "fixed-date", "month": 3, "day": 31},
        proof_types=[],
        penalty={},
        source_refs=[{"source_id": "src-1", "section": "3"}],
        version="1",
        confidence=1.0,
    )

    # Create entity profile that matches
    profile = EntityProfile(
        entity_type="pvt-ltd",
        sector="chemicals",
        jurisdictions=["IN-GJ"],
        headcount=50,
        annual_turnover_inr=10000000,
    )

    # Evaluate
    results = evaluate_applicability([obligation], profile)

    # Should be applicable
    assert len(results) == 1
    assert results[0].result == "applicable"
```

---

## Task 16: Run All Tests

**Files:**
- None (verification step)

**Interfaces:**
- Consumes: All tests
- Produces: Test results

- [ ] **Step 1: Run all tests**

Run: `cd D:\SIH\backend && python -m pytest tests/ -v`

- [ ] **Step 2: Verify all tests pass**

All tests should pass. Fix any failures.

- [ ] **Step 3: Run linting**

Run: `cd D:\SIH\backend && python -m ruff check app/ tests/`

- [ ] **Step 4: Fix any lint issues**

Run: `cd D:\SIH\backend && python -m ruff check app/ tests/ --fix`

---

## Task 17: Update Documentation

**Files:**
- Modify: `D:\SIH\ARCHITECTURE.md`
- Modify: `D:\SIH\RULES.md`

**Interfaces:**
- Consumes: Implementation details
- Produces: Updated documentation

- [ ] **Step 1: Update ARCHITECTURE.md**

Add Phase 2A status section.

- [ ] **Step 2: Update RULES.md**

Add backend structure information.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-09-14-phase-2a-database-api.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
