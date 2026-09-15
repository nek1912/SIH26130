"""Scenario_Profile facts from the frozen workbook.

These are the reusable stress-test inputs defined in the workbook.
They are NOT general regulatory rules — they are test scenario values.
"""
from __future__ import annotations

from typing import Any


def load_scenario() -> dict[str, Any]:
    """Return the scenario facts dict from the workbook."""
    return dict(SCENARIO_FACTS)


SCENARIO_FACTS: dict[str, Any] = {
    "state": "Gujarat",
    "estate": "Dahej-II",
    "district": "Bharuch",
    "taluka": "Vagra",
    "plot_area_sqm": 12000,
    "builtup_area_sqm": 5000,
    "industry_type": "synthetic organic / specialty chemical manufacturing",
    "new_project": True,
    "production_capacity": 20000,
    "raw_materials": [
        "Methanol",
        "Toluene",
        "Ethylene dichloride (EDC)",
        "Tetrahydrofuran (THF)",
        "Nitrobenzene",
    ],
    "hazardous_chemicals_handled": True,
    "hazardous_chemical_list": [
        "Methanol",
        "Toluene",
        "Ethylene dichloride (EDC)",
        "Tetrahydrofuran (THF)",
        "Nitrobenzene",
    ],
    "max_storage_by_chemical": {
        "Methanol": "25 MT",
        "Toluene": "20 MT",
        "EDC": "15 MT",
        "THF": "10 MT",
        "Nitrobenzene": "10 MT",
    },
    "hazardous_waste_generated": True,
    "hazardous_waste_streams": [
        "Spent organic solvent/residue",
        "ETP sludge",
        "contaminated containers/liners",
        "process residue",
    ],
    "water_source": "GIDC industrial water",
    "fresh_water_requirement": 100,
    "process_water": 70,
    "domestic_water": 30,
    "effluent_generation": 70,
    "ETP_capacity": 80,
    "discharge_mode": "GIDC drainage + treatment/reuse",
    "power_demand": 1000,
    "connection_type": "HT",
    "DG_capacity": 750,
    "workers_total": 60,
    "workers_powered_factory": 60,
    "hazardous_process": True,
    "building_height": 18,
    "fire_safety_certificate_candidate": True,
    "lift_present": True,
    "boiler_present": True,
    "petroleum_or_licensed_storage": "Conditional",
    "groundwater_use": False,
    "tree_felling": False,
    "forest_or_protected_area_overlap": "UNRESOLVED_AT_PLOT_LEVEL",
    "critical_pollution_area_status": "UNRESOLVED_AT_PLOT_LEVEL",
    "coastal_regulation_zone_status": "UNRESOLVED_AT_PLOT_LEVEL",
    "notified_industrial_area": "UNRESOLVED_AT_PLOT_LEVEL",
    "legal_entity": "Pvt Ltd",
    "electricity_license_area": "UNRESOLVED_AT_PLOT_LEVEL",
    "village": "Dahej",
    "pin_code": "392130",
}
