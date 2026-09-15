"""Background extraction job for document processing.

Runs via FastAPI BackgroundTasks after document upload.
Sets extraction_status on the document record and stores results.
"""
from __future__ import annotations

import logging

from app.core.config import get_settings
from app.db.client import get_supabase
from app.extraction.service import extract_document

logger = logging.getLogger(__name__)


def run_extraction_background(document_id: str, application_id: str) -> None:
    """Background job: extract metadata from an uploaded document.

    This function is designed to be called via FastAPI BackgroundTasks.
    It fetches all needed data internally and handles all errors safely.
    """
    client = get_supabase()
    settings = get_settings()

    try:
        # Load document record
        doc_result = (
            client.table("documents")
            .select("*")
            .eq("id", document_id)
            .execute()
        )
        document = doc_result.data[0] if doc_result.data else None

        if not document:
            logger.warning("Document %s not found, skipping extraction", document_id)
            return

        # Skip if already completed (idempotent)
        if document.get("extraction_status") == "completed":
            logger.info("Document %s already extracted, skipping", document_id)
            return

        # Set status to running
        client.table("documents").update(
            {"extraction_status": "running"}
        ).eq("id", document_id).execute()

        # Download file from storage
        storage_path = document.get("storage_path", "")
        try:
            file_data = client.storage.from_(
                settings.supabase_storage_bucket
            ).download(storage_path)
        except Exception as e:
            logger.warning("Failed to download document %s: %s", document_id, e)
            _set_failed(client, document_id, f"Storage download failed: {type(e).__name__}")
            return

        # Perform extraction
        mime_type = document.get("mime_type", "application/octet-stream")
        extraction_result = extract_document(
            content=file_data,
            mime_type=mime_type,
            document_id=document_id,
            application_id=application_id,
        )

        # Delete existing extraction data (idempotent)
        client.table("extracted_fields").delete().eq(
            "document_id", document_id
        ).execute()

        # Store extraction result
        extraction_data = {
            "document_id": document_id,
            "application_id": application_id,
            "status": extraction_result.status.value,
            "errors": extraction_result.errors,
            "metadata": extraction_result.metadata,
        }

        existing = (
            client.table("extraction_results")
            .select("id")
            .eq("document_id", document_id)
            .execute()
        )
        if existing.data:
            client.table("extraction_results").update(extraction_data).eq(
                "document_id", document_id
            ).execute()
        else:
            client.table("extraction_results").insert(extraction_data).execute()

        # Store extracted fields
        if extraction_result.fields:
            fields_data = []
            for field in extraction_result.fields:
                fields_data.append({
                    "document_id": document_id,
                    "application_id": application_id,
                    "field_name": field.field_name,
                    "field_value": field.field_value,
                    "field_type": field.field_type,
                    "extraction_method": field.extraction_method,
                    "confidence": field.confidence,
                    "metadata": field.metadata,
                })
            client.table("extracted_fields").insert(fields_data).execute()

        # Update requirement extraction status
        requirement_key = document.get("requirement_key")
        if requirement_key:
            client.table("document_requirements").update(
                {"extraction_status": extraction_result.status.value}
            ).eq("application_id", application_id).eq(
                "requirement_key", requirement_key
            ).execute()

        # Set final status
        final_status = "completed"
        if extraction_result.status.value in ("failed", "unsupported"):
            final_status = extraction_result.status.value

        client.table("documents").update(
            {"extraction_status": final_status}
        ).eq("id", document_id).execute()

        logger.info(
            "Extraction completed for document %s: %s",
            document_id,
            final_status,
        )

    except Exception as e:
        logger.error("Background extraction failed for %s: %s", document_id, e)
        _set_failed(client, document_id, f"Extraction failed: {type(e).__name__}")


def _set_failed(client, document_id: str, error_msg: str) -> None:
    """Safely set extraction_status to failed."""
    try:
        client.table("documents").update(
            {"extraction_status": "failed"}
        ).eq("id", document_id).execute()
    except Exception:
        logger.error("Could not update extraction_status for %s", document_id)
