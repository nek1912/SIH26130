"""Background extraction job for document processing.

Runs via FastAPI BackgroundTasks after document upload.
Sets extraction_status on the document record and stores results.
Uses DocumentsRepository + the storage adapter boundary (local
filesystem for development); no Supabase dependency.
"""
from __future__ import annotations

import logging

from app.db.client import get_db
from app.extraction.service import extract_document
from app.repositories.documents import DocumentsRepository
from app.storage import DocumentStorage, get_storage

logger = logging.getLogger(__name__)


def run_extraction_background(
    document_id: str,
    application_id: str,
    repo: DocumentsRepository | None = None,
    storage: DocumentStorage | None = None,
) -> None:
    """Background job: extract metadata from an uploaded document.

    This function is designed to be called via FastAPI BackgroundTasks.
    It fetches all needed data internally and handles all errors safely.
    """
    repo = repo or DocumentsRepository(get_db())
    storage = storage or get_storage()

    try:
        document = repo.get_document(document_id)

        if not document:
            logger.warning("Document %s not found, skipping extraction", document_id)
            return

        # Skip if already completed (idempotent)
        if document.get("extraction_status") == "completed":
            logger.info("Document %s already extracted, skipping", document_id)
            return

        # Set status to running
        repo.set_document_extraction_status(document_id, "running")

        # Download file from storage
        storage_path = document.get("storage_path", "")
        try:
            file_data = storage.read(storage_path)
        except Exception as e:
            logger.warning("Failed to download document %s: %s", document_id, e)
            _set_failed(repo, document_id, f"Storage download failed: {type(e).__name__}")
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
        repo.delete_extracted_fields_for_document(document_id)

        # Store extraction result
        extraction_data = {
            "document_id": document_id,
            "application_id": application_id,
            "status": extraction_result.status.value,
            "errors": extraction_result.errors,
            "metadata": extraction_result.metadata,
        }

        existing = repo.get_extraction_result_for_document(document_id)
        if existing:
            repo.update_extraction_result(document_id, extraction_data)
        else:
            repo.create_extraction_result(extraction_data)

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
            repo.create_extracted_fields_bulk(fields_data)

        # Update requirement extraction status
        requirement_key = document.get("requirement_key")
        if requirement_key:
            repo.update_requirement_extraction_status(
                application_id,
                requirement_key,
                extraction_result.status.value,
            )

        # Set final status
        final_status = "completed"
        if extraction_result.status.value in ("failed", "unsupported"):
            final_status = extraction_result.status.value

        repo.set_document_extraction_status(document_id, final_status)

        logger.info(
            "Extraction completed for document %s: %s",
            document_id,
            final_status,
        )

    except Exception as e:
        logger.error("Background extraction failed for %s: %s", document_id, e)
        _set_failed(repo, document_id, f"Extraction failed: {type(e).__name__}")


def _set_failed(
    repo: DocumentsRepository, document_id: str, error_msg: str
) -> None:
    """Safely set extraction_status to failed."""
    try:
        repo.set_document_extraction_status(document_id, "failed")
    except Exception:
        logger.error("Could not update extraction_status for %s", document_id)
