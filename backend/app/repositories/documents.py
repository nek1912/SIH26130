"""Documents repository — CRUD for document_requirements and documents tables."""
from __future__ import annotations

from typing import Any

from app.repositories.base import BaseRepository


class DocumentsRepository(BaseRepository):
    """Repository for document operations."""

    def __init__(self, client):
        super().__init__(client, "documents")

    # -- Document Requirements --

    def list_requirements_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all document requirements for an application."""
        result = (
            self.client.table("document_requirements")
            .select("*")
            .eq("application_id", application_id)
            .order("requirement_key")
            .execute()
        )
        return result.data or []

    def get_requirement(
        self, application_id: str, requirement_key: str
    ) -> dict[str, Any] | None:
        """Get a specific document requirement by application + key."""
        result = (
            self.client.table("document_requirements")
            .select("*")
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_requirement(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a document requirement record."""
        result = (
            self.client.table("document_requirements").insert(data).execute()
        )
        return result.data[0]

    def create_requirements_bulk(
        self, requirements: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create multiple document requirements in one call."""
        if not requirements:
            return []
        result = (
            self.client.table("document_requirements")
            .insert(requirements)
            .execute()
        )
        return result.data or []

    def update_requirement_readiness(
        self,
        application_id: str,
        requirement_key: str,
        readiness: str,
        uploaded_document_id: str | None = None,
        rejection_reason: str | None = None,
    ) -> dict[str, Any] | None:
        """Update readiness status for a document requirement."""
        update_data: dict[str, Any] = {"readiness": readiness}
        if uploaded_document_id is not None:
            update_data["uploaded_document_id"] = uploaded_document_id
        if rejection_reason is not None:
            update_data["rejection_reason"] = rejection_reason

        result = (
            self.client.table("document_requirements")
            .update(update_data)
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None

    # -- Uploaded Documents --

    def list_documents_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all uploaded documents for an application."""
        result = (
            self.client.table("documents")
            .select("*")
            .eq("application_id", application_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        """Get a document by ID."""
        result = (
            self.client.table("documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def create_document(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a document record."""
        result = self.client.table("documents").insert(data).execute()
        return result.data[0]

    def delete_document(self, document_id: str) -> bool:
        """Delete a document record."""
        self.client.table("documents").delete().eq("id", document_id).execute()
        return True

    def get_document_by_requirement(
        self, application_id: str, requirement_key: str
    ) -> dict[str, Any] | None:
        """Get the uploaded document for a specific requirement."""
        result = (
            self.client.table("documents")
            .select("*")
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None
