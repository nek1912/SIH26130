"""Tests for document requirement seed data and lookup."""
from __future__ import annotations

from app.seed.documents import (
    APPROVAL_TO_DOCS,
    get_requirements_for_approval,
    load_document_requirements,
    parse_used_for,
)


class TestLoadDocumentRequirements:
    def test_returns_17_requirements(self):
        reqs = load_document_requirements()
        assert len(reqs) == 17

    def test_all_have_doc_ids(self):
        reqs = load_document_requirements()
        for req in reqs:
            assert "requirement_key" in req
            assert req["requirement_key"].startswith("D")
            assert len(req["requirement_key"]) == 3

    def test_all_have_required_fields(self):
        reqs = load_document_requirements()
        required_fields = [
            "requirement_key", "document_name", "approval_ids",
            "domain", "requirement_level", "source_url",
        ]
        for req in reqs:
            for field in required_fields:
                assert field in req, f"Missing {field} in {req['requirement_key']}"

    def test_mandatory_vs_required_levels(self):
        reqs = load_document_requirements()
        levels = {req["requirement_level"] for req in reqs}
        assert "required" in levels
        assert "mandatory" in levels

    def test_conditional_requirements_exist(self):
        reqs = load_document_requirements()
        conditional = [r for r in reqs if r["requirement_level"] == "conditional"]
        assert len(conditional) >= 3  # D15, D16, D17 are conditional


class TestParseUsedFor:
    def test_single_approval(self):
        result = parse_used_for("GIDC Plan")
        assert "A01" in result

    def test_multiple_approvals(self):
        result = parse_used_for("GIDC Plan/Water/Drainage")
        assert "A01" in result
        assert "A02" in result
        assert "A03" in result

    def test_conditional_text(self):
        result = parse_used_for("MSIHC")
        assert "A12" in result


class TestGetRequirementsForApproval:
    def test_gidc_plan_returns_documents(self):
        reqs = get_requirements_for_approval("A01")
        keys = [r["requirement_key"] for r in reqs]
        assert "D01" in keys  # GIDC Offer-cum-Allotment
        assert "D02" in keys  # GIDC Licence Agreement
        assert "D04" in keys  # Approved Building Plan

    def test_gpcb_returns_documents(self):
        reqs = get_requirements_for_approval("A04")
        keys = [r["requirement_key"] for r in reqs]
        assert "D05" in keys  # GPCB CTE/NOC

    def test_unknown_approval_returns_empty(self):
        reqs = get_requirements_for_approval("A99")
        assert reqs == []


class TestApprovalToDocsMapping:
    def test_all_18_approvals_mapped(self):
        for i in range(1, 19):
            aid = f"A{i:02d}"
            assert aid in APPROVAL_TO_DOCS, f"Approval {aid} not mapped"

    def test_gidc_plan_maps_to_three_docs(self):
        assert len(APPROVAL_TO_DOCS["A01"]) >= 3


class TestDocumentsRepository:
    """Tests for DocumentsRepository (unit tests with mocked Supabase client)."""

    def test_list_requirements_for_application(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        chain = mock_client.table.return_value.select.return_value
        chain = chain.eq.return_value.order.return_value
        chain.execute.return_value.data = [
            {
                "id": "1",
                "application_id": "app-1",
                "requirement_key": "D01",
                "readiness": "pending",
            },
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.list_requirements_for_application("app-1")
        assert len(result) == 1
        assert result[0]["requirement_key"] == "D01"

    def test_get_requirement(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        chain = mock_client.table.return_value.select.return_value
        chain = chain.eq.return_value.eq.return_value
        chain.execute.return_value.data = [
            {"id": "1", "requirement_key": "D01"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.get_requirement("app-1", "D01")
        assert result is not None

    def test_update_requirement_readiness(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        chain = mock_client.table.return_value.update.return_value
        chain = chain.eq.return_value.eq.return_value
        chain.execute.return_value.data = [
            {"id": "1", "readiness": "uploaded"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.update_requirement_readiness("app-1", "D01", "uploaded")
        assert result["readiness"] == "uploaded"

    def test_list_documents_for_application(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        chain = mock_client.table.return_value.select.return_value
        chain = chain.eq.return_value.order.return_value
        chain.execute.return_value.data = [
            {
                "id": "doc-1",
                "application_id": "app-1",
                "requirement_key": "D01",
            },
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.list_documents_for_application("app-1")
        assert len(result) == 1

    def test_create_document(self):
        from unittest.mock import MagicMock

        from app.repositories.documents import DocumentsRepository

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value \
            .execute.return_value.data = [
            {"id": "doc-1", "requirement_key": "D01"},
        ]
        repo = DocumentsRepository(mock_client)
        result = repo.create_document(
            {"requirement_key": "D01", "application_id": "app-1"}
        )
        assert result["id"] == "doc-1"
