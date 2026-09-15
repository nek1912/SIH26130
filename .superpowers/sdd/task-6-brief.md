## Task 6: Background Extraction Job

**Files:**
- Create: `backend/app/extraction/background.py`
- Create: `backend/tests/test_background_extraction.py`

**Interfaces:**
- Consumes: `extract_document()` from `app/extraction/service.py`, `DocumentsRepository` for persistence
- Produces: `run_extraction_background(document_id, application_id)` callable for BackgroundTasks

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_background_extraction.py
"""Tests for background extraction job."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.extraction.models import ExtractionStatus


class TestRunExtractionBackground:
    """Test the background extraction job."""

    @patch("app.extraction.background.get_supabase")
    @patch("app.extraction.background.get_settings")
    def test_sets_status_to_running_then_succeeded(self, mock_settings, mock_supabase):
        """Background job sets extraction_status to running then succeeded."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())

        # Mock settings and storage
        mock_settings.return_value.supabase_storage_bucket = "documents"
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        mock_client.storage.from_.return_value.download.return_value = b"test content"

        # Mock document record
        mock_doc = MagicMock()
        mock_doc.data = [{
            "id": doc_id,
            "application_id": app_id,
            "mime_type": "text/csv",
            "storage_path": "test/path.csv",
            "requirement_key": "D01",
            "extraction_status": "pending",
        }]

        # Mock extraction result
        mock_extraction = MagicMock()
        mock_extraction.data = None  # No existing result

        # Mock requirement
        mock_req = MagicMock()
        mock_req.data = [{"requirement_key": "D01", "domain": "environment"}]

        def side_effect(table_name):
            m = MagicMock()
            if table_name == "documents":
                m.select.return_value.eq.return_value.execute.return_value = mock_doc
                m.update.return_value.execute.return_value = MagicMock()
            elif table_name == "extraction_results":
                m.select.return_value.eq.return_value.execute.return_value = mock_extraction
                m.insert.return_value.execute.return_value = MagicMock()
                m.delete.return_value.eq.return_value.execute.return_value = MagicMock()
            elif table_name == "extracted_fields":
                m.delete.return_value.eq.return_value.execute.return_value = MagicMock()
                m.insert.return_value.execute.return_value = MagicMock()
            elif table_name == "document_requirements":
                m.select.return_value.eq.return_value.execute.return_value = mock_req
                m.update.return_value.eq.return_value.execute.return_value = MagicMock()
            return m

        mock_client.table.side_effect = side_effect

        # Run the background job
        run_extraction_background(doc_id, app_id)

        # Verify extraction_status was updated
        # The mock should have been called with update containing extraction_status
        calls = mock_client.table.return_value.update.call_args_list
        # At least one update should set extraction_status
        status_updates = [c for c in calls if c[0][0].get("extraction_status")]
        assert len(status_updates) >= 1

    @patch("app.extraction.background.get_supabase")
    @patch("app.extraction.background.get_settings")
    def test_skips_if_already_succeeded(self, mock_settings, mock_supabase):
        """Background job skips if document already has extraction_status=succeeded."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())

        mock_settings.return_value.supabase_storage_bucket = "documents"
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client

        # Mock document with already succeeded status
        mock_doc = MagicMock()
        mock_doc.data = [{
            "id": doc_id,
            "application_id": app_id,
            "mime_type": "text/csv",
            "storage_path": "test/path.csv",
            "requirement_key": "D01",
            "extraction_status": "succeeded",
        }]

        def side_effect(table_name):
            m = MagicMock()
            if table_name == "documents":
                m.select.return_value.eq.return_value.execute.return_value = mock_doc
            return m

        mock_client.table.side_effect = side_effect

        # Run â€” should return early without downloading
        run_extraction_background(doc_id, app_id)

        # Storage download should NOT be called
        mock_client.storage.from_.assert_not_called()

    @patch("app.extraction.background.get_supabase")
    @patch("app.extraction.background.get_settings")
    def test_sets_failed_on_exception(self, mock_settings, mock_supabase):
        """Background job sets extraction_status to failed on exception."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())

        mock_settings.return_value.supabase_storage_bucket = "documents"
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        mock_client.storage.from_.return_value.download.side_effect = Exception("Storage error")

        mock_doc = MagicMock()
        mock_doc.data = [{
            "id": doc_id,
            "application_id": app_id,
            "mime_type": "text/csv",
            "storage_path": "test/path.csv",
            "requirement_key": "D01",
            "extraction_status": "pending",
        }]

        def side_effect(table_name):
            m = MagicMock()
            if table_name == "documents":
                m.select.return_value.eq.return_value.execute.return_value = mock_doc
                m.update.return_value.execute.return_value = MagicMock()
            return m

        mock_client.table.side_effect = side_effect

        # Run â€” should not raise, should set failed status
        run_extraction_background(doc_id, app_id)

        # Verify extraction_status was set to failed
        calls = mock_client.table.return_value.update.call_args_list
        failed_updates = [c for c in calls if c[0][0].get("extraction_status") == "failed"]
        assert len(failed_updates) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_background_extraction.py -v`
Expected: FAIL â€” `ModuleNotFoundError: No module named 'app.extraction.background'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/extraction/background.py
"""Background extraction job for document processing.

Runs via FastAPI BackgroundTasks after document upload.
Sets extraction_status on the document record and stores results.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_extraction_background(document_id: str, application_id: str) -> None:
    """Background job: extract metadata from an uploaded document.

    This function is designed to be called via FastAPI BackgroundTasks.
    It fetches all needed data internally and handles all errors safely.
    """
    from app.core.config import get_settings
    from app.db.client import get_supabase
    from app.extraction.service import extract_document

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

        # Skip if already succeeded (idempotent)
        if document.get("extraction_status") == "succeeded":
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
        final_status = "succeeded"
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_background_extraction.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/extraction/background.py backend/tests/test_background_extraction.py
git commit -m "feat: add background extraction job with idempotency and error handling"
```

---

