"""Base repository with common database operations."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from supabase import Client

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, client: Client, table_name: str):
        self.client = client
        self.table_name = table_name

    def get_by_id(self, id: UUID) -> dict[str, Any] | None:
        """Get a record by ID."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .eq("id", str(id))
            .execute()
        )
        return result.data[0] if result.data else None

    def get_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Get all records with pagination."""
        result = (
            self.client.table(self.table_name)
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record."""
        result = self.client.table(self.table_name).insert(data).execute()
        return result.data[0]

    def update(self, id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        """Update a record by ID."""
        result = (
            self.client.table(self.table_name)
            .update(data)
            .eq("id", str(id))
            .execute()
        )
        return result.data[0] if result.data else None

    def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        self.client.table(self.table_name).delete().eq("id", str(id)).execute()
        return True