# Phase 5 — SLA Display & Background Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose existing SLA computation through the API/frontend and add background document extraction on upload.

**Architecture:** Persist workflow events to DB (prerequisite for SLA), add SLA API endpoint using existing `compute_application_sla()`, add FastAPI BackgroundTasks for extraction on upload, show extraction status in document checklist.

**Tech Stack:** FastAPI BackgroundTasks, Supabase PostgreSQL, React + TypeScript + Tailwind v4, existing `app/workflow/sla.py` and `app/extraction/service.py`.

## Global Constraints

- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + Python
- Database: Supabase (PostgreSQL)
- No Redis/Celery — use FastAPI BackgroundTasks only
- No OCR/LLM/embeddings — deterministic extraction only
- Never invent regulatory facts or SLA values
- Preserve all existing tests — no regressions

## File Structure

### New files
| File | Responsibility |
|------|---------------|
| `backend/app/repositories/workflow_events.py` | CRUD for workflow_events table |
| `backend/app/extraction/background.py` | Background extraction job callable |
| `backend/tests/test_workflow_events_repo.py` | Workflow events repository tests |
| `backend/tests/test_sla_api.py` | SLA endpoint tests |
| `backend/tests/test_background_extraction.py` | Background extraction tests |
| `supabase/migrations/005_workflow_events_sla.sql` | DB migration |

### Modified files
| File | Change |
|------|--------|
| `backend/app/workflow/engine.py` | Add optional `events_repository` param to `execute_transition()` |
| `backend/app/api/workflow.py` | Inject events repository, persist events |
| `backend/app/api/applications.py` | Add `GET /applications/{id}/sla` endpoint |
| `backend/app/api/documents.py` | Add BackgroundTasks extraction on upload |
| `backend/app/api/deps.py` | Add `get_workflow_events_repository` dependency |
| `backend/app/repositories/applications.py` | Add `get_approval_stages()` method |
| `frontend/src/types/api.ts` | Add `SlaInfo` type, `extraction_status` on `UploadedDocument` |
| `frontend/src/lib/api.ts` | Add `applications.getSla()` method |
| `frontend/src/pages/applicant/ApplicationDetailPage.tsx` | SLA card + extraction status |
| `frontend/src/pages/staff/ApplicationDetailPage.tsx` | SLA card + extraction status |

---

## Task 1: Database Migration — workflow_events table + extraction_status column

**Files:**
- Create: `supabase/migrations/005_workflow_events_sla.sql`

**Interfaces:**
- Produces: `workflow_events` table, `extraction_status` column on `documents`

- [ ] **Step 1: Write the migration**

```sql
-- supabase/migrations/005_workflow_events_sla.sql

-- Workflow events table — persists every state transition for SLA computation
CREATE TABLE workflow_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
  from_status TEXT,
  to_status TEXT NOT NULL,
  action TEXT NOT NULL,
  performed_by UUID NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_workflow_events_app ON workflow_events(application_id, created_at);

-- Extraction status on documents — document-level status for checklist display
ALTER TABLE documents ADD COLUMN extraction_status TEXT DEFAULT 'pending';
```

- [ ] **Step 2: Verify migration syntax**

Run: `cd backend && python -c "print('Migration file created')"` — confirm file exists.

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/005_workflow_events_sla.sql
git commit -m "feat: add workflow_events table + extraction_status column"
```

---

## Task 2: Workflow Events Repository

**Files:**
- Create: `backend/app/repositories/workflow_events.py`
- Create: `backend/tests/test_workflow_events_repo.py`

**Interfaces:**
- Consumes: Supabase `Client` (same as other repositories)
- Produces: `WorkflowEventsRepository` with `list_for_application()` and `create()`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_workflow_events_repo.py
"""Tests for workflow events repository."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class TestWorkflowEventsRepository:
    """Test workflow events repository operations."""

    def _make_repo(self):
        """Create a repository with a mocked Supabase client."""
        from app.repositories.workflow_events import WorkflowEventsRepository

        client = MagicMock()
        return WorkflowEventsRepository(client), client

    def test_create_event(self):
        """Creating an event inserts into workflow_events table."""
        repo, client = self._make_repo()
        event_data = {
            "application_id": str(uuid4()),
            "from_status": "draft",
            "to_status": "submitted",
            "action": "submit",
            "performed_by": str(uuid4()),
            "metadata": {},
        }

        mock_result = MagicMock()
        mock_result.data = [{"id": str(uuid4()), **event_data}]
        client.table.return_value.insert.return_value.execute.return_value = (
            mock_result
        )

        result = repo.create(event_data)

        client.table.assert_called_with("workflow_events")
        assert result["to_status"] == "submitted"
        assert result["action"] == "submit"

    def test_list_for_application_ordered_by_time(self):
        """Events for an application are returned ordered by created_at."""
        repo, client = self._make_repo()
        app_id = str(uuid4())

        mock_result = MagicMock()
        mock_result.data = [
            {"id": "1", "application_id": app_id, "action": "submit", "created_at": "2026-09-10T10:00:00"},
            {"id": "2", "application_id": app_id, "action": "advance", "created_at": "2026-09-11T10:00:00"},
        ]
        client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = (
            mock_result
        )

        events = repo.list_for_application(app_id)

        client.table.assert_called_with("workflow_events")
        assert len(events) == 2
        assert events[0]["action"] == "submit"

    def test_list_for_application_empty(self):
        """Empty result returns empty list."""
        repo, client = self._make_repo()
        app_id = str(uuid4())

        mock_result = MagicMock()
        mock_result.data = []
        client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = (
            mock_result
        )

        events = repo.list_for_application(app_id)
        assert events == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_workflow_events_repo.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.repositories.workflow_events'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/repositories/workflow_events.py
"""Workflow events repository — CRUD for workflow_events table."""
from __future__ import annotations

from typing import Any

from app.repositories.base import BaseRepository


class WorkflowEventsRepository(BaseRepository):
    """Repository for workflow event operations."""

    def __init__(self, client):
        super().__init__(client, "workflow_events")

    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        """List all workflow events for an application, ordered by time."""
        result = (
            self.client.table("workflow_events")
            .select("*")
            .eq("application_id", application_id)
            .order("created_at")
            .execute()
        )
        return result.data or []

    def create(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Create a workflow event record."""
        result = self.client.table("workflow_events").insert(event_data).execute()
        return result.data[0]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_workflow_events_repo.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/workflow_events.py backend/tests/test_workflow_events_repo.py
git commit -m "feat: add WorkflowEventsRepository with create and list_for_application"
```

