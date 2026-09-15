"""Workflow events repository — CRUD for workflow_events table."""
from __future__ import annotations

from typing import Any

from supabase import Client

from app.repositories.base import BaseRepository


class WorkflowEventsRepository(BaseRepository):
    """Repository for workflow event operations."""

    def __init__(self, client: Client):
        super().__init__(client, "workflow_events")

    def list_for_application(self, application_id: str) -> list[dict[str, Any]]:
        """List all workflow events for an application, ordered by time."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("application_id", application_id)
            .order("created_at")
            .execute()
        )
        return result.data or []
