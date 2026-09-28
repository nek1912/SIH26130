"""Documents repository — CRUD for document_requirements and documents tables."""
from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from app.repositories.base import BaseRepository


def _jsonb_lists(data: dict[str, Any]) -> dict[str, Any]:
    """Wrap known jsonb-list fields (accepted_mime_types) explicitly."""
    out = dict(data)
    if isinstance(out.get("accepted_mime_types"), list):
        out["accepted_mime_types"] = Jsonb(out["accepted_mime_types"])
    return out


def _jsonb_any_lists(data: dict[str, Any]) -> dict[str, Any]:
    """Wrap every list value as jsonb.

    Used only for extraction/validation tables, whose list-receiving
    columns (errors, source_refs, field_value, findings payloads) are
    all jsonb — there are no text[] columns in these tables.
    """
    return {
        key: (Jsonb(value) if isinstance(value, list) else value)
        for key, value in data.items()
    }


class DocumentsRepository(BaseRepository):
    """Repository for document operations."""

    def __init__(self, client):
        super().__init__(client, "documents")

    # -- Document Requirements --

    def list_requirements_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all document requirements for an application."""
        return self.client.fetch_all(
            "SELECT * FROM document_requirements WHERE application_id = %s "
            "ORDER BY requirement_key",
            (application_id,),
        )

    def get_requirement(
        self, application_id: str, requirement_key: str
    ) -> dict[str, Any] | None:
        """Get a specific document requirement by application + key."""
        return self.client.fetch_one(
            "SELECT * FROM document_requirements WHERE application_id = %s "
            "AND requirement_key = %s",
            (application_id, requirement_key),
        )

    def create_requirement(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a document requirement record."""
        return self.client.insert_one("document_requirements", _jsonb_lists(data))

    def create_requirements_bulk(
        self, requirements: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create multiple document requirements in one call."""
        if not requirements:
            return []
        return self.client.insert_many(
            "document_requirements", [_jsonb_lists(r) for r in requirements]
        )

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

        rows = self.client.update_where(
            "document_requirements",
            update_data,
            "application_id = %s AND requirement_key = %s",
            (application_id, requirement_key),
        )
        return rows[0] if rows else None

    def list_documents_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all uploaded documents for an application."""
        return self.client.fetch_all(
            "SELECT * FROM documents WHERE application_id = %s "
            "ORDER BY created_at DESC",
            (application_id,),
        )

    # -- Uploaded Documents --

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        """Get a document by ID."""
        return self.client.fetch_one(
            "SELECT * FROM documents WHERE id = %s", (document_id,)
        )

    def create_document(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a document record."""
        return self.client.insert_one("documents", data)

    def delete_document(self, document_id: str) -> bool:
        """Delete a document record."""
        self.client.delete_where("documents", "id = %s", (document_id,))
        return True

    def get_document_by_requirement(
        self, application_id: str, requirement_key: str
    ) -> dict[str, Any] | None:
        """Get the uploaded document for a specific requirement."""
        return self.client.fetch_one(
            "SELECT * FROM documents WHERE application_id = %s "
            "AND requirement_key = %s",
            (application_id, requirement_key),
        )

    def set_document_extraction_status(
        self, document_id: str, extraction_status: str
    ) -> dict[str, Any] | None:
        """Set extraction_status on a document record."""
        rows = self.client.update_where(
            "documents",
            {"extraction_status": extraction_status},
            "id = %s",
            (document_id,),
        )
        return rows[0] if rows else None

    # -- Extracted Fields --

    def create_extracted_field(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create an extracted field record."""
        return self.client.insert_one("extracted_fields", _jsonb_any_lists(data))

    def create_extracted_fields_bulk(
        self, fields: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create multiple extracted field records in one call."""
        if not fields:
            return []
        return self.client.insert_many("extracted_fields", [_jsonb_any_lists(r) for r in fields])

    def list_extracted_fields_for_document(
        self, document_id: str
    ) -> list[dict[str, Any]]:
        """List all extracted fields for a document."""
        return self.client.fetch_all(
            "SELECT * FROM extracted_fields WHERE document_id = %s "
            "ORDER BY field_name",
            (document_id,),
        )

    def list_extracted_fields_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all extracted fields for an application."""
        return self.client.fetch_all(
            "SELECT * FROM extracted_fields WHERE application_id = %s "
            "ORDER BY created_at DESC",
            (application_id,),
        )

    def delete_extracted_fields_for_document(self, document_id: str) -> bool:
        """Delete all extracted fields for a document."""
        self.client.delete_where(
            "extracted_fields", "document_id = %s", (document_id,)
        )
        return True

    # -- Extraction Results --

    def create_extraction_result(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create an extraction result record."""
        return self.client.insert_one("extraction_results", _jsonb_any_lists(data))

    def get_extraction_result_for_document(
        self, document_id: str
    ) -> dict[str, Any] | None:
        """Get the extraction result for a document."""
        return self.client.fetch_one(
            "SELECT * FROM extraction_results WHERE document_id = %s",
            (document_id,),
        )

    def update_extraction_result(
        self, document_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update an extraction result."""
        rows = self.client.update_where(
            "extraction_results",
            _jsonb_any_lists(data),
            "document_id = %s",
            (document_id,),
        )
        return rows[0] if rows else None

    # -- Validation Findings --

    def create_validation_finding(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a validation finding record."""
        return self.client.insert_one("validation_findings", _jsonb_any_lists(data))

    def create_validation_findings_bulk(
        self, findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create multiple validation finding records in one call."""
        if not findings:
            return []
        return self.client.insert_many(
            "validation_findings", [_jsonb_any_lists(r) for r in findings]
        )

    def list_validation_findings_for_document(
        self, document_id: str
    ) -> list[dict[str, Any]]:
        """List all validation findings for a document."""
        return self.client.fetch_all(
            "SELECT * FROM validation_findings WHERE document_id = %s "
            "ORDER BY rule_id",
            (document_id,),
        )

    def list_validation_findings_for_application(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """List all validation findings for an application."""
        return self.client.fetch_all(
            "SELECT * FROM validation_findings WHERE application_id = %s "
            "ORDER BY created_at DESC",
            (application_id,),
        )

    def delete_validation_findings_for_document(self, document_id: str) -> bool:
        """Delete all validation findings for a document."""
        self.client.delete_where(
            "validation_findings", "document_id = %s", (document_id,)
        )
        return True

    # -- Validation Results --

    def create_validation_result(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a validation result record."""
        return self.client.insert_one("validation_results", _jsonb_any_lists(data))

    def get_validation_result_for_document(
        self, document_id: str
    ) -> dict[str, Any] | None:
        """Get the validation result for a document."""
        return self.client.fetch_one(
            "SELECT * FROM validation_results WHERE document_id = %s",
            (document_id,),
        )

    def update_validation_result(
        self, document_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a validation result."""
        rows = self.client.update_where(
            "validation_results",
            _jsonb_any_lists(data),
            "document_id = %s",
            (document_id,),
        )
        return rows[0] if rows else None

    def delete_validation_results_for_document(self, document_id: str) -> bool:
        """Delete all validation results for a document."""
        self.client.delete_where(
            "validation_results", "document_id = %s", (document_id,)
        )
        return True

    # -- Requirement Status Updates --

    def update_requirement_extraction_status(
        self,
        application_id: str,
        requirement_key: str,
        extraction_status: str,
    ) -> dict[str, Any] | None:
        """Update extraction status for a document requirement."""
        rows = self.client.update_where(
            "document_requirements",
            {"extraction_status": extraction_status},
            "application_id = %s AND requirement_key = %s",
            (application_id, requirement_key),
        )
        return rows[0] if rows else None

    def update_requirement_validation_outcome(
        self, application_id: str,
        requirement_key: str,
        validation_outcome: str,
    ) -> dict[str, Any] | None:
        """Update validation outcome for a document requirement."""
        rows = self.client.update_where(
            "document_requirements",
            {"validation_outcome": validation_outcome},
            "application_id = %s AND requirement_key = %s",
            (application_id, requirement_key),
        )
        return rows[0] if rows else None
