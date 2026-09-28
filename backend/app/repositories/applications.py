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
        return self.client.fetch_all(
            "SELECT * FROM applications WHERE project_id = %s",
            (str(project_id),),
        )

    def get_by_status(self, status: str) -> list[dict[str, Any]]:
        """Get applications by status."""
        return self.client.fetch_all(
            "SELECT * FROM applications WHERE status = %s", (status,)
        )

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
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            placeholders = ", ".join(["%s"] * len(status))
            clauses.append(f"status IN ({placeholders})")
            params.extend(status)
        if assigned_to:
            clauses.append("assigned_officer_id = %s")
            params.append(assigned_to)
        if applicant_id:
            clauses.append("applicant_id = %s")
            params.append(applicant_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        total_row = self.client.fetch_one(
            f"SELECT COUNT(*) AS n FROM applications {where}", tuple(params)
        )
        total = int(total_row["n"]) if total_row else 0

        offset = (page - 1) * page_size
        items = self.client.fetch_all(
            f"SELECT * FROM applications {where} "
            "ORDER BY created_at DESC LIMIT %s OFFSET %s",
            tuple(params) + (page_size, offset),
        )
        return items, total

    def get_approval_stages(self, approval_id: str) -> list[dict[str, Any]] | None:
        """Load workflow stages from the approval's workflow_definition."""
        row = self.client.fetch_one(
            "SELECT workflow_definition FROM approvals WHERE id = %s",
            (approval_id,),
        )
        if not row:
            return None
        wf_def = row.get("workflow_definition")
        if not wf_def:
            return None
        return wf_def.get("stages", [])

    def create_with_reference(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create application with auto-generated reference number."""
        data["reference_number"] = f"APP-{uuid.uuid4().hex[:8].upper()}"
        return self.create(data)
