"""Tests for cross-document consistency engine."""
from __future__ import annotations

from app.consistency.engine import check_application_consistency
from app.consistency.models import (
    ConsistencyFinding,
    ConsistencyOutcome,
    ConsistencyResult,
    ConsistencyRule,
)
from app.extraction.models import ExtractedField
from app.seed.consistency import load_consistency_rules


def _make_field(
    doc_id: str, app_id: str, field_name: str, value: str | None,
) -> ExtractedField:
    """Helper to create an ExtractedField for testing."""
    return ExtractedField(
        document_id=doc_id,
        application_id=app_id,
        field_name=field_name,
        field_value=value,
        field_type="string",
    )


DOC_REQ_MAP = {
    "doc-D01": "D01",
    "doc-D02": "D02",
    "doc-D03": "D03",
    "doc-D04": "D04",
    "doc-D05": "D05",
    "doc-D06": "D06",
    "doc-D07": "D07",
    "doc-D08": "D08",
    "doc-D09": "D09",
    "doc-D10": "D10",
    "doc-D11": "D11",
    "doc-D12": "D12",
    "doc-D13": "D13",
    "doc-D14": "D14",
    "doc-D15": "D15",
    "doc-D16": "D16",
    "doc-D17": "D17",
}


RULES = [
    ConsistencyRule(
        id="C01", canonical_field="plot_area_sqm",
        affected_systems="GIDC Plan", evidence_field="Land/title/GIS",
        requirement_key="MUST_MATCH", document_keys=["D01", "D02"],
    ),
    ConsistencyRule(
        id="C02", canonical_field="builtup_area_sqm",
        affected_systems="GIDC Plan / BU", evidence_field="Architectural drawings",
        requirement_key="MUST_MATCH", document_keys=["D04"],
    ),
]


class TestConsistencyModels:
    def test_consistency_outcome_values(self):
        assert ConsistencyOutcome.VALID == "VALID"
        assert ConsistencyOutcome.REVIEW_REQUIRED == "REVIEW_REQUIRED"
        assert ConsistencyOutcome.INSUFFICIENT_DATA == "INSUFFICIENT_DATA"

    def test_consistency_rule_creation(self):
        rule = ConsistencyRule(
            id="C01",
            canonical_field="plot_area_sqm",
            affected_systems="GIDC Plan",
            evidence_field="Land/title/GIS",
            requirement_key="MUST_MATCH",
            document_keys=["D01", "D02", "D03"],
        )
        assert rule.id == "C01"
        assert rule.document_keys == ["D01", "D02", "D03"]

    def test_consistency_finding_creation(self):
        finding = ConsistencyFinding(
            rule_id="C01",
            canonical_field="plot_area_sqm",
            outcome=ConsistencyOutcome.VALID,
            observed_values={"D01": "5000", "D02": "5000"},
            expected_relationship="MUST_MATCH across [D01, D02]",
            message="Values match",
            source_ref="Workbook Consistency_Fields C01",
        )
        assert finding.outcome == ConsistencyOutcome.VALID
        assert len(finding.observed_values) == 2

    def test_consistency_result_creation(self):
        result = ConsistencyResult(
            application_id="app-1",
            outcome=ConsistencyOutcome.VALID,
            findings=[],
            checked_at="2026-09-15T10:00:00",
            rule_version="1",
        )
        assert result.application_id == "app-1"
        assert result.outcome == ConsistencyOutcome.VALID


class TestConsistencySeed:
    def test_load_returns_all_18_rules(self):
        rules = load_consistency_rules()
        assert len(rules) == 18

    def test_rule_ids_are_c01_through_c18(self):
        rules = load_consistency_rules()
        ids = [r.id for r in rules]
        expected = [f"C{i:02d}" for i in range(1, 19)]
        assert ids == expected

    def test_all_rules_are_must_match(self):
        rules = load_consistency_rules()
        assert all(r.requirement_key == "MUST_MATCH" for r in rules)

    def test_multi_doc_rules_have_multiple_keys(self):
        rules = load_consistency_rules()
        multi_doc = [r for r in rules if len(r.document_keys) > 1]
        assert len(multi_doc) >= 10

    def test_document_keys_are_valid_format(self):
        rules = load_consistency_rules()
        for rule in rules:
            for key in rule.document_keys:
                assert key.startswith("D"), (
                    f"Invalid doc key {key} in rule {rule.id}"
                )


class TestConsistencyEngine:
    def test_all_identical_values_returns_valid(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D04", "app-1", "builtup_area_sqm", "2000"),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        assert result.outcome == ConsistencyOutcome.VALID
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID

    def test_mismatched_values_returns_review_required(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "4800"),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        assert result.outcome == ConsistencyOutcome.REVIEW_REQUIRED
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.REVIEW_REQUIRED
        assert "D01" in c01.observed_values
        assert "D02" in c01.observed_values

    def test_no_values_returns_insufficient_data(self):
        fields = []
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        assert result.outcome == ConsistencyOutcome.INSUFFICIENT_DATA
        assert all(
            f.outcome == ConsistencyOutcome.INSUFFICIENT_DATA
            for f in result.findings
        )

    def test_single_document_has_value_returns_valid(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID

    def test_partial_values_matching_returns_valid(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID

    def test_empty_string_treated_as_no_value(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", ""),
            _make_field("doc-D02", "app-1", "plot_area_sqm", ""),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.INSUFFICIENT_DATA

    def test_single_doc_rule_always_valid(self):
        fields = [
            _make_field("doc-D04", "app-1", "builtup_area_sqm", "2000"),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        c02 = [f for f in result.findings if f.rule_id == "C02"][0]
        assert c02.outcome == ConsistencyOutcome.VALID

    def test_mixed_outcomes_worst_case(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "4800"),
            _make_field("doc-D04", "app-1", "builtup_area_sqm", "2000"),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        assert result.outcome == ConsistencyOutcome.REVIEW_REQUIRED

    def test_empty_fields_all_insufficient_data(self):
        result = check_application_consistency(
            "app-1", [], RULES, DOC_REQ_MAP,
        )
        assert len(result.findings) == 2
        assert all(
            f.outcome == ConsistencyOutcome.INSUFFICIENT_DATA
            for f in result.findings
        )

    def test_deterministic_finding_order(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
            _make_field("doc-D04", "app-1", "builtup_area_sqm", "2000"),
        ]
        result1 = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        result2 = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        assert [f.rule_id for f in result1.findings] == [
            f.rule_id for f in result2.findings
        ]

    def test_null_field_value_treated_as_no_value(self):
        fields = [
            _make_field("doc-D01", "app-1", "plot_area_sqm", None),
            _make_field("doc-D02", "app-1", "plot_area_sqm", "5000"),
        ]
        result = check_application_consistency(
            "app-1", fields, RULES, DOC_REQ_MAP,
        )
        c01 = [f for f in result.findings if f.rule_id == "C01"][0]
        assert c01.outcome == ConsistencyOutcome.VALID