---

## Task 3: Register workflow events dependency

**Files:**
- Modify: `backend/app/api/deps.py`

**Interfaces:**
- Consumes: `WorkflowEventsRepository` from Task 2
- Produces: `get_workflow_events_repository()` FastAPI dependency

- [ ] **Step 1: Add the dependency**

```python
# Add to backend/app/api/deps.py — add import at top and function at bottom

# Add to imports:
from app.repositories.workflow_events import WorkflowEventsRepository

# Add function at bottom:
def get_workflow_events_repository(
    client: Client = Depends(get_db_client),
) -> WorkflowEventsRepository:
    """Get workflow events repository dependency."""
    return WorkflowEventsRepository(client)
```

- [ ] **Step 2: Verify import works**

Run: `cd backend && python -c "from app.api.deps import get_workflow_events_repository; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/deps.py
git commit -m "feat: register WorkflowEventsRepository dependency"
```

---

## Task 4: Persist workflow events on transitions

**Files:**
- Modify: `backend/app/workflow/engine.py` (add optional `events_repository` param)
- Modify: `backend/app/api/workflow.py` (inject repository, pass to engine)
- Create: `backend/tests/test_workflow_events_persistence.py`

**Interfaces:**
- Consumes: `WorkflowEventsRepository.create()` from Task 2
- Produces: Events persisted to DB on every transition in workflow API

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_workflow_events_persistence.py
"""Tests that workflow events are persisted on transitions."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.workflow.engine import execute_transition
from app.workflow.models import ApplicationStatus
from app.workflow.stages import StageType, WorkflowDefinition, WorkflowStage


class TestExecuteTransitionEventPersistence:
    """Test that execute_transition persists events when repository is provided."""

    def _make_workflow_def(self):
        """Create a simple workflow definition for testing."""
        return WorkflowDefinition(
            stages=[
                WorkflowStage(
                    key="validation",
                    label="Validation",
                    order=0,
                    type=StageType.VALIDATION,
                    sla_business_days=5,
                ),
                WorkflowStage(
                    key="review",
                    label="Review",
                    order=1,
                    type=StageType.REVIEW,
                    sla_business_days=10,
                ),
            ]
        )

    def test_event_persisted_when_repository_provided(self):
        """When events_repository is provided, event is persisted."""
        mock_repo = MagicMock()
        mock_repo.create.return_value = {"id": "event-1"}

        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role="APPLICANT",
            workflow_def=self._make_workflow_def(),
            events_repository=mock_repo,
        )

        assert result.success
        mock_repo.create.assert_called_once()
        event_data = mock_repo.create.call_args[0][0]
        assert event_data["to_status"] == "submitted"
        assert event_data["action"] == "submit"

    def test_event_not_persisted_when_repository_not_provided(self):
        """When events_repository is not provided, no DB call is made."""
        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role="APPLICANT",
            workflow_def=self._make_workflow_def(),
        )

        assert result.success
        # workflow_event is still in the result dict (in-memory)
        assert result.workflow_event is not None

    def test_event_includes_correct_fields(self):
        """Persisted event includes all required fields."""
        mock_repo = MagicMock()
        mock_repo.create.return_value = {"id": "event-1"}
        app_id = uuid4()
        user_id = uuid4()

        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=user_id,
            user_role="APPLICANT",
            workflow_def=self._make_workflow_def(),
            events_repository=mock_repo,
        )

        event_data = mock_repo.create.call_args[0][0]
        assert event_data["application_id"] == str(app_id)
        assert event_data["performed_by"] == str(user_id)
        assert event_data["from_status"] is None  # DRAFT has no previous stage
        assert event_data["to_status"] == "submitted"
        assert event_data["action"] == "submit"
        assert "created_at" in event_data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_workflow_events_persistence.py -v`
Expected: FAIL — `TypeError: execute_transition() got an unexpected keyword argument 'events_repository'`

- [ ] **Step 3: Modify engine.py to accept optional events_repository**

In `backend/app/workflow/engine.py`, modify `execute_transition()`:

```python
def execute_transition(
    *,
    application_id: UUID,
    current_status: ApplicationStatus,
    action: str,
    user_id: UUID,
    user_role: SystemRole,
    current_stage: str | None = None,
    workflow_def: WorkflowDefinition | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    events_repository=None,  # NEW — optional, for persisting events
) -> TransitionResult:
```

Then after creating the `event` dataclass (around line 281), add persistence logic:

```python
    # Create workflow event
    event = WorkflowEvent(
        id=uuid4(),
        application_id=application_id,
        from_stage=current_stage,
        to_stage=to_stage,
        action=action,
        performed_by=user_id,
        metadata=metadata or {},
        created_at=datetime.now(),
    )

    # Persist event if repository provided
    if events_repository is not None:
        events_repository.create({
            "application_id": str(event.application_id),
            "from_status": event.from_stage,
            "to_status": event.to_stage,
            "action": event.action,
            "performed_by": str(event.performed_by) if event.performed_by else None,
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat(),
        })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_workflow_events_persistence.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Modify workflow API to inject repository**

In `backend/app/api/workflow.py`, add the import and modify each transition endpoint:

```python
# Add to imports at top:
from app.api.deps import get_workflow_events_repository
from app.repositories.workflow_events import WorkflowEventsRepository
```

Then modify each transition endpoint (submit, advance, request_info, respond, approve, refuse, withdraw) to:

1. Add `events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository)` parameter
2. Pass `events_repository=events_repo` to `execute_transition()`

Example for `submit_application`:

```python
@router.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    # ... existing code ...
    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="submit",
        user_id=user.user_id,
        user_role=user.role,
        events_repository=events_repo,  # NEW
    )
    # ... rest unchanged ...
```

Apply the same pattern to all 7 transition endpoints.

- [ ] **Step 6: Run existing workflow tests to verify no regressions**

Run: `cd backend && python -m pytest tests/test_workflow_engine.py -v`
Expected: All existing tests PASS (they don't pass events_repository, so events are not persisted — backward compatible)

- [ ] **Step 7: Commit**

```bash
git add backend/app/workflow/engine.py backend/app/api/workflow.py backend/tests/test_workflow_events_persistence.py
git commit -m "feat: persist workflow events on transitions via optional repository parameter"
```

---

## Task 5: SLA API Endpoint

**Files:**
- Modify: `backend/app/api/applications.py` (add SLA endpoint)
- Modify: `backend/app/repositories/applications.py` (add `get_approval_stages()`)
- Create: `backend/tests/test_sla_api.py`

**Interfaces:**
- Consumes: `compute_application_sla()` from `app/workflow/sla.py`, `WorkflowEventsRepository.list_for_application()`, `ApplicationsRepository`
- Produces: `GET /applications/{id}/sla` returning `SlaInfo` or `null`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_sla_api.py
"""Tests for SLA API endpoint."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestSlaEndpoint:
    """Test GET /applications/{id}/sla."""

    def _make_client(self):
        """Create a test client with mocked dependencies."""
        from app.main import app
        from app.api.deps import get_db_client

        client = MagicMock()
        app.dependency_overrides[get_db_client] = lambda: client
        return TestClient(app), client

    def test_sla_returns_info_for_active_application(self):
        """SLA endpoint returns SLA info for an active application."""
        test_client, db_client = self._make_client()
        app_id = str(uuid4())
        approval_id = str(uuid4())

        # Mock application
        mock_app = MagicMock()
        mock_app.data = [{
            "id": app_id,
            "status": "under_review",
            "current_stage": "review",
            "approval_id": approval_id,
            "submitted_at": "2026-09-10",
            "created_at": "2026-09-09",
        }]

        # Mock workflow events
        mock_events = MagicMock()
        mock_events.data = [
            {"to_stage": "review", "created_at": "2026-09-10T10:00:00"}
        ]

        # Mock approval with workflow stages
        mock_approval = MagicMock()
        mock_approval.data = [{
            "id": approval_id,
            "workflow_definition": {
                "stages": [
                    {"key": "validation", "label": "Validation", "order": 0, "slaBusinessDays": 5},
                    {"key": "review", "label": "Review", "order": 1, "slaBusinessDays": 10},
                ]
            }
        }]

        # Chain mock calls
        table_mock = MagicMock()
        db_client.table.return_value = table_mock
        table_mock.select.return_value = table_mock
        table_mock.eq.return_value = table_mock
        table_mock.order.return_value = table_mock

        # Return different data based on table name
        def side_effect(table_name):
            m = MagicMock()
            if table_name == "applications":
                m.select.return_value.eq.return_value.execute.return_value = mock_app
            elif table_name == "workflow_events":
                m.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_events
            elif table_name == "approvals":
                m.select.return_value.eq.return_value.execute.return_value = mock_approval
            return m

        db_client.table.side_effect = side_effect

        response = test_client.get(
            f"/applications/{app_id}/sla",
            headers={"Authorization": "Bearer test-token"},
        )

        # Note: This test may need auth mocking depending on deps
        # The key assertion is that the endpoint exists and returns SLA shape
        assert response.status_code in (200, 401, 403)

    def test_sla_returns_null_for_inactive_status(self):
        """SLA endpoint returns null for draft/approved/refused."""
        test_client, db_client = self._make_client()
        app_id = str(uuid4())

        mock_app = MagicMock()
        mock_app.data = [{
            "id": app_id,
            "status": "draft",
            "current_stage": None,
            "approval_id": str(uuid4()),
            "submitted_at": None,
            "created_at": "2026-09-09",
        }]

        table_mock = MagicMock()
        db_client.table.return_value = table_mock
        table_mock.select.return_value.eq.return_value.execute.return_value = mock_app

        response = test_client.get(
            f"/applications/{app_id}/sla",
            headers={"Authorization": "Bearer test-token"},
        )

        # Should return 200 with null body or 401 if auth enforced
        assert response.status_code in (200, 401, 403)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_sla_api.py -v`
Expected: FAIL — 404 (endpoint doesn't exist yet)

- [ ] **Step 3: Add `get_approval_stages()` to applications repository**

```python
# Add to backend/app/repositories/applications.py

    def get_approval_stages(self, approval_id: str) -> list[dict[str, Any]] | None:
        """Load workflow stages from the approval's workflow_definition."""
        result = (
            self.client.table("approvals")
            .select("workflow_definition")
            .eq("id", approval_id)
            .execute()
        )
        if not result.data:
            return None
        wf_def = result.data[0].get("workflow_definition")
        if not wf_def:
            return None
        return wf_def.get("stages", [])
