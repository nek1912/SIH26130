"""Tests for deterministic validation engine."""
from __future__ import annotations

from app.extraction.models import (
    ExtractedField,
    ExtractionResult,
    ExtractionStatus,
    ValidationOutcome,
)
from app.extraction.validation import VALIDATION_RULES, validate_document


class TestValidateDocument:
    def test_valid_pdf_for_land_domain(self):
        """Test VALID outcome for a proper PDF in LAND domain."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
            fields=[
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="page_count",
                    field_value=5,
                    field_type="integer",
                ),
            ],
            metadata={"page_count": 5},
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D01",
            domain="LAND",
            mime_type="application/pdf",
        )

        assert result.outcome == ValidationOutcome.VALID
        assert result.document_id == "doc-1"
        assert result.requirement_key == "D01"
        assert len(result.findings) > 0
        assert all(f.outcome == ValidationOutcome.VALID for f in result.findings)

    def test_invalid_mime_type(self):
        """Test INVALID outcome when MIME type is not accepted."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
            fields=[
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="page_count",
                    field_value=1,
                    field_type="integer",
                ),
            ],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D01",
            domain="LAND",
            mime_type="image/jpeg",
            accepted_mime_types=["application/pdf"],
        )

        assert result.outcome == ValidationOutcome.INVALID
        invalid_findings = [f for f in result.findings if f.outcome == ValidationOutcome.INVALID]
        assert len(invalid_findings) > 0

    def test_unsupported_extraction_returns_review_required(self):
        """Test REVIEW_REQUIRED when extraction is unsupported."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.UNSUPPORTED,
            errors=["Image extraction requires OCR"],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D01",
            domain="LAND",
            mime_type="image/jpeg",
        )

        assert result.outcome == ValidationOutcome.REVIEW_REQUIRED

    def test_failed_extraction_returns_review_required(self):
        """Test REVIEW_REQUIRED when extraction fails."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.FAILED,
            errors=["PDF parsing failed"],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D01",
            domain="LAND",
            mime_type="application/pdf",
        )

        assert result.outcome == ValidationOutcome.REVIEW_REQUIRED

    def test_valid_csv_for_chemical_domain(self):
        """Test VALID outcome for CSV in CHEMICAL domain."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
            fields=[
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="headers",
                    field_value=["Chemical", "Quantity"],
                    field_type="list",
                ),
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="column_count",
                    field_value=2,
                    field_type="integer",
                ),
            ],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D11",
            domain="CHEMICAL",
            mime_type="text/csv",
        )

        assert result.outcome == ValidationOutcome.VALID

    def test_csv_with_insufficient_columns(self):
        """Test INVALID outcome when CSV has too few columns."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
            fields=[
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="headers",
                    field_value=["Name"],
                    field_type="list",
                ),
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="column_count",
                    field_value=1,
                    field_type="integer",
                ),
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="mime_type",
                    field_value="text/csv",
                    field_type="string",
                ),
            ],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D11",
            domain="CHEMICAL",
            mime_type="text/csv",
        )

        # Should be INVALID due to insufficient columns
        assert result.outcome == ValidationOutcome.INVALID

    def test_source_refs_collected(self):
        """Test that source references are collected from findings."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
            fields=[
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="page_count",
                    field_value=1,
                    field_type="integer",
                ),
            ],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D01",
            domain="LAND",
            mime_type="application/pdf",
        )

        assert len(result.source_refs) > 0

    def test_findings_have_rule_info(self):
        """Test that findings include rule ID and description."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
            fields=[
                ExtractedField(
                    document_id="doc-1",
                    application_id="app-1",
                    field_name="page_count",
                    field_value=1,
                    field_type="integer",
                ),
            ],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D01",
            domain="LAND",
            mime_type="application/pdf",
        )

        for finding in result.findings:
            assert finding.rule_id
            assert finding.rule_description
            assert finding.field_name

    def test_unknown_domain_produces_no_findings(self):
        """Test that unknown domain produces no domain-specific findings."""
        extraction_result = ExtractionResult(
            document_id="doc-1",
            application_id="app-1",
            status=ExtractionStatus.COMPLETED,
            fields=[],
        )

        result = validate_document(
            extraction_result=extraction_result,
            requirement_key="D99",
            domain="UNKNOWN_DOMAIN",
            mime_type="application/pdf",
        )

        # No domain-specific findings, but outcome should be VALID
        # (no rules to fail)
        assert result.outcome == ValidationOutcome.VALID


class TestValidationRules:
    def test_all_domains_have_rules(self):
        """Test that all expected domains have validation rules."""
        expected_domains = [
            "LAND", "BUILDING", "ENVIRONMENT", "PROCESS", "WASTE",
            "CHEMICAL", "FIRE", "ELECTRICAL", "FACTORY", "CHEMICAL STORAGE", "WATER",
        ]
        for domain in expected_domains:
            assert domain in VALIDATION_RULES, f"Domain {domain} missing rules"

    def test_rules_have_required_fields(self):
        """Test that all rules have required fields."""
        for domain, rules in VALIDATION_RULES.items():
            for rule in rules:
                assert "rule_id" in rule, f"Rule in {domain} missing rule_id"
                assert "description" in rule, f"Rule in {domain} missing description"
                assert "field_name" in rule, f"Rule in {domain} missing field_name"
                assert "check" in rule, f"Rule in {domain} missing check"
                assert "source_ref" in rule, f"Rule in {domain} missing source_ref"

    def test_rules_have_valid_check_types(self):
        """Test that all rules have valid check types."""
        valid_checks = {"accepted_mime", "min_value", "conditional_min"}
        for domain, rules in VALIDATION_RULES.items():
            for rule in rules:
                assert rule["check"] in valid_checks, (
                    f"Rule {rule['rule_id']} in {domain} has invalid check type: {rule['check']}"
                )


class TestValidationModels:
    def test_field_finding_creation(self):
        """Test FieldFinding model creation."""
        from app.extraction.models import FieldFinding

        finding = FieldFinding(
            field_name="page_count",
            rule_id="LAND-002",
            rule_description="Document must have at least 1 page",
            outcome=ValidationOutcome.VALID,
            expected=1,
            actual=5,
            message="Value 5 meets minimum 1",
            source_ref="GIDC Requirements",
        )
        assert finding.field_name == "page_count"
        assert finding.outcome == ValidationOutcome.VALID

    def test_validation_result_creation(self):
        """Test ValidationResult model creation."""
        from app.extraction.models import ValidationResult

        result = ValidationResult(
            document_id="doc-1",
            application_id="app-1",
            requirement_key="D01",
            outcome=ValidationOutcome.VALID,
        )
        assert result.document_id == "doc-1"
        assert result.outcome == ValidationOutcome.VALID
        assert result.findings == []
