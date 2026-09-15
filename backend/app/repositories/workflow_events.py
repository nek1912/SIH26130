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
