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
        return self.client.fetch_one(
            "SELECT * FROM project_facts WHERE project_id = %s",
            (str(project_id),),
        )

    def upsert(self, project_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update facts for a project."""
        payload = dict(data)
        payload["project_id"] = str(project_id)
        return self.client.upsert_one(
            self.table_name, payload, conflict_columns=["project_id"]
        )
