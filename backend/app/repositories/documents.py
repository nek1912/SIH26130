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

    # -- Extracted Fields --

    def create_extracted_field(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create an extracted field record."""
        result = self.client.table("extracted_fields").insert(data).execute()
        return result.data[0]

    def create_extracted_fields_bulk(
        self, fields: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create multiple extracted field records in one call."""
        if not fields:
            return []
        result = self.client.table("extracted_fields").insert(fields).execute()
        return result.data or []

    def list_extracted_fields_for_document(
        self, document_id: str
    ) -> list[dict[str, Any]]:
        """List all extracted fields for a document."""
        result = (
            self.client.table("extracted_fields")
            .select("*")
            .eq("document_id", document_id)
            .order("field_name")
            .execute()
        )
        return result.data or []

    def list_extracted_fields_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all extracted fields for an application."""
        result = (
            self.client.table("extracted_fields")
            .select("*")
            .eq("application_id", application_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    def delete_extracted_fields_for_document(self, document_id: str) -> bool:
        """Delete all extracted fields for a document."""
        self.client.table("extracted_fields").delete().eq(
            "document_id", document_id
        ).execute()
        return True

    # -- Extraction Results --

    def create_extraction_result(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create an extraction result record."""
        result = self.client.table("extraction_results").insert(data).execute()
        return result.data[0]

    def get_extraction_result_for_document(
        self, document_id: str
    ) -> dict[str, Any] | None:
        """Get the extraction result for a document."""
        result = (
            self.client.table("extraction_results")
            .select("*")
            .eq("document_id", document_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def update_extraction_result(
        self, document_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update an extraction result."""
        result = (
            self.client.table("extraction_results")
            .update(data)
            .eq("document_id", document_id)
            .execute()
        )
        return result.data[0] if result.data else None

    # -- Validation Findings --

    def create_validation_finding(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a validation finding record."""
        result = self.client.table("validation_findings").insert(data).execute()
        return result.data[0]

    def create_validation_findings_bulk(
        self, findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create multiple validation finding records in one call."""
        if not findings:
            return []
        result = self.client.table("validation_findings").insert(findings).execute()
        return result.data or []

    def list_validation_findings_for_document(
        self, document_id: str
    ) -> list[dict[str, Any]]:
        """List all validation findings for a document."""
        result = (
            self.client.table("validation_findings")
            .select("*")
            .eq("document_id", document_id)
            .order("rule_id")
            .execute()
        )
        return result.data or []

    def list_validation_findings_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all validation findings for an application."""
        result = (
            self.client.table("validation_findings")
            .select("*")
            .eq("application_id", application_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    def delete_validation_findings_for_document(self, document_id: str) -> bool:
        """Delete all validation findings for a document."""
        self.client.table("validation_findings").delete().eq(
            "document_id", document_id
        ).execute()
        return True

    # -- Validation Results --

    def create_validation_result(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a validation result record."""
        result = self.client.table("validation_results").insert(data).execute()
        return result.data[0]

    def get_validation_result_for_document(
        self, document_id: str
    ) -> dict[str, Any] | None:
        """Get the validation result for a document."""
        result = (
            self.client.table("validation_results")
            .select("*")
            .eq("document_id", document_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def update_validation_result(
        self, document_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a validation result."""
        result = (
            self.client.table("validation_results")
            .update(data)
            .eq("document_id", document_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def delete_validation_results_for_document(self, document_id: str) -> bool:
        """Delete all validation results for a document."""
        self.client.table("validation_results").delete().eq(
            "document_id", document_id
        ).execute()
        return True

    # -- Requirement Status Updates --

    def update_requirement_extraction_status(
        self,
        application_id: str,
        requirement_key: str,
        extraction_status: str,
    ) -> dict[str, Any] | None:
        """Update extraction status for a document requirement."""
        result = (
            self.client.table("document_requirements")
            .update({"extraction_status": extraction_status})
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None

    def update_requirement_validation_outcome(
        self,
        application_id: str,
        requirement_key: str,
        validation_outcome: str,
    ) -> dict[str, Any] | None:
        """Update validation outcome for a document requirement."""
        result = (
            self.client.table("document_requirements")
            .update({"validation_outcome": validation_outcome})
            .eq("application_id", application_id)
            .eq("requirement_key", requirement_key)
            .execute()
        )
        return result.data[0] if result.data else None
