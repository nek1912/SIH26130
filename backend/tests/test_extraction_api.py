"""Tests for extraction/validation API endpoints."""
from __future__ import annotations


class TestExtractionEndpoints:
    def test_extract_requires_auth(self):
        """Verify extract endpoint requires authentication."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001/extract",
        )
        assert resp.status_code == 401

    def test_validate_requires_auth(self):
        """Verify validate endpoint requires authentication."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001/validate",
        )
        assert resp.status_code == 401

    def test_get_extraction_requires_auth(self):
        """Verify get extraction endpoint requires authentication."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001/extraction",
        )
        assert resp.status_code == 401

    def test_get_validation_requires_auth(self):
        """Verify get validation endpoint requires authentication."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001/validation",
        )
        assert resp.status_code == 401

    def test_get_extraction_summary_requires_auth(self):
        """Verify get extraction summary endpoint requires authentication."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/applications/00000000-0000-0000-0000-000000000001/extraction-summary",
        )
        assert resp.status_code == 401


class TestDocumentsRepositoryExtraction:
    """Tests for DocumentsRepository extraction/validation methods."""

    def test_create_extracted_field(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.insert_one.return_value = {
            "id": "field-1",
            "field_name": "page_count",
        }
        repo = DocumentsRepository(mock_client)
        result = repo.create_extracted_field(
            {"document_id": "doc-1", "field_name": "page_count", "field_value": 5}
        )
        assert result["id"] == "field-1"

    def test_list_extracted_fields_for_document(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = [
            {"id": "field-1", "field_name": "page_count"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.list_extracted_fields_for_document("doc-1")
        assert len(result) == 1

    def test_create_extraction_result(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.insert_one.return_value = {
            "id": "result-1",
            "status": "completed",
        }
        repo = DocumentsRepository(mock_client)
        result = repo.create_extraction_result(
            {"document_id": "doc-1", "status": "completed"}
        )
        assert result["id"] == "result-1"

    def test_get_extraction_result_for_document(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.fetch_one.return_value = {
            "id": "result-1",
            "status": "completed",
        }
        repo = DocumentsRepository(mock_client)
        result = repo.get_extraction_result_for_document("doc-1")
        assert result is not None
        assert result["status"] == "completed"

    def test_create_validation_result(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.insert_one.return_value = {
            "id": "val-1",
            "outcome": "VALID",
        }
        repo = DocumentsRepository(mock_client)
        result = repo.create_validation_result(
            {"document_id": "doc-1", "outcome": "VALID"}
        )
        assert result["id"] == "val-1"

    def test_list_validation_findings_for_document(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.fetch_all.return_value = [
            {"id": "finding-1", "rule_id": "LAND-001"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.list_validation_findings_for_document("doc-1")
        assert len(result) == 1

    def test_update_requirement_extraction_status(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.update_where.return_value = [
            {"id": "req-1", "extraction_status": "completed"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.update_requirement_extraction_status("app-1", "D01", "completed")
        assert result["extraction_status"] == "completed"

    def test_update_requirement_validation_outcome(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.update_where.return_value = [
            {"id": "req-1", "validation_outcome": "VALID"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.update_requirement_validation_outcome("app-1", "D01", "VALID")
        assert result["validation_outcome"] == "VALID"
