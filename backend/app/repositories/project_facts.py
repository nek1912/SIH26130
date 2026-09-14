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
        result = self.client.table(self.table_name).upsert(data).execute()
        return result.data[0]