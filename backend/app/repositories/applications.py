"""Applications repository."""

import uuid
from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class ApplicationsRepository(BaseRepository):
    """Repository for applications operations."""

    def __init__(self, client):
        super().__init__(client, "applications")

    def get_by_project(self, project_id: UUID) -> list[dict[str, Any]]:
        """Get all applications for a project."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("project_id", str(project_id))
            .execute()
        )
        return result.data

    def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get applications by status."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("status", status)
            .execute()
        )
        return result.data

    def list_all_with_filters(
        self,
        *,
        status: list[str] | None = None,
        assigned_to: str | None = None,
        applicant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """List applications with optional filters and pagination.

        Returns (items, total_count).
        """
        query = self.client.table(self.table_name).select("*", count="exact")

        if status:
            query = query.in_("status", status)
        if assigned_to:
            query = query.eq("assigned_officer_id", assigned_to)
        if applicant_id:
            query = query.eq("applicant_id", applicant_id)

        offset = (page - 1) * page_size
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

        result = query.execute()
        items = result.data or []
        total = result.count if result.count is not None else len(items)
        return items, total

    def get_approval_stages(self, approval_id: str) -> list[dict[str, Any]] | None:
        """Load workflow stages from the approval's workflow_definition."""
        result = (
            self.client.table("approvals")
            .select("workflow_definition")
            .eq("id", approval_id)
            .execute()
        )
        if not result.data:
            return None
        wf_def = result.data[0].get("workflow_definition")
        if not wf_def:
            return None
        return wf_def.get("stages", [])

    def create_with_reference(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create application with auto-generated reference number."""
        data["reference_number"] = f"APP-{uuid.uuid4().hex[:8].upper()}"
        return self.create(data)