"""Sources repository."""

from typing import Any

from app.repositories.base import BaseRepository


class SourcesRepository(BaseRepository):
    """Repository for sources operations."""

    def __init__(self, client):
        super().__init__(client, "sources")

    def get_by_jurisdiction(self, jurisdiction: str) -> list[dict[str, Any]]:
        """Get sources by jurisdiction."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("jurisdiction", jurisdiction)
            .execute()
        )
        return result.data