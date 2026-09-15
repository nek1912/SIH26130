"""Tests for document extraction service."""
from __future__ import annotations

import io

from app.extraction.models import ExtractedField, ExtractionResult, ExtractionStatus
from app.extraction.service import (
    extract_document,
    extract_from_csv,
    extract_from_excel,
    extract_from_pdf,
)


class TestExtractFromPdf:
    def test_extract_metadata_from_valid_pdf(self):
        """Test extracting metadata from a valid PDF."""
        # Create a minimal valid PDF
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\n"
            b"startxref\n190\n%%EOF"
        )

        result = extract_from_pdf(pdf_content, "doc-1", "app-1")

        assert result.status == ExtractionStatus.COMPLETED
        assert result.document_id == "doc-1"
        assert result.application_id == "app-1"
        assert len(result.fields) > 0

        # Check page_count field
        page_fields = [f for f in result.fields if f.field_name == "page_count"]
        assert len(page_fields) == 1
        assert page_fields[0].field_value == 1

    def test_extract_handles_invalid_pdf(self):
        """Test extraction handles invalid PDF gracefully."""
        result = extract_from_pdf(b"not a pdf", "doc-1", "app-1")

        assert result.status == ExtractionStatus.FAILED
        assert len(result.errors) > 0

    def test_extract_file_size_field(self):
        """Test that file_size_bytes field is extracted from a valid PDF."""
        # Use a proper minimal PDF
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\n"
            b"startxref\n190\n%%EOF"
        )
        result = extract_from_pdf(pdf_content, "doc-1", "app-1")

        size_fields = [f for f in result.fields if f.field_name == "file_size_bytes"]
        assert len(size_fields) == 1
        assert size_fields[0].field_value == len(pdf_content)


class TestExtractFromCsv:
    def test_extract_headers_and_counts(self):
        """Test extracting headers and row/column counts from CSV."""
        csv_content = b"Name,Quantity,Unit\nChemical A,100,kg\nChemical B,50,L\n"

        result = extract_from_csv(csv_content, "doc-1", "app-1")

        assert result.status == ExtractionStatus.COMPLETED
        assert result.metadata["row_count"] == 2
        assert result.metadata["column_count"] == 3
        assert result.metadata["headers"] == ["Name", "Quantity", "Unit"]

        # Check fields
        headers_field = [f for f in result.fields if f.field_name == "headers"]
        assert len(headers_field) == 1
        assert headers_field[0].field_value == ["Name", "Quantity", "Unit"]

    def test_extract_empty_csv(self):
        """Test extraction from empty CSV."""
        result = extract_from_csv(b"", "doc-1", "app-1")

        assert result.status == ExtractionStatus.COMPLETED
        assert result.metadata["row_count"] == 0
        assert result.metadata["column_count"] == 0

    def test_extract_detects_empty_headers(self):
        """Test detection of empty headers."""
        csv_content = b"Name,,Quantity\nA,1,2\n"

        result = extract_from_csv(csv_content, "doc-1", "app-1")

        empty_header_fields = [
            f for f in result.fields if f.field_name == "empty_header_columns"
        ]
        assert len(empty_header_fields) == 1
        assert 1 in empty_header_fields[0].field_value

    def test_extract_handles_invalid_csv(self):
        """Test extraction handles invalid CSV gracefully."""
        # This should still work as CSV parser is lenient
        result = extract_from_csv(b"just,some,text", "doc-1", "app-1")
        assert result.status == ExtractionStatus.COMPLETED


class TestExtractFromExcel:
    def test_extract_sheet_info(self):
        """Test extracting sheet information from Excel."""
        try:
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            ws.title = "Materials"
            ws.append(["Name", "Quantity", "Unit"])
            ws.append(["Chemical A", 100, "kg"])

            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            content = buf.read()

            result = extract_from_excel(content, "doc-1", "app-1")

            assert result.status == ExtractionStatus.COMPLETED
            assert result.metadata["sheet_count"] == 1
            assert result.metadata["sheets"][0]["name"] == "Materials"
            assert result.metadata["sheets"][0]["headers"] == ["Name", "Quantity", "Unit"]
            assert result.metadata["sheets"][0]["row_count"] == 1

        except ImportError:
            # openpyxl not installed, skip
            pass

    def test_extract_handles_invalid_excel(self):
        """Test extraction handles invalid Excel file gracefully."""
        result = extract_from_excel(b"not excel", "doc-1", "app-1")

        assert result.status == ExtractionStatus.FAILED
        assert len(result.errors) > 0


class TestExtractDocument:
    def test_extract_pdf(self):
        """Test extraction dispatch for PDF."""
        pdf_content = b"%PDF-1.4 minimal"
        result = extract_document(pdf_content, "application/pdf", "doc-1", "app-1")
        assert result.status in (ExtractionStatus.COMPLETED, ExtractionStatus.FAILED)

    def test_extract_csv(self):
        """Test extraction dispatch for CSV."""
        csv_content = b"Name,Value\nA,1\n"
        result = extract_document(csv_content, "text/csv", "doc-1", "app-1")
        assert result.status == ExtractionStatus.COMPLETED

    def test_extract_unsupported_image(self):
        """Test extraction returns UNSUPPORTED for images."""
        result = extract_document(b"fake image", "image/jpeg", "doc-1", "app-1")
        assert result.status == ExtractionStatus.UNSUPPORTED
        assert "OCR" in result.errors[0]

    def test_extract_unsupported_type(self):
        """Test extraction returns UNSUPPORTED for unknown types."""
        result = extract_document(b"data", "application/octet-stream", "doc-1", "app-1")
        assert result.status == ExtractionStatus.UNSUPPORTED


class TestExtractionModels:
    def test_extracted_field_creation(self):
        """Test ExtractedField model creation."""
        field = ExtractedField(
            document_id="doc-1",
            application_id="app-1",
            field_name="page_count",
            field_value=5,
            field_type="integer",
        )
        assert field.document_id == "doc-1"
        assert field.field_name == "page_count"
        assert field.confidence == 1.0

    def test_extraction_result_creation(self):
        """Test ExtractionResult model creation."""
        result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
        )
        assert result.document_id == "doc-1"
        assert result.status == ExtractionStatus.COMPLETED
        assert result.fields == []
        assert result.errors == []
