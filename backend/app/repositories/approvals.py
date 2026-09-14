"""Approvals repository."""

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class ApprovalsRepository(BaseRepository):
    """Repository for approvals operations."""

    def __init__(self, client):
        super().__init__(client, "approvals")

    def get_active(self) -> list[dict[str, Any]]:
        """Get all active approvals."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("active", True)
            .execute()
        )
        return result.data

    def get_with_rules(self, approval_id: UUID) -> dict[str, Any] | None:
        """Get approval with its rules."""
        approval = self.get_by_id(approval_id)
        if not approval:
            return None

        rules_result = (
            self.client.table("approval_rules")
            .select("*")
            .eq("approval_id", str(approval_id))
            .execute()
        )
        approval["rules"] = rules_result.data
        return approval