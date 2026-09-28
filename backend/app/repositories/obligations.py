"""Obligations repository."""

from typing import Any

from app.repositories.base import BaseRepository


class ObligationsRepository(BaseRepository):
    """Repository for obligations operations."""

    def __init__(self, client):
        super().__init__(client, "obligations")

    def get_all_active(self) -> list[dict[str, Any]]:
        """Get all obligations."""
        return self.client.fetch_all("SELECT * FROM obligations")

    def get_by_canonical_id(self, canonical_id: str) -> dict[str, Any] | None:
        """Get obligation by canonical ID."""
        return self.client.fetch_one(
            "SELECT * FROM obligations WHERE canonical_id = %s", (canonical_id,)
        )
