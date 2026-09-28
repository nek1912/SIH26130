"""Tests for background extraction job (repository + storage seam)."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from app.repositories.documents import DocumentsRepository


def _make_repo(doc):
    repo = MagicMock(spec=DocumentsRepository)
    repo.get_document.return_value = doc
    repo.get_extraction_result_for_document.return_value = None
    return repo


def _make_storage(content: bytes | Exception = b"a,b\n1,2\n"):
    storage = MagicMock()
    if isinstance(content, Exception):
        storage.read.side_effect = content
    else:
        storage.read.return_value = content
    return storage


def _doc(doc_id, app_id, **over):
    row = {
        "id": doc_id,
        "application_id": app_id,
        "mime_type": "text/csv",
        "storage_path": "test/path.csv",
        "requirement_key": "D01",
        "extraction_status": "pending",
    }
    row.update(over)
    return row


class TestRunExtractionBackground:
    """Test the background extraction job."""

    def test_sets_status_to_running_then_completed(self):
        """Background job sets extraction_status to running then completed."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())
        repo = _make_repo(_doc(doc_id, app_id))
        storage = _make_storage()

        run_extraction_background(doc_id, app_id, repo=repo, storage=storage)

        statuses = [
            c[0][1]
            for c in repo.set_document_extraction_status.call_args_list
        ]
        assert "running" in statuses
        assert "completed" in statuses
        assert repo.create_extraction_result.called

    def test_skips_if_already_completed(self):
        """Background job skips if document already has extraction_status=completed."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())
        repo = _make_repo(_doc(doc_id, app_id, extraction_status="completed"))
        storage = _make_storage()

        run_extraction_background(doc_id, app_id, repo=repo, storage=storage)

        storage.read.assert_not_called()
        repo.set_document_extraction_status.assert_not_called()

    def test_sets_failed_on_exception(self):
        """Background job sets extraction_status to failed on exception."""
        from app.extraction.background import run_extraction_background

        doc_id = str(uuid4())
        app_id = str(uuid4())
        repo = _make_repo(_doc(doc_id, app_id))
        storage = _make_storage(Exception("Storage error"))

        run_extraction_background(doc_id, app_id, repo=repo, storage=storage)

        statuses = [
            c[0][1]
            for c in repo.set_document_extraction_status.call_args_list
        ]
        assert "failed" in statuses