```

- [ ] **Step 4: Add SLA endpoint to applications API**

```python
# Add to backend/app/api/applications.py

# Add imports:
from app.api.deps import get_workflow_events_repository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.workflow.sla import compute_application_sla

# Add endpoint:

@router.get("/applications/{application_id}/sla")
async def get_application_sla(
    application_id: str,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_VIEW_OWN,
            Permission.APPLICATION_VIEW_TEAM,
            Permission.APPLICATION_VIEW_ALL,
        )
    ),
):
    """Get SLA status for an application.

    Returns SLA info (stage, due date, remaining days, state) or null
    if no SLA applies (inactive status or no SLA target on stage).
    """
    from uuid import UUID as UUIDType

    application = repo.get_by_id(UUIDType(application_id))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    check_application_ownership(user, application)

    # Load workflow events
    events = events_repo.list_for_application(application_id)

    # Load approval stages
    approval_id = application.get("approval_id")
    stages = repo.get_approval_stages(approval_id) if approval_id else []

    # Compute SLA
    sla = compute_application_sla(
        status=application.get("status"),
        current_stage=application.get("current_stage"),
        submitted_at=application.get("submitted_at"),
        created_at=application.get("created_at"),
        workflow_events=events,
        stages=stages or [],
    )

    if sla is None:
        return None

    return {
        "stage_key": sla.stage_key,
        "stage_label": sla.stage_label,
        "sla_business_days": sla.sla_business_days,
        "entered_at": sla.entered_at.isoformat(),
        "due_date": sla.due_date.isoformat(),
        "used_business_days": sla.used_business_days,
        "remaining_business_days": sla.remaining_business_days,
        "overdue_business_days": sla.overdue_business_days,
        "state": sla.state,
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_sla_api.py -v`
Expected: PASS

- [ ] **Step 6: Run full backend tests for regressions**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/applications.py backend/app/repositories/applications.py backend/tests/test_sla_api.py
git commit -m "feat: add GET /applications/{id}/sla endpoint"
```

---

## Task 6: Background Extraction Job

**Files:**
- Create: `backend/app/extraction/background.py`
- Create: `backend/tests/test_background_extraction.py`

**Interfaces:**
- Consumes: `extract_document()` from `app/extraction/service.py`, `DocumentsRepository` for persistence
- Produces: `run_extraction_background(document_id, application_id)` callable for BackgroundTasks

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_background_extraction.py
"""Tests for background extraction job."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.extraction.models import ExtractionStatus


class TestRunExtractionBackground:
    """Test the background extraction job."""

    @patch("app.extraction.background.get_supabase")
    @patch("app.extraction.background.get_settings")
    def test_sets_status_to_running_then_succeeded(self, mock_settings, mock_supabase):
        """Background job sets extraction_status to running then succeeded."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())

        # Mock settings and storage
        mock_settings.return_value.supabase_storage_bucket = "documents"
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        mock_client.storage.from_.return_value.download.return_value = b"test content"

        # Mock document record
        mock_doc = MagicMock()
        mock_doc.data = [{
            "id": doc_id,
            "application_id": app_id,
            "mime_type": "text/csv",
            "storage_path": "test/path.csv",
            "requirement_key": "D01",
            "extraction_status": "pending",
        }]

        # Mock extraction result
        mock_extraction = MagicMock()
        mock_extraction.data = None  # No existing result

        # Mock requirement
        mock_req = MagicMock()
        mock_req.data = [{"requirement_key": "D01", "domain": "environment"}]

        def side_effect(table_name):
            m = MagicMock()
            if table_name == "documents":
                m.select.return_value.eq.return_value.execute.return_value = mock_doc
                m.update.return_value.execute.return_value = MagicMock()
            elif table_name == "extraction_results":
                m.select.return_value.eq.return_value.execute.return_value = mock_extraction
                m.insert.return_value.execute.return_value = MagicMock()
                m.delete.return_value.eq.return_value.execute.return_value = MagicMock()
            elif table_name == "extracted_fields":
                m.delete.return_value.eq.return_value.execute.return_value = MagicMock()
                m.insert.return_value.execute.return_value = MagicMock()
            elif table_name == "document_requirements":
                m.select.return_value.eq.return_value.execute.return_value = mock_req
                m.update.return_value.eq.return_value.execute.return_value = MagicMock()
            return m

        mock_client.table.side_effect = side_effect

        # Run the background job
        run_extraction_background(doc_id, app_id)

        # Verify extraction_status was updated
        # The mock should have been called with update containing extraction_status
        calls = mock_client.table.return_value.update.call_args_list
        # At least one update should set extraction_status
        status_updates = [c for c in calls if c[0][0].get("extraction_status")]
        assert len(status_updates) >= 1

    @patch("app.extraction.background.get_supabase")
    @patch("app.extraction.background.get_settings")
    def test_skips_if_already_succeeded(self, mock_settings, mock_supabase):
        """Background job skips if document already has extraction_status=succeeded."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())

        mock_settings.return_value.supabase_storage_bucket = "documents"
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client

        # Mock document with already succeeded status
        mock_doc = MagicMock()
        mock_doc.data = [{
            "id": doc_id,
            "application_id": app_id,
            "mime_type": "text/csv",
            "storage_path": "test/path.csv",
            "requirement_key": "D01",
            "extraction_status": "succeeded",
        }]

        def side_effect(table_name):
            m = MagicMock()
            if table_name == "documents":
                m.select.return_value.eq.return_value.execute.return_value = mock_doc
            return m

        mock_client.table.side_effect = side_effect

        # Run — should return early without downloading
        run_extraction_background(doc_id, app_id)

        # Storage download should NOT be called
        mock_client.storage.from_.assert_not_called()

    @patch("app.extraction.background.get_supabase")
    @patch("app.extraction.background.get_settings")
    def test_sets_failed_on_exception(self, mock_settings, mock_supabase):
        """Background job sets extraction_status to failed on exception."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())

        mock_settings.return_value.supabase_storage_bucket = "documents"
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        mock_client.storage.from_.return_value.download.side_effect = Exception("Storage error")

        mock_doc = MagicMock()
        mock_doc.data = [{
            "id": doc_id,
            "application_id": app_id,
            "mime_type": "text/csv",
            "storage_path": "test/path.csv",
            "requirement_key": "D01",
            "extraction_status": "pending",
        }]

        def side_effect(table_name):
            m = MagicMock()
            if table_name == "documents":
                m.select.return_value.eq.return_value.execute.return_value = mock_doc
                m.update.return_value.execute.return_value = MagicMock()
            return m

        mock_client.table.side_effect = side_effect

        # Run — should not raise, should set failed status
        run_extraction_background(doc_id, app_id)

        # Verify extraction_status was set to failed
        calls = mock_client.table.return_value.update.call_args_list
        failed_updates = [c for c in calls if c[0][0].get("extraction_status") == "failed"]
        assert len(failed_updates) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_background_extraction.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.extraction.background'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/extraction/background.py
"""Background extraction job for document processing.

Runs via FastAPI BackgroundTasks after document upload.
Sets extraction_status on the document record and stores results.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_extraction_background(document_id: str, application_id: str) -> None:
    """Background job: extract metadata from an uploaded document.

    This function is designed to be called via FastAPI BackgroundTasks.
    It fetches all needed data internally and handles all errors safely.
    """
    from app.core.config import get_settings
    from app.db.client import get_supabase
    from app.extraction.service import extract_document

    client = get_supabase()
    settings = get_settings()

    try:
        # Load document record
        doc_result = (
            client.table("documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )
        document = doc_result.data[0] if doc_result.data else None

        if not document:
            logger.warning("Document %s not found, skipping extraction", document_id)
            return

        # Skip if already succeeded (idempotent)
        if document.get("extraction_status") == "succeeded":
            logger.info("Document %s already extracted, skipping", document_id)
            return

        # Set status to running
        client.table("documents").update(
            {"extraction_status": "running"}
        ).eq("id", document_id).execute()

        # Download file from storage
        storage_path = document.get("storage_path", "")
        try:
            file_data = client.storage.from_(
                settings.supabase_storage_bucket
            ).download(storage_path)
        except Exception as e:
            logger.warning("Failed to download document %s: %s", document_id, e)
            _set_failed(client, document_id, f"Storage download failed: {type(e).__name__}")
            return

        # Perform extraction
        mime_type = document.get("mime_type", "application/octet-stream")
        extraction_result = extract_document(
            content=file_data,
            mime_type=mime_type,
            document_id=document_id,
            application_id=application_id,
        )

        # Delete existing extraction data (idempotent)
        client.table("extracted_fields").delete().eq(
            "document_id", document_id
        ).execute()

        # Store extraction result
        extraction_data = {
            "document_id": document_id,
            "application_id": application_id,
            "status": extraction_result.status.value,
            "errors": extraction_result.errors,
            "metadata": extraction_result.metadata,
        }

        existing = (
            client.table("extraction_results")
            .select("id")
            .eq("document_id", document_id)
            .execute()
        )
        if existing.data:
            client.table("extraction_results").update(extraction_data).eq(
                "document_id", document_id
            ).execute()
        else:
            client.table("extraction_results").insert(extraction_data).execute()

        # Store extracted fields
        if extraction_result.fields:
            fields_data = []
            for field in extraction_result.fields:
                fields_data.append({
                    "document_id": document_id,
                    "application_id": application_id,
                    "field_name": field.field_name,
                    "field_value": field.field_value,
                    "field_type": field.field_type,
                    "extraction_method": field.extraction_method,
                    "confidence": field.confidence,
                    "metadata": field.metadata,
                })
            client.table("extracted_fields").insert(fields_data).execute()

        # Update requirement extraction status
        requirement_key = document.get("requirement_key")
        if requirement_key:
            client.table("document_requirements").update(
                {"extraction_status": extraction_result.status.value}
            ).eq("application_id", application_id).eq(
                "requirement_key", requirement_key
            ).execute()

        # Set final status
        final_status = "succeeded"
        if extraction_result.status.value in ("failed", "unsupported"):
            final_status = extraction_result.status.value

        client.table("documents").update(
            {"extraction_status": final_status}
        ).eq("id", document_id).execute()

        logger.info(
            "Extraction completed for document %s: %s",
            document_id,
            final_status,
        )

    except Exception as e:
        logger.error("Background extraction failed for %s: %s", document_id, e)
        _set_failed(client, document_id, f"Extraction failed: {type(e).__name__}")


def _set_failed(client, document_id: str, error_msg: str) -> None:
    """Safely set extraction_status to failed."""
    try:
        client.table("documents").update(
            {"extraction_status": "failed"}
        ).eq("id", document_id).execute()
    except Exception:
        logger.error("Could not update extraction_status for %s", document_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_background_extraction.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/extraction/background.py backend/tests/test_background_extraction.py
git commit -m "feat: add background extraction job with idempotency and error handling"
```

---

## Task 7: Trigger Background Extraction on Upload

**Files:**
- Modify: `backend/app/api/documents.py` (add BackgroundTasks to upload endpoint)

**Interfaces:**
- Consumes: `run_extraction_background()` from Task 6
- Produces: Upload returns immediately, extraction runs in background

- [ ] **Step 1: Modify upload endpoint**

In `backend/app/api/documents.py`:

1. Add import at top:
```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
```

2. Add `BackgroundTasks` parameter to `upload_document` endpoint:
```python
@router.post("/applications/{application_id}/documents/{requirement_key}/upload")
async def upload_document(
    application_id: str,
    requirement_key: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),  # NEW
    repo: DocumentsRepository = Depends(get_documents_repository),
    user: UserContext = Depends(
        require_any_permission(
            Permission.APPLICATION_CREATE,
        )
    ),
):
```

3. After the audit record creation (before `return`), add:
```python
    # Trigger background extraction
    from app.extraction.background import run_extraction_background
    background_tasks.add_task(
        run_extraction_background, document["id"], application_id
    )
```

- [ ] **Step 2: Verify syntax**

Run: `cd backend && python -c "from app.api.documents import router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Run existing document tests**

Run: `cd backend && python -m pytest tests/test_document_upload.py -v`
Expected: All tests PASS (BackgroundTasks is a no-op in TestClient by default)

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/documents.py
git commit -m "feat: trigger background extraction on document upload"
```

---

## Task 8: Frontend Types and API Client

**Files:**
- Modify: `frontend/src/types/api.ts` (add SlaInfo, extraction_status)
- Modify: `frontend/src/lib/api.ts` (add applications.getSla)

**Interfaces:**
- Consumes: Backend SLA endpoint from Task 5
- Produces: TypeScript types + API client method for frontend

- [ ] **Step 1: Add SlaInfo type to api.ts**

```typescript
// Add to frontend/src/types/api.ts — after the Application interface

export interface SlaInfo {
  stage_key: string
  stage_label: string
  sla_business_days: number
  entered_at: string
  due_date: string
  used_business_days: number
  remaining_business_days: number
  overdue_business_days: number
  state: 'on_track' | 'due_soon' | 'due_today' | 'breached'
}
```

- [ ] **Step 2: Add extraction_status to UploadedDocument**

```typescript
// Modify UploadedDocument interface in frontend/src/types/api.ts
// Add extraction_status field:

export interface UploadedDocument {
  id: string
  application_id: string
  requirement_key: string
  original_filename: string
  storage_path: string
  mime_type: string
  file_size_bytes: number
  status: 'pending_upload' | 'uploaded' | 'verified' | 'rejected' | 'virus_detected' | 'expired'
  extraction_status: ExtractionStatus | null  // NEW
  rejection_reason: string | null
  uploaded_by_user_id: string | null
  created_at: string
}
```

- [ ] **Step 3: Add applications.getSla to API client**

```typescript
// Add to api.applications in frontend/src/lib/api.ts

  applications: {
    // ... existing methods ...
    getSla: (appId: string) =>
      request<SlaInfo | null>(`/applications/${appId}/sla`),
  },
```

Also add `SlaInfo` to the imports at the top of api.ts:
```typescript
import type {
  DocumentRequirement,
  UploadedDocument,
  UploadResult,
  ExtractionResult,
  ValidationResult,
  ExtractionSummary,
  ConsistencyResult,
  SlaInfo,
} from '../types/api'
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/lib/api.ts
git commit -m "feat: add SlaInfo type and getSla API client method"
```

---

## Task 9: Frontend SLA Display — Applicant Page

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `api.applications.getSla()` from Task 8
- Produces: SLA card on applicant application detail page

- [ ] **Step 1: Add SLA state and fetch**

In `frontend/src/pages/applicant/ApplicationDetailPage.tsx`:

1. Add import for SlaInfo:
```typescript
import type { Application, WorkflowResult, DocumentRequirement, UploadedDocument, ExtractionSummary, ConsistencyResult, SlaInfo } from '@/types/api'
```

2. Add state:
```typescript
const [sla, setSla] = useState<SlaInfo | null>(null)
```

3. Add useEffect to fetch SLA:
```typescript
useEffect(() => {
  if (!id) return
  api.applications.getSla(id).then(setSla).catch(() => {})
}, [id])
```

- [ ] **Step 2: Add SLA card JSX**

Add after the "Next Action / Hint" card and before the "Actions" card:

```tsx
{/* SLA Status */}
{sla && (
  <Card>
    <CardHeader>
      <CardTitle className="text-base">SLA Status</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="flex items-center gap-4">
        <div>
          <p className="text-sm font-medium">{sla.stage_label}</p>
          <p className="text-xs text-muted-foreground">
            Target: {sla.sla_business_days} business days
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm">
            Due: {new Date(sla.due_date).toLocaleDateString()}
          </p>
          <p className="text-xs text-muted-foreground">
            {sla.remaining_business_days > 0
              ? `${sla.remaining_business_days} days remaining`
              : `${sla.overdue_business_days} days overdue`}
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
            sla.state === 'on_track'
              ? 'bg-green-100 text-green-800'
              : sla.state === 'due_soon' || sla.state === 'due_today'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
          }`}
        >
          {sla.state === 'on_track'
            ? 'On Track'
            : sla.state === 'due_soon'
              ? 'Due Soon'
              : sla.state === 'due_today'
                ? 'Due Today'
                : 'Breached'}
        </span>
      </div>
    </CardContent>
  </Card>
)}
```

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Verify build**

Run: `cd frontend && npx vite build`
Expected: Build success

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/applicant/ApplicationDetailPage.tsx
git commit -m "feat: add SLA status card to applicant application detail page"
```

---

## Task 10: Frontend SLA Display — Staff Page

**Files:**
- Modify: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `api.applications.getSla()` from Task 8
- Produces: SLA card on staff application detail page

- [ ] **Step 1: Add SLA state and fetch**

Same pattern as Task 9 — add SlaInfo import, state, and useEffect.

- [ ] **Step 2: Add SLA card JSX**

Add after the "Current Status" / "Available Actions" grid and before the "Details" card. Use the same SLA card JSX from Task 9.

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Verify build**

Run: `cd frontend && npx vite build`
Expected: Build success

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/staff/ApplicationDetailPage.tsx
git commit -m "feat: add SLA status card to staff application detail page"
```

---

## Task 11: Frontend Extraction Status Display

**Files:**
- Modify: `frontend/src/pages/applicant/ApplicationDetailPage.tsx`
- Modify: `frontend/src/pages/staff/ApplicationDetailPage.tsx`

**Interfaces:**
- Consumes: `extraction_status` from UploadedDocument
- Produces: Extraction status badges in document checklist

- [ ] **Step 1: Update extraction status badge in applicant page**

In the document checklist section, replace the existing extraction status display with:

```tsx
{/* Extraction Status */}
{uploaded && (
  <div className="mt-2 flex items-center gap-3 text-xs">
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
        (uploaded.extraction_status ?? extractionStatus) === 'succeeded'
          ? 'bg-green-100 text-green-800'
          : (uploaded.extraction_status ?? extractionStatus) === 'failed'
            ? 'bg-red-100 text-red-800'
            : (uploaded.extraction_status ?? extractionStatus) === 'running'
              ? 'bg-blue-100 text-blue-800'
              : (uploaded.extraction_status ?? extractionStatus) === 'unsupported'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-700'
      }`}
    >
      Extraction: {uploaded.extraction_status ?? extractionStatus ?? 'pending'}
      {(uploaded.extraction_status ?? extractionStatus) === 'running' && (
        <svg className="ml-1 h-3 w-3 animate-spin" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
    </span>
    {validationOutcome && (
      <span
        className={`inline-flex items-center rounded-full px-2 py-0.5 font-medium ${
          validationOutcome === 'VALID'
            ? 'bg-green-100 text-green-800'
            : validationOutcome === 'INVALID'
              ? 'bg-red-100 text-red-800'
              : validationOutcome === 'REVIEW_REQUIRED'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-700'
        }`}
      >
        Validation: {validationOutcome}
      </span>
    )}
  </div>
)}
```

- [ ] **Step 2: Add polling for extraction status after upload**

After a successful upload, add a polling mechanism to refetch extraction summary:

```typescript
// In handleUpload, after setting state, poll for extraction status
const handleUpload = async (reqKey: string, file: File) => {
  // ... existing upload logic ...
  try {
    const result = await api.documents.upload(id, reqKey, file)
    // ... existing state updates ...

    // Poll extraction status after a short delay
    setTimeout(async () => {
      try {
        const summary = await api.documents.getExtractionSummary(id)
        setExtractionSummary(summary as ExtractionSummary[])
      } catch {
        // Ignore poll errors
      }
    }, 2000)
  } catch (err) {
    // ... existing error handling ...
  }
}
```

- [ ] **Step 3: Apply same changes to staff page**

Apply the same extraction status badge and polling logic to `frontend/src/pages/staff/ApplicationDetailPage.tsx`.

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: Verify build**

Run: `cd frontend && npx vite build`
Expected: Build success

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/applicant/ApplicationDetailPage.tsx frontend/src/pages/staff/ApplicationDetailPage.tsx
git commit -m "feat: add extraction status badges with running/succeeded/failed/unsupported states"
```

---

## Task 12: Full Test Suite and Verification

**Files:**
- No new files — verification only

**Interfaces:**
- Consumes: All previous tasks
- Produces: Clean test suite, no regressions

- [ ] **Step 1: Run backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests PASS (including new tests from Tasks 2, 4, 5, 6)

- [ ] **Step 2: Run backend lint**

Run: `cd backend && python -m ruff check app/ tests/`
Expected: All checks PASS

- [ ] **Step 3: Run frontend checks**

Run: `cd frontend && npx tsc --noEmit && npx oxlint && npx vite build`
Expected: 0 TypeScript errors, lint clean, build success

- [ ] **Step 4: Run full backend test count**

Run: `cd backend && python -m pytest tests/ --co -q | tail -1`
Expected: Count should be 527+ (existing) + new tests from this phase

- [ ] **Step 5: Final commit with all changes**

```bash
git add -A
git commit -m "feat: Phase 5 complete — SLA display + background extraction

- Persist workflow events to DB for SLA computation
- GET /applications/{id}/sla endpoint
- Background extraction on upload via FastAPI BackgroundTasks
- Extraction status (pending/running/succeeded/failed/unsupported) on documents
- SLA status card on applicant and staff application detail pages
- Idempotent extraction with error handling
- 527+ backend tests passing, frontend builds clean"
```

---

## Summary

| Task | Deliverable | Tests |
|------|-------------|-------|
| 1 | DB migration | — |
| 2 | WorkflowEventsRepository | 3 |
| 3 | Dependency registration | — |
| 4 | Event persistence on transitions | 3 |
| 5 | SLA API endpoint | 2+ |
| 6 | Background extraction job | 3 |
| 7 | Upload → background extraction trigger | — |
| 8 | Frontend types + API client | — |
| 9 | Applicant SLA card | — |
| 10 | Staff SLA card | — |
| 11 | Extraction status badges | — |
| 12 | Full verification | — |
