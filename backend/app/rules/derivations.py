"""IN-MH derived-fact computation (deterministic, evidence-gated).

Implements exactly the derivation semantics documented in the in-repo
v5 research CSVs. Nothing is invented; anything without documented
semantics fails closed to UNKNOWN (None).

- F-INC-01 (msme_class) := R-057 MSME_CLASS bands: MICRO if
  inv<=2.5 AND turnover<=10; SMALL if inv<=25 AND turnover<=100;
  MEDIUM if inv<=125 AND turnover<=500 (Rs crore); else LARGE.
  Either input missing/UNKNOWN/invalid -> None. (rules.csv /
  rule_register_v5.csv row R-057, SRC-061 GR MSME definition para;
  ET-040/041/042/112. R-057 itself is REQUIRES_OFFICIAL_CONFIRMATION
  with MEDIUM confidence on turnover limits — recorded here, not
  resolved here.)
- F-PRC-03 (is_MAH_under_MSIHC) := R-091 MAH_DERIVED join semantics:
  TRUE if any resolved inventory chemical has max_qty_t >= col3_t;
  FALSE only if every inventory chemical resolves (exact ``chemical``
  match in the supplied F-HAZ-02 mapping with a numeric col3_t) and
  none reaches col 3; otherwise None. Empty inventory -> False. The
  msihc_t1_thresholds table is evidence behind F-HAZ-02 values, never
  a runtime lookup (M2 identity source unselected; CON-021 thresholds
  unconfirmed). ET-127/ET-081/ET-v4-04/ET-v5-06. col 4 is the
  safety-report threshold, not MAH: ignored.
- F-INC-03 BLOCKED: INC-001 documents only "unit's sector falls in
  thrust sector #6" (SRC-061) with no input-fact mapping and no member
  list. F-INC-04 BLOCKED: R-058 is DO_NOT_IMPLEMENT_YET ("Annexure
  not digitised in this pack"); no taluka->basket table exists
  in-repo. Neither is ever produced here.

Contract: never overrides an explicitly supplied value (present keys
win, even when None); IN-MH only — IN-GJ raises
JURISDICTION_MISMATCH, anything else UNKNOWN_JURISDICTION.
"""
from __future__ import annotations

from typing import Any

from app.rules.facts import (
    GJ_JURISDICTION,
    MH_JURISDICTION,
    FactValidationError,
)

# R-057 bands, Rs crore, checked MICRO -> SMALL -> MEDIUM in order.
_MSME_BANDS: tuple[tuple[str, float, float], ...] = (
    ("MICRO", 2.5, 10.0),
    ("SMALL", 25.0, 100.0),
    ("MEDIUM", 125.0, 500.0),
)

# Provenance metadata for each derivable fact: the derivation function
# identifier and its source fact IDs. Used by the orchestration layer
# to explain derived values; never drives the derivation itself.
DERIVATION_PROVENANCE: dict[str, dict[str, Any]] = {
    "F-INC-01": {
        "derivation": "derive_msme_class",
        "source_facts": ("F-INC-02", "F-INC-09"),
    },
    "F-PRC-03": {
        "derivation": "derive_mah_status",
        "source_facts": ("F-HAZ-01", "F-HAZ-02"),
    },
}


def _is_number(value: Any) -> bool:
    """True for real numbers; bools are never quantities."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def derive_msme_class(
    investment_cr: Any, turnover_cr: Any
) -> str | None:
    """Derive F-INC-01 from F-INC-02 + F-INC-09 (R-057, AND per band).

    Returns MICRO/SMALL/MEDIUM/LARGE, or None (UNKNOWN) when either
    input is missing, "UNKNOWN", non-numeric, or negative.
    """
    if not _is_number(investment_cr) or not _is_number(turnover_cr):
        return None
    if investment_cr < 0 or turnover_cr < 0:
        return None
    for label, inv_cap, turnover_cap in _MSME_BANDS:
        if investment_cr <= inv_cap and turnover_cr <= turnover_cap:
            return label
    return "LARGE"


def derive_mah_status(
    inventory: Any, schedule_mapping: Any
) -> bool | None:
    """Derive F-PRC-03 from F-HAZ-01 + F-HAZ-02 (R-091 semantics).

    Exact ``chemical``-string join only — no fuzzy/CAS identity
    resolution (M2 unselected). TRUE dominates; FALSE requires every
    item resolved with none reaching col 3; anything else is None.
    """
    if not isinstance(inventory, list) or not isinstance(
        schedule_mapping, list
    ):
        return None
    if not inventory:
        return False
    col3: dict[str, float] = {}
    for entry in schedule_mapping:
        if not isinstance(entry, dict):
            continue
        name = entry.get("chemical")
        threshold = entry.get("col3_t")
        if (
            isinstance(name, str)
            and _is_number(threshold)
            and threshold >= 0
            and name not in col3
        ):
            col3[name] = threshold
    all_resolved = True
    for item in inventory:
        if not isinstance(item, dict) or not isinstance(
            item.get("chemical"), str
        ):
            all_resolved = False
            continue
        qty = item.get("max_qty_t")
        threshold = col3.get(item["chemical"])
        if not _is_number(qty) or qty < 0 or threshold is None:
            all_resolved = False
            continue
        if qty >= threshold:
            return True
    return False if all_resolved else None


def derive_mh_facts(
    facts: dict[str, Any], jurisdiction: str = MH_JURISDICTION
) -> dict[str, Any]:
    """Derive missing IN-MH derived facts from supplied source facts.

    Returns {F-INC-01, F-PRC-03} values only for keys absent from
    ``facts``; supplied values (including None) are never overridden.
    F-INC-03/F-INC-04 are never produced (blocked, see module note).
    Inputs are never mutated.
    """
    if jurisdiction == MH_JURISDICTION:
        pass
    elif jurisdiction == GJ_JURISDICTION:
        raise FactValidationError(
            "jurisdiction",
            "derived-fact computation is IN-MH only, not IN-GJ",
            FactValidationError.JURISDICTION_MISMATCH,
        )
    else:
        raise FactValidationError(
            "jurisdiction",
            f"unknown jurisdiction {jurisdiction!r}",
            FactValidationError.UNKNOWN_JURISDICTION,
        )
    derived: dict[str, Any] = {}
    if "F-INC-01" not in facts:
        msme = derive_msme_class(facts.get("F-INC-02"), facts.get("F-INC-09"))
        if msme is not None:
            derived["F-INC-01"] = msme
    if "F-PRC-03" not in facts:
        mah = derive_mah_status(facts.get("F-HAZ-01"), facts.get("F-HAZ-02"))
        if mah is not None:
            derived["F-PRC-03"] = mah
    return derived
