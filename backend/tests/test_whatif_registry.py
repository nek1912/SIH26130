"""What-If overrides against the fact registry (Phase 2).

IN-MH overrides use the MH registry (unknown field / wrong type /
invalid enum / jurisdiction mismatch rejected; None removes the key;
base facts never mutated; nothing persisted). IN-GJ behavior is
unchanged.
"""
from __future__ import annotations

import pytest

from app.orchestration.whatif import (
    WhatIfValidationError,
    apply_fact_overrides,
)
from app.rules.facts import GJ_JURISDICTION, MH_JURISDICTION


class TestMHOverrides:
    def test_valid_override_applies(self):
        base = {"F-BLD-01": 12000}
        merged = apply_fact_overrides(
            base, {"F-BLD-01": 25000}, jurisdiction=MH_JURISDICTION
        )
        assert merged == {"F-BLD-01": 25000}

    def test_unknown_field_rejected(self):
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(
                {}, {"F-NOPE-99": True}, jurisdiction=MH_JURISDICTION
            )

    def test_invalid_type_rejected(self):
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(
                {}, {"F-BLD-01": "big"}, jurisdiction=MH_JURISDICTION
            )

    def test_invalid_enum_rejected(self):
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(
                {}, {"F-PRD-03": "ALCHEMY"}, jurisdiction=MH_JURISDICTION
            )

    def test_gujarat_field_in_mh_rejected_as_mismatch(self):
        with pytest.raises(WhatIfValidationError) as exc:
            apply_fact_overrides(
                {}, {"industry_type": "textiles"},
                jurisdiction=MH_JURISDICTION,
            )
        assert "mismatch" in str(exc.value).lower()

    def test_excluded_fact_rejected(self):
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides(
                {}, {"F-BLD-02": True}, jurisdiction=MH_JURISDICTION
            )

    def test_none_removes_key(self):
        base = {"F-BLD-01": 12000, "F-PRD-01": True}
        merged = apply_fact_overrides(
            base, {"F-BLD-01": None}, jurisdiction=MH_JURISDICTION
        )
        assert merged == {"F-PRD-01": True}

    def test_base_facts_not_mutated(self):
        base = {"F-BLD-01": 12000}
        apply_fact_overrides(
            base, {"F-BLD-01": 1}, jurisdiction=MH_JURISDICTION
        )
        assert base == {"F-BLD-01": 12000}

    def test_unknown_jurisdiction_rejected(self):
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides({}, {"F-BLD-01": 1}, jurisdiction="IN-US")


class TestGJOverridesUnchanged:
    def test_default_jurisdiction_is_gujarat(self):
        base = {"production_capacity": 20000}
        assert apply_fact_overrides(base, {"production_capacity": 100}) == {
            "production_capacity": 100
        }
        assert apply_fact_overrides(
            base, {"production_capacity": 100},
            jurisdiction=GJ_JURISDICTION,
        ) == {"production_capacity": 100}

    def test_gj_unknown_field_still_rejected(self):
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides({}, {"nope": 1})

    def test_gj_none_removal_still_works(self):
        base = {"production_capacity": 20000}
        assert apply_fact_overrides(base, {"production_capacity": None}) == {}

    def test_mh_field_in_gj_is_unknown_field(self):
        with pytest.raises(WhatIfValidationError):
            apply_fact_overrides({}, {"F-BLD-01": 5})
