"""Tests for background extraction job."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4


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

        # Track mocks per table so we can assert on them
        table_mocks: dict[str, MagicMock] = {}

        def side_effect(table_name):
            m = MagicMock()
            table_mocks[table_name] = m
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

        # Verify extraction_status was updated to "succeeded"
        doc_mock = table_mocks["documents"]
        calls = doc_mock.update.call_args_list
        status_updates = [c for c in calls if c[0][0].get("extraction_status") == "succeeded"]
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

        # Run — should return early without downloading
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

        table_mocks: dict[str, MagicMock] = {}

        def side_effect(table_name):
            m = MagicMock()
            table_mocks[table_name] = m
            if table_name == "documents":
                m.select.return_value.eq.return_value.execute.return_value = mock_doc
                m.update.return_value.execute.return_value = MagicMock()
            return m

        mock_client.table.side_effect = side_effect

        # Run — should not raise, should set failed status
        run_extraction_background(doc_id, app_id)

        # Verify extraction_status was set to failed
        doc_mock = table_mocks["documents"]
        calls = doc_mock.update.call_args_list
        failed_updates = [c for c in calls if c[0][0].get("extraction_status") == "failed"]
        assert len(failed_updates) >= 1
