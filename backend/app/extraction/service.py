"""Document extraction service.

Extracts structured metadata from uploaded documents using deterministic methods:
- PDF: metadata extraction (title, author, pages, creation date)
- CSV: header validation, row count, column detection
- Excel: sheet names, header validation, row counts

No LLM, OCR, or external AI services used.
"""
from __future__ import annotations

import csv
import io
import logging

from app.extraction.models import (
    ExtractedField,
    ExtractionResult,
    ExtractionStatus,
)

logger = logging.getLogger(__name__)


def extract_from_pdf(content: bytes, document_id: str, application_id: str) -> ExtractionResult:
    """Extract metadata from a PDF file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        metadata = reader.metadata or {}

        fields = []

        # Extract standard PDF metadata fields
        if metadata.get("/Title"):
            fields.append(ExtractedField(
                document_id=document_id,
                application_id=application_id,
                field_name="title",
                field_value=str(metadata["/Title"]),
                field_type="string",
                extraction_method="pdf_metadata",
            ))

        if metadata.get("/Author"):
            fields.append(ExtractedField(
                document_id=document_id,
                application_id=application_id,
                field_name="author",
                field_value=str(metadata["/Author"]),
                field_type="string",
                extraction_method="pdf_metadata",
            ))

        if metadata.get("/Creator"):
            fields.append(ExtractedField(
                document_id=document_id,
                application_id=application_id,
                field_name="creator",
                field_value=str(metadata["/Creator"]),
                field_type="string",
                extraction_method="pdf_metadata",
            ))

        # Page count
        page_count = len(reader.pages)
        fields.append(ExtractedField(
            document_id=document_id,
            application_id=application_id,
            field_name="page_count",
            field_value=page_count,
            field_type="integer",
            extraction_method="pdf_metadata",
        ))

        # File size
        fields.append(ExtractedField(
            document_id=document_id,
            application_id=application_id,
            field_name="file_size_bytes",
            field_value=len(content),
            field_type="integer",
            extraction_method="file_info",
        ))

        return ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus.COMPLETED,
            fields=fields,
            metadata={
                "page_count": page_count,
                "has_metadata": bool(metadata),
                "encrypted": reader.is_encrypted,
            },
        )

    except Exception as e:
        logger.warning("PDF extraction failed: %s", e)
        return ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus.FAILED,
            errors=[f"PDF extraction failed: {str(e)}"],
        )


def extract_from_csv(content: bytes, document_id: str, application_id: str) -> ExtractionResult:
    """Extract metadata from a CSV file."""
    try:
        text = content.decode("utf-8-sig")  # Handle BOM
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            return ExtractionResult(
                document_id=document_id,
                application_id=application_id,
                status=ExtractionStatus.COMPLETED,
                fields=[],
                metadata={"row_count": 0, "column_count": 0},
            )

        headers = rows[0]
        data_rows = rows[1:]

        fields = []

        # Header fields
        fields.append(ExtractedField(
            document_id=document_id,
            application_id=application_id,
            field_name="headers",
            field_value=headers,
            field_type="list",
            extraction_method="csv_headers",
        ))

        fields.append(ExtractedField(
            document_id=document_id,
            application_id=application_id,
            field_name="column_count",
            field_value=len(headers),
            field_type="integer",
            extraction_method="csv_metadata",
        ))

        fields.append(ExtractedField(
            document_id=document_id,
            application_id=application_id,
            field_name="row_count",
            field_value=len(data_rows),
            field_type="integer",
            extraction_method="csv_metadata",
        ))

        # Check for empty headers
        empty_headers = [i for i, h in enumerate(headers) if not h.strip()]
        if empty_headers:
            fields.append(ExtractedField(
                document_id=document_id,
                application_id=application_id,
                field_name="empty_header_columns",
                field_value=empty_headers,
                field_type="list",
                extraction_method="csv_validation",
            ))

        return ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus.COMPLETED,
            fields=fields,
            metadata={
                "row_count": len(data_rows),
                "column_count": len(headers),
                "headers": headers,
            },
        )

    except Exception as e:
        logger.warning("CSV extraction failed: %s", e)
        return ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus.FAILED,
            errors=[f"CSV extraction failed: {str(e)}"],
        )


def extract_from_excel(content: bytes, document_id: str, application_id: str) -> ExtractionResult:
    """Extract metadata from an Excel file."""
    try:
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)

        fields = []
        sheet_info = []

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            headers = [str(c) if c is not None else "" for c in rows[0]] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []

            sheet_info.append({
                "name": sheet_name,
                "headers": headers,
                "row_count": len(data_rows),
                "column_count": len(headers),
            })

            # Add fields for first sheet
            if len(sheet_info) == 1:
                fields.append(ExtractedField(
                    document_id=document_id,
                    application_id=application_id,
                    field_name="headers",
                    field_value=headers,
                    field_type="list",
                    extraction_method="excel_headers",
                    metadata={"sheet": sheet_name},
                ))

                fields.append(ExtractedField(
                    document_id=document_id,
                    application_id=application_id,
                    field_name="column_count",
                    field_value=len(headers),
                    field_type="integer",
                    extraction_method="excel_metadata",
                ))

                fields.append(ExtractedField(
                    document_id=document_id,
                    application_id=application_id,
                    field_name="row_count",
                    field_value=len(data_rows),
                    field_type="integer",
                    extraction_method="excel_metadata",
                ))

        fields.append(ExtractedField(
            document_id=document_id,
            application_id=application_id,
            field_name="sheet_count",
            field_value=len(wb.sheetnames),
            field_type="integer",
            extraction_method="excel_metadata",
        ))

        wb.close()

        return ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus.COMPLETED,
            fields=fields,
            metadata={
                "sheet_count": len(wb.sheetnames),
                "sheets": sheet_info,
            },
        )

    except Exception as e:
        logger.warning("Excel extraction failed: %s", e)
        return ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus.FAILED,
            errors=[f"Excel extraction failed: {str(e)}"],
        )


def extract_document(
    content: bytes,
    mime_type: str,
    document_id: str,
    application_id: str,
) -> ExtractionResult:
    """Extract metadata from a document based on its MIME type.

    Supports:
    - application/pdf
    - text/csv
    - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

    Returns REVIEW_REQUIRED for unsupported types.
    """
    if mime_type == "application/pdf":
        return extract_from_pdf(content, document_id, application_id)

    if mime_type == "text/csv":
        return extract_from_csv(content, document_id, application_id)

    if mime_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ):
        return extract_from_excel(content, document_id, application_id)

    # Image types - cannot extract without OCR
    if mime_type.startswith("image/"):
        return ExtractionResult(
            document_id=document_id,
            application_id=application_id,
            status=ExtractionStatus.UNSUPPORTED,
            errors=[f"Image extraction requires OCR (not available): {mime_type}"],
        )

    return ExtractionResult(
        document_id=document_id,
        application_id=application_id,
        status=ExtractionStatus.UNSUPPORTED,
        errors=[f"Unsupported MIME type for extraction: {mime_type}"],
    )
