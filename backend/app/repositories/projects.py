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
        return self.client.fetch_all(
            "SELECT * FROM projects WHERE applicant_id = %s",
            (str(applicant_id),),
        )

    def get_with_facts(self, project_id: UUID) -> dict[str, Any] | None:
        """Get project with its facts."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        facts = self.client.fetch_one(
            "SELECT * FROM project_facts WHERE project_id = %s",
            (str(project_id),),
        )
        project["facts"] = facts
        return project
