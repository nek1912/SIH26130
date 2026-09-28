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
        return self.client.fetch_all(
            "SELECT * FROM approvals WHERE active = %s", (True,)
        )

    def get_by_code(self, code: str) -> dict[str, Any] | None:
        """Get an approval by its canonical workbook code (e.g. 'A04').

        Codes are stable machine identities (migration 008); UUIDs remain
        persistence identifiers. Returns None when no row carries the code.
        """
        return self.client.fetch_one(
            "SELECT * FROM approvals WHERE code = %s", (code,)
        )

    def get_with_rules(self, approval_id: UUID) -> dict[str, Any] | None:
        """Get approval with its rules."""
        approval = self.get_by_id(approval_id)
        if not approval:
            return None

        approval["rules"] = self.client.fetch_all(
            "SELECT * FROM approval_rules WHERE approval_id = %s",
            (str(approval_id),),
        )
        return approval

    def get_rules_for_approval(self, approval_id: UUID) -> list[dict[str, Any]]:
        """Get all active rules for an approval."""
        return self.client.fetch_all(
            "SELECT * FROM approval_rules WHERE approval_id = %s AND active = %s",
            (str(approval_id), True),
        )
