"""Base repository with common database operations (local PostgreSQL)."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from app.db.postgres import PostgresDB

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, client: PostgresDB, table_name: str):
        self.client = client
        self.table_name = table_name

    def get_by_id(self, id: UUID) -> dict[str, Any] | None:
        """Get a record by ID."""
        return self.client.fetch_one(
            f"SELECT * FROM {self.table_name} WHERE id = %s", (str(id),)
        )

    def get_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Get all records with pagination."""
        return self.client.fetch_all(
            f"SELECT * FROM {self.table_name} LIMIT %s OFFSET %s", (limit, offset)
        )

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record."""
        return self.client.insert_one(self.table_name, data)

    def update(self, id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        """Update a record by ID."""
        rows = self.client.update_where(
            self.table_name, data, "id = %s", (str(id),)
        )
        return rows[0] if rows else None  # type: ignore[return-value]

    def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        self.client.delete_where(self.table_name, "id = %s", (str(id),))
        return True
