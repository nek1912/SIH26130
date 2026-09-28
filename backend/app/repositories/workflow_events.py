"""Workflow events repository — CRUD for workflow_events table."""
from __future__ import annotations

from typing import Any

from app.db.postgres import PostgresDB
from app.repositories.base import BaseRepository


class WorkflowEventsRepository(BaseRepository):
    """Repository for workflow event operations."""

    def __init__(self, client: PostgresDB):
        super().__init__(client, "workflow_events")

    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        """List all workflow events for an application, ordered by time."""
        return self.client.fetch_all(
            "SELECT * FROM workflow_events WHERE application_id = %s "
            "ORDER BY created_at",
            (application_id,),
        )
