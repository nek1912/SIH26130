"""Shared project-facts resolution.

A project_facts row carries typed columns plus a facts_json JSONB extension
(migration 001). Extended regulatory facts (industry_type, plot_area_sqm,
production_capacity, groundwater_use, ...) live in facts_json because the
typed columns only cover entity_type/sector/jurisdictions/headcount/
annual_turnover_inr/incorporation_date/registered_state.

Both baseline orchestration and What-If must resolve facts through this one
function so they operate on exactly the same representation:

- facts_json (when a dict) is flattened first,
- typed top-level columns overlay it (DB-constrained values win),
- id/project_id/created_at/updated_at/facts_json metadata keys are dropped,
- None values are dropped so missing facts fail closed (UNKNOWN) instead of
  evaluating to FALSE inside the deterministic engine,
- inputs are never mutated.
"""
from __future__ import annotations

from typing import Any

from app.rules.derivations import DERIVATION_PROVENANCE, derive_mh_facts
from app.rules.facts import MH_JURISDICTION

_METADATA_KEYS = frozenset({"id", "project_id", "created_at", "updated_at", "facts_json"})


def resolve_project_facts(facts_record: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve a project_facts DB row into the flat facts dict for engines."""
    if not facts_record:
        return {}
    resolved: dict[str, Any] = {}
    raw_json = facts_record.get("facts_json")
    if isinstance(raw_json, dict):
        for key, value in raw_json.items():
            if value is not None:
                resolved[key] = value
    for key, value in facts_record.items():
        if key in _METADATA_KEYS:
            continue
        if value is None:
            continue
        resolved[key] = value
    return resolved


def apply_derived_facts(
    facts: dict[str, Any], jurisdiction: str
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Merge IN-MH derived facts into resolved project facts.

    Single derivation choke point for baseline orchestration (What-If,
    handoffs and rehearse all consume its output): ``derive_mh_facts``
    remains the only derivation implementation. Returns
    ``(merged_facts, provenance)`` where provenance carries one entry
    per derived fact (fact_id, derived=True, derivation function,
    source fact IDs, value). Facts absent from the provenance map are
    supplied facts. Non-IN-MH jurisdictions pass through unchanged
    with empty provenance, so IN-GJ behavior is byte-identical.
    """
    if jurisdiction != MH_JURISDICTION:
        return dict(facts), {}
    derived = derive_mh_facts(facts, jurisdiction)
    merged = dict(facts)
    merged.update(derived)
    provenance: dict[str, dict[str, Any]] = {}
    for key, value in derived.items():
        info = DERIVATION_PROVENANCE.get(key, {})
        provenance[key] = {
            "fact_id": key,
            "derived": True,
            "derivation": info.get("derivation", ""),
            "source_facts": list(info.get("source_facts", ())),
            "value": value,
        }
    return merged, provenance
