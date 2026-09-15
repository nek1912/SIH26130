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
