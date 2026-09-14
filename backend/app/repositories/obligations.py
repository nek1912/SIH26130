"""Obligations repository."""

from typing import Any

from app.repositories.base import BaseRepository


class ObligationsRepository(BaseRepository):
    """Repository for obligations operations."""

    def __init__(self, client):
        super().__init__(client, "obligations")

    def get_all_active(self) -> list[dict[str, Any]]:
        """Get all obligations."""
        result = self.client.table(self.table_name).select("*").execute()
        return result.data

    def get_by_canonical_id(self, canonical_id: str) -> dict[str, Any] | None:
        """Get obligation by canonical ID."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("canonical_id", canonical_id)
            .execute()
        )
        return result.data[0] if result.data else None