"""Tests for applicability condition validation."""
from __future__ import annotations

from app.rules.models import ApplicabilityCondition, ApplicabilityOp
from app.rules.validation import validate_applicability_conditions


def _cond(field: str, op: str, value) -> ApplicabilityCondition:
    return ApplicabilityCondition(field=field, op=ApplicabilityOp(op), value=value)


class TestAllowedFields:
    def test_valid_field_passes(self):
        result = validate_applicability_conditions(
            [_cond("sector", "eq", "chemicals")]
        )
        assert result.ok is True
        assert len(result.issues) == 0

    def test_unknown_field_fails(self):
        result = validate_applicability_conditions(
            [_cond("factory_occupier", "eq", "yes")]
        )
        assert result.ok is False
        assert len(result.issues) == 1
        assert "factory_occupier" in result.issues[0].reason

    def test_all_allowed_fields(self):
        """Each allowed field should pass validation with a type-appropriate value."""
        valid_values = {
            "sector": "chemicals",
            "entity_type": "pvt-ltd",
            "jurisdictions": "IN-GJ",
            "headcount": 100,
            "annual_turnover_inr": 5_000_000,
            "incorporation_date": "2024-01-15",
            "registered_state": "IN-GJ",
        }
        for field, value in valid_values.items():
            result = validate_applicability_conditions(
                [_cond(field, "eq", value)]
            )
            assert result.ok is True, f"Field {field} should be allowed, issues: {result.issues}"


class TestNumericOps:
    def test_numeric_op_on_numeric_field(self):
        result = validate_applicability_conditions(
            [_cond("headcount", "gt", 100)]
        )
        assert result.ok is True

    def test_numeric_op_on_string_field_fails(self):
        result = validate_applicability_conditions(
            [_cond("sector", "gt", "chemicals")]
        )
        assert result.ok is False
        assert "requires a numeric or date field" in result.issues[0].reason

    def test_numeric_op_on_date_field(self):
        result = validate_applicability_conditions(
            [_cond("incorporation_date", "gte", "2024-01-01")]
        )
        assert result.ok is True


class TestValueTypes:
    def test_entity_type_valid(self):
        result = validate_applicability_conditions(
            [_cond("entity_type", "eq", "pvt-ltd")]
        )
        assert result.ok is True

    def test_entity_type_invalid(self):
        result = validate_applicability_conditions(
            [_cond("entity_type", "eq", "factory-occupier")]
        )
        assert result.ok is False
        assert "EntityType enum" in result.issues[0].reason

    def test_jurisdiction_valid(self):
        result = validate_applicability_conditions(
            [_cond("jurisdictions", "eq", "IN-GJ")]
        )
        assert result.ok is True

    def test_jurisdiction_invalid(self):
        result = validate_applicability_conditions(
            [_cond("jurisdictions", "eq", "Gujarat")]
        )
        assert result.ok is False

    def test_headcount_valid(self):
        result = validate_applicability_conditions(
            [_cond("headcount", "gte", 100)]
        )
        assert result.ok is True

    def test_headcount_invalid_type(self):
        result = validate_applicability_conditions(
            [_cond("headcount", "gte", "hundred")]
        )
        assert result.ok is False
        assert "must be a number" in result.issues[0].reason

    def test_incorporation_date_valid(self):
        result = validate_applicability_conditions(
            [_cond("incorporation_date", "eq", "2024-06-15")]
        )
        assert result.ok is True

    def test_incorporation_date_invalid_format(self):
        result = validate_applicability_conditions(
            [_cond("incorporation_date", "eq", "15-06-2024")]
        )
        assert result.ok is False
        assert "ISO date" in result.issues[0].reason

    def test_sector_valid(self):
        result = validate_applicability_conditions(
            [_cond("sector", "eq", "chemicals")]
        )
        assert result.ok is True

    def test_sector_empty_string_fails(self):
        result = validate_applicability_conditions(
            [_cond("sector", "eq", "")]
        )
        assert result.ok is False


class TestInOperator:
    def test_entity_type_in_valid(self):
        result = validate_applicability_conditions(
            [_cond("entity_type", "in", ["pvt-ltd", "public-ltd"])]
        )
        assert result.ok is True

    def test_entity_type_in_invalid(self):
        result = validate_applicability_conditions(
            [_cond("entity_type", "in", ["factory"])]
        )
        assert result.ok is False

    def test_headcount_in_valid(self):
        result = validate_applicability_conditions(
            [_cond("headcount", "in", [50, 100, 150])]
        )
        assert result.ok is True


class TestMultipleIssues:
    def test_reports_all_issues(self):
        result = validate_applicability_conditions(
            [
                _cond("unknown_field", "eq", "x"),
                _cond("sector", "gt", "bad"),
                _cond("headcount", "eq", "not_a_number"),
            ]
        )
        assert result.ok is False
        assert len(result.issues) == 3
