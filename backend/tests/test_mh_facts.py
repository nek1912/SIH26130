"""MH fact registry + validation (Phase 2).

The registry is a code-defined transcription of the v5 facts.csv
artifact: 128 ACTIVE/VERIFIED IN-MH facts. F-BLD-02 is excluded by the
baseline itself. Missing (None) is always valid; supplied values must
satisfy the spec.
"""
from __future__ import annotations

import pytest

from app.rules.facts import (
    EXCLUDED_MH_FACTS,
    GJ_JURISDICTION,
    MH_FACTS,
    MH_JURISDICTION,
    FactSpec,
    FactValidationError,
    FactValueType,
    get_fact_spec,
    is_unknown_value,
    mh_fact_keys,
    validate_fact_value,
)


class TestRegistryContents:
    def test_128_mh_facts_encoded(self):
        assert len(MH_FACTS) == 128
        assert len(mh_fact_keys()) == 128
        assert mh_fact_keys() == sorted(MH_FACTS)

    def test_deprecated_fact_excluded_explicitly(self):
        assert "F-BLD-02" not in MH_FACTS
        assert "F-BLD-02" in EXCLUDED_MH_FACTS

    def test_all_specs_are_in_mh_scoped(self):
        for key, spec in MH_FACTS.items():
            assert spec.key == key
            assert spec.jurisdiction == MH_JURISDICTION
            assert isinstance(spec.value_type, FactValueType)
            assert spec.label

    def test_no_gujarat_field_leaks_into_registry(self):
        for gj_key in (
            "industry_type",
            "plot_area_sqm",
            "production_capacity",
            "hazardous_process",
            "building_height",
            "discharge_mode",
        ):
            assert gj_key not in MH_FACTS

    def test_valid_mh_fact_lookup(self):
        spec = get_fact_spec(MH_JURISDICTION, "F-PRD-01")
        assert isinstance(spec, FactSpec)
        assert spec.value_type == FactValueType.BOOLEAN
        assert spec.unknown_allowed is True

    def test_unknown_fact_rejected(self):
        with pytest.raises(FactValidationError) as exc:
            get_fact_spec(MH_JURISDICTION, "F-NOPE-99")
        assert exc.value.code == FactValidationError.UNKNOWN_FIELD

    def test_gujarat_field_in_mh_is_mismatch(self):
        with pytest.raises(FactValidationError) as exc:
            get_fact_spec(MH_JURISDICTION, "industry_type")
        assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH

    def test_mh_field_in_gj_is_mismatch(self):
        with pytest.raises(FactValidationError) as exc:
            get_fact_spec(GJ_JURISDICTION, "F-PRD-01")
        assert exc.value.code == FactValidationError.JURISDICTION_MISMATCH

    def test_excluded_fact_rejected_explicitly(self):
        with pytest.raises(FactValidationError) as exc:
            get_fact_spec(MH_JURISDICTION, "F-BLD-02")
        assert exc.value.code == FactValidationError.DO_NOT_IMPLEMENT

    def test_unknown_jurisdiction_rejected(self):
        with pytest.raises(FactValidationError) as exc:
            get_fact_spec("IN-US", "F-PRD-01")
        assert exc.value.code == FactValidationError.UNKNOWN_JURISDICTION


class TestMissingUnknownDistinction:
    def test_none_is_always_valid(self):
        for key in ("F-PRD-01", "F-BLD-01", "F-PV-02", "F-BLR-08",
                    "F-PRD-03", "F-HAZ-01"):
            validate_fact_value(MH_JURISDICTION, key, None)

    def test_unknown_token_accepted_where_allowed(self):
        assert is_unknown_value(MH_FACTS["F-PRD-01"], "UNKNOWN") is True
        validate_fact_value(MH_JURISDICTION, "F-PRD-01", "UNKNOWN")
        validate_fact_value(MH_JURISDICTION, "F-WAT-03", "UNKNOWN")

    def test_unknown_token_rejected_where_strict(self):
        assert is_unknown_value(MH_FACTS["F-PV-02"], "UNKNOWN") is False
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-PV-02", "UNKNOWN")

    def test_is_unknown_value_none(self):
        assert is_unknown_value(MH_FACTS["F-PV-02"], None) is True
        assert is_unknown_value(MH_FACTS["F-PV-02"], True) is False


class TestTypeValidation:
    def test_boolean(self):
        validate_fact_value(MH_JURISDICTION, "F-PV-02", True)
        with pytest.raises(FactValidationError) as exc:
            validate_fact_value(MH_JURISDICTION, "F-PV-02", "true")
        assert exc.value.code == FactValidationError.WRONG_TYPE
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-PV-02", 1)

    def test_integer_rejects_bool(self):
        validate_fact_value(MH_JURISDICTION, "F-LAB-01", 60)
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-LAB-01", True)
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-LAB-01", 1.5)

    def test_number(self):
        validate_fact_value(MH_JURISDICTION, "F-BLD-01", 12000)
        validate_fact_value(MH_JURISDICTION, "F-BLD-01", 12000.5)
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-BLD-01", "12000")

    def test_enum(self):
        validate_fact_value(MH_JURISDICTION, "F-PRD-03", "SYNTHESIS")
        with pytest.raises(FactValidationError) as exc:
            validate_fact_value(MH_JURISDICTION, "F-PRD-03", "SYNTHESIZE")
        assert exc.value.code == FactValidationError.INVALID_ENUM

    def test_enum_set(self):
        validate_fact_value(
            MH_JURISDICTION, "F-PRD-02", ["PESTICIDE_TECHNICAL", "NONE"]
        )
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-PRD-02", "PESTICIDE_TECHNICAL")
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-PRD-02", ["NOPE"])

    def test_enum_placeholder_prefix(self):
        validate_fact_value(
            MH_JURISDICTION, "F-LOC-05", "MUNICIPAL_CORP:Pune"
        )
        validate_fact_value(MH_JURISDICTION, "F-LOC-05", "MIDC")
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-LOC-05", "GRAM_PANCHAYAT:X")

    def test_date(self):
        validate_fact_value(MH_JURISDICTION, "F-BLR-08", "2026-09-26")
        with pytest.raises(FactValidationError) as exc:
            validate_fact_value(MH_JURISDICTION, "F-BLR-08", "26-09-2026")
        assert exc.value.code == FactValidationError.INVALID_DATE
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-BLR-08", 20260926)

    def test_list_and_object_containers(self):
        validate_fact_value(
            MH_JURISDICTION, "F-HAZ-01", [{"chemical": "Methanol"}]
        )
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-HAZ-01", "Methanol")
        validate_fact_value(
            MH_JURISDICTION, "F-LOC-09", {"lat": 21.7, "lon": 72.9}
        )
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-LOC-09", "21.7,72.9")

    def test_string(self):
        validate_fact_value(MH_JURISDICTION, "F-LOC-04", "Vagra")
        with pytest.raises(FactValidationError):
            validate_fact_value(MH_JURISDICTION, "F-LOC-04", 123)

    def test_derived_facts_are_marked(self):
        assert MH_FACTS["F-PRC-03"].derived is True
        assert MH_FACTS["F-INC-01"].derived is True
        assert MH_FACTS["F-PRD-01"].derived is False
