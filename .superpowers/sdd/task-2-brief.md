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
Expected: FAIL â€” `ModuleNotFoundError: No module named 'app.repositories.workflow_events'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/repositories/workflow_events.py
"""Workflow events repository â€” CRUD for workflow_events table."""
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

