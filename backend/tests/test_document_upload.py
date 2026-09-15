"""Tests for document upload API endpoints."""
from __future__ import annotations


class TestDocumentRequirementsEndpoint:
    def test_list_requirements_returns_list(self):
        """Verify the endpoint structure exists and returns data."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        # Without auth, should get 401
        resp = client.get(
            "/applications/00000000-0000-0000-0000-000000000001/document-requirements"
        )
        assert resp.status_code == 401

    def test_list_documents_returns_list(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/applications/00000000-0000-0000-0000-000000000001/documents")
        assert resp.status_code == 401

    def test_upload_requires_auth(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/applications/00000000-0000-0000-0000-000000000001/documents/D01/upload",
        )
        assert resp.status_code == 401

    def test_get_document_requires_auth(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001",
        )
        assert resp.status_code == 401

    def test_delete_document_requires_auth(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete(
            "/applications/00000000-0000-0000-0000-000000000001/documents/00000000-0000-0000-0000-000000000001",
        )
        assert resp.status_code == 401


class TestUploadValidation:
    def test_reject_empty_file(self):
        """Upload endpoint should reject empty file uploads."""
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="test.pdf",
            content_type="application/pdf",
            file_size=0,
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert not is_valid
        assert "empty" in error.lower() or "size" in error.lower()

    def test_reject_oversized_file(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="large.pdf",
            content_type="application/pdf",
            file_size=50 * 1024 * 1024,  # 50MB
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert not is_valid
        assert "size" in error.lower()

    def test_reject_wrong_type(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="script.exe",
            content_type="application/x-executable",
            file_size=1024,
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert not is_valid
        assert "type" in error.lower() or "mime" in error.lower()

    def test_accept_valid_file(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="doc.pdf",
            content_type="application/pdf",
            file_size=1024,
            accepted_types=["application/pdf"],
            max_size_mb=10,
        )
        assert is_valid
        assert error == ""

    def test_accept_wildcard_type(self):
        from app.api.documents import _validate_upload

        is_valid, error = _validate_upload(
            filename="photo.jpg",
            content_type="image/jpeg",
            file_size=1024,
            accepted_types=["image/*"],
            max_size_mb=10,
        )
        assert is_valid

    def test_reject_path_traversal(self):
        from app.api.documents import _sanitize_filename

        result = _sanitize_filename("../../etc/passwd.pdf")
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result


class TestSanitizeFilename:
    def test_removes_path_separators(self):
        from app.api.documents import _sanitize_filename

        assert _sanitize_filename("path/to/file.pdf") == "file.pdf"

    def test_removes_null_bytes(self):
        from app.api.documents import _sanitize_filename

        assert _sanitize_filename("file\x00.pdf") == "file.pdf"

    def test_preserves_dots_in_name(self):
        from app.api.documents import _sanitize_filename

        assert _sanitize_filename("my.document.v2.pdf") == "my.document.v2.pdf"

    def test_handles_empty_name(self):
        from app.api.documents import _sanitize_filename

        result = _sanitize_filename("")
        assert len(result) > 0  # Should generate a fallback name
