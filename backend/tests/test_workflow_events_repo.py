"""Tests for workflow events repository."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4


class TestWorkflowEventsRepository:
    """Test workflow events repository operations."""

    def _make_repo(self):
        """Create a repository with a mocked PostgresDB handle."""
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

        client.insert_one.return_value = {"id": str(uuid4()), **event_data}

        result = repo.create(event_data)

        assert client.insert_one.call_args[0][0] == "workflow_events"
        assert result["to_status"] == "submitted"
        assert result["action"] == "submit"

    def test_list_for_application_ordered_by_time(self):
        """Events for an application are returned ordered by created_at."""
        repo, client = self._make_repo()
        app_id = str(uuid4())

        client.fetch_all.return_value = [
            {
                "id": "1",
                "application_id": app_id,
                "action": "submit",
                "created_at": "2026-09-10T10:00:00",
            },
            {
                "id": "2",
                "application_id": app_id,
                "action": "advance",
                "created_at": "2026-09-11T10:00:00",
            },
        ]

        events = repo.list_for_application(app_id)

        sql = client.fetch_all.call_args[0][0]
        assert "ORDER BY created_at" in sql
        assert len(events) == 2
        assert events[0]["action"] == "submit"

    def test_list_for_application_empty(self):
        """Empty result returns empty list."""
        repo, client = self._make_repo()
        app_id = str(uuid4())

        client.fetch_all.return_value = []

        events = repo.list_for_application(app_id)
        assert events == []
