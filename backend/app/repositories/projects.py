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