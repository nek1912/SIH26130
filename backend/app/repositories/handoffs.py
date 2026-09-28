"""Handoffs repository — CRUD for approval_handoffs table."""

from typing import Any
from uuid import UUID

from app.repositories.base import BaseRepository


class HandoffsRepository(BaseRepository):
    """Repository for manual government handoff records."""

    def __init__(self, client):
        super().__init__(client, "approval_handoffs")

    def list_for_application(self, application_id: UUID | str) -> list[dict[str, Any]]:
        """List all handoff records for an application, oldest first."""
        return self.client.fetch_all(
            "SELECT * FROM approval_handoffs WHERE application_id = %s "
            "ORDER BY created_at",
            (str(application_id),),
        )

    def get_active_for_approval(
        self, application_id: UUID | str, approval_code: str
    ) -> dict[str, Any] | None:
        """Get the active handoff for an (application, approval), if any."""
        from app.handoff.models import ACTIVE_STATUSES

        statuses = [s.value for s in ACTIVE_STATUSES]
        placeholders = ", ".join(["%s"] * len(statuses))
        return self.client.fetch_one(
            "SELECT * FROM approval_handoffs WHERE application_id = %s "
            f"AND approval_code = %s AND status IN ({placeholders})",
            (str(application_id), approval_code, *statuses),
        )
