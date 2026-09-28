"""Regression tests for shared project-facts resolution.

Both baseline orchestration and What-If must operate on exactly the same
resolved fact representation. The project_facts row carries typed columns
plus a facts_json JSONB extension; the resolver flattens facts_json and
drops metadata/None so missing facts fail closed (UNKNOWN) instead of
evaluating to FALSE.
"""
from __future__ import annotations


class TestResolveProjectFacts:
    def test_none_record_resolves_empty(self):
        from app.orchestration.facts import resolve_project_facts

        assert resolve_project_facts(None) == {}

    def test_flat_record_passes_through(self):
        from app.orchestration.facts import resolve_project_facts

        record = {
            "id": "x",
            "project_id": "y",
            "industry_type": "synthetic organic / specialty chemical manufacturing",
            "power_demand": 1000,
            "created_at": "t",
            "updated_at": "t",
        }
        resolved = resolve_project_facts(record)
        assert resolved == {
            "industry_type": "synthetic organic / specialty chemical manufacturing",
            "power_demand": 1000,
        }

    def test_facts_json_flattened(self):
        from app.orchestration.facts import resolve_project_facts

        record = {
            "id": "x",
            "project_id": "y",
            "entity_type": "pvt-ltd",
            "facts_json": {
                "industry_type": "synthetic organic / specialty chemical manufacturing",
                "production_capacity": 20000,
                "groundwater_use": False,
            },
            "created_at": "t",
            "updated_at": "t",
        }
        resolved = resolve_project_facts(record)
        assert resolved["industry_type"] == "synthetic organic / specialty chemical manufacturing"
        assert resolved["production_capacity"] == 20000
        assert resolved["groundwater_use"] is False
        assert resolved["entity_type"] == "pvt-ltd"
        assert "facts_json" not in resolved

    def test_typed_columns_win_over_facts_json(self):
        from app.orchestration.facts import resolve_project_facts

        record = {
            "id": "x",
            "project_id": "y",
            "headcount": 60,
            "facts_json": {"headcount": 5},
            "created_at": "t",
            "updated_at": "t",
        }
        assert resolve_project_facts(record)["headcount"] == 60

    def test_none_values_treated_as_missing(self):
        from app.orchestration.facts import resolve_project_facts

        record = {
            "id": "x",
            "project_id": "y",
            "registered_state": None,
            "facts_json": {"incorporation_date": None, "power_demand": 100},
            "created_at": "t",
            "updated_at": "t",
        }
        resolved = resolve_project_facts(record)
        assert "registered_state" not in resolved
        assert "incorporation_date" not in resolved
        assert resolved["power_demand"] == 100

    def test_non_dict_facts_json_ignored(self):
        from app.orchestration.facts import resolve_project_facts

        record = {
            "id": "x",
            "project_id": "y",
            "power_demand": 100,
            "facts_json": "not-a-dict",
            "created_at": "t",
            "updated_at": "t",
        }
        assert resolve_project_facts(record) == {"power_demand": 100}

    def test_does_not_mutate_input(self):
        from app.orchestration.facts import resolve_project_facts

        record = {
            "id": "x",
            "project_id": "y",
            "facts_json": {"power_demand": 100},
            "created_at": "t",
            "updated_at": "t",
        }
        snapshot = {
            "id": "x",
            "project_id": "y",
            "facts_json": {"power_demand": 100},
            "created_at": "t",
            "updated_at": "t",
        }
        resolve_project_facts(record)
        assert record == snapshot
