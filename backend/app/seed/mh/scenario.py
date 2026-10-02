"""Canonical Maharashtra industrial chemical project demo scenario.

DATA/INTEGRATION ONLY.
Defines one fixed, deterministic Maharashtra chemical-industry project scenario
(Sahyadri Specialty Chemicals Pvt. Ltd., located in MIDC Kurkumbh, Taluka Daund,
District Pune) designed to demonstrate the complete PS 26130 applicant journey.

Uses ONLY currently verified IN-MH rules, facts, dependencies, document
requirements, sources, and portal catalog entries without modifying rule
engine semantics or inventing regulatory data.
"""
from __future__ import annotations

from typing import Any

CANONICAL_MH_PROJECT_META: dict[str, Any] = {
    "name": "Sahyadri Specialty Chemicals Pvt. Ltd.",
    "description": (
        "Greenfield synthetic organic chemical and pesticide intermediate "
        "manufacturing facility in MIDC Kurkumbh, Taluka Daund, District Pune, "
        "Maharashtra."
    ),
    "entity_type": "pvt-ltd",
    "sector": "chemical",
    "jurisdictions": ["IN-MH"],
    "headcount": 60,
    "annual_turnover_inr": 500_000_000.0,  # Rs. 50 crore
}

# Raw input facts supplied by the applicant.
# Every key and value strictly adheres to the 128 registered IN-MH fact specs.
# Missing/unknown facts are omitted (fail-closed to None/UNKNOWN per registry design).
CANONICAL_MH_SCENARIO_FACTS: dict[str, Any] = {
    # --- Location & Site ---
    "F-LOC-01": True,  # site_in_midc_estate (MIDC Kurkumbh)
    "F-LOC-04": "Daund",  # taluka
    "F-LOC-05": "MIDC",  # planning_authority
    "F-LOC-11": "Pune",  # district
    "F-LOC-12": "MIDC Kurkumbh",  # industrial_estate_name
    "F-LOC-15": False,  # forest_land_involved
    "F-GEO-01": "NOT_IN_CRZ",  # CRZ_category_of_site
    "F-SITE-01": False,  # trees_to_fell
    # --- Products & Processes ---
    "F-PRD-01": True,  # product_in_EIA_5f_scope (synthetic organic chemicals)
    "F-PRD-02": ["PESTICIDE_TECHNICAL"],  # product_type_special
    "F-PRD-03": "SYNTHESIS",  # process_mode
    "F-PRC-01": 10.0,  # water_consumption_m3_per_day (< 25 m3/day small-unit test)
    "F-PRC-02": 10.0,  # fuel_consumption_tpd (< 25 tpd small-unit test)
    "F-BLD-01": 12000.0,  # total_built_up_area_m2 (< 20,000 m2 threshold for 8(a))
    "F-BLD-03": 2.5,  # project_area_ha (< 50 ha threshold for 8(b))
    # --- Hazardous Chemicals & MSIHC (drives F-PRC-03 derivation) ---
    "F-HAZ-01": [
        {
            "chemical": "Toluene",
            "cas": "108-88-3",
            "max_qty_t": 20.0,
            "storage_type": "PROCESS",
        }
    ],
    "F-HAZ-02": [
        {
            "chemical": "Toluene",
            "schedule": "Sch 3 Part I",
            "col3_t": 200.0,
            "col4_t": 2000.0,
        }
    ],
    # --- Petroleum Storage (PESO Class B) ---
    "F-PET-01": "B",  # petroleum_class B (flash point 23°C - 65°C)
    "F-PET-02": 2000.0,  # petroleum_qty_litres (2,000 L <= 2,500 L limit)
    "F-PET-04": 900.0,  # max_receptacle_litres (900 L <= 1,000 L limit)
    # --- Utilities, Water & Boiler ---
    "F-WAT-01": ["MIDC"],  # water_source (MIDC piped supply)
    "F-WAT-02": True,  # effluent_generated
    "F-WAT-03": "CETP",  # discharge_mode (conveyance to Kurkumbh CETP)
    "F-WAT-05": 0.0,  # groundwater_abstraction_m3_per_day (zero extraction)
    "F-WAT-08": False,  # construction_dewatering
    "F-GW-01": "SAFE",  # CGWB_assessment_unit_category (safe assessment unit)
    "F-BLR-04": False,  # steam_generated_for_external_use (no commercial steam)
    # --- Labour & Factory Operations ---
    "F-LAB-01": 60,  # max_workers_any_day_prev_12_months
    "F-LAB-02": True,  # manufacturing_with_power
    "F-LAB-03": 60,  # max_contract_labour (>= 50 threshold for s.45(2))
    "F-LAB-07": True,  # hazardous_process_first_schedule
    "F-LAB-08": 0,  # interstate_migrant_workers (< 10)
    "F-LAB-09": False,  # work_intermittent_or_casual_only (regular manufacturing)
    # --- Waste Management & Environment ---
    "F-HW-01": True,  # hw_generated (hazardous waste generation trigger)
    "F-HW-03": False,  # hw_utilisation_or_recovery (no on-site utilization)
    "F-EEE-01": 50.0,  # units_of_Schedule_I_EEE_used_in_FY (< 1,000 units)
    # --- Expansion & Incentives (drives F-INC-01 derivation) ---
    "F-EXP-01": False,  # is_expansion_or_modernisation (fresh greenfield)
    "F-INC-02": 15.0,  # pm_investment_cr (Rs. 15 cr, <= 25 cr for SMALL)
    "F-INC-09": 50.0,  # turnover_cr (Rs. 50 cr, <= 100 cr for SMALL)
    # --- Other Regulatory Regimes ---
    "F-INS-01": False,  # manufactures_insecticide (technical material, not end-use)
    "F-TRN-01": False,  # consigns_CMVR_Table_III_goods_by_road
}

# The expected outcomes for all 20 active approvals in the IN-MH pack.
# Recorded strictly against the verified rule definitions and deterministic engine.
CANONICAL_MH_EXPECTED_ASSESSMENTS: dict[str, dict[str, Any]] = {
    "APR-001": {
        "approval_id": "APR-001",
        "rule_id": "R-002",
        "authority": "AUT-001 (Cat A) / AUT-002 (Cat B)",
        "source_ref": "SRC-001 Item 5(f) column 5",
        "expected_applicability": "insufficient_data",
        "expected_readiness": "insufficient_data",
        "dependency": None,
        "documents": [],
        "notes": (
            "R-002 is CLASSIFICATION (small-unit). With R-001 deferred, "
            "no active trigger exists; composes to INSUFFICIENT_DATA. "
            "Evidence gap UR-06 attaches advisory blocker."
        ),
    },
    "APR-003": {
        "approval_id": "APR-003",
        "rule_id": "R-007",
        "authority": "AUT-002",
        "source_ref": "SRC-001 Item 8(a); SRC-179 Item 8(a)",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Built-up area 12,000 m2 < 20,000 m2 threshold.",
    },
    "APR-004": {
        "approval_id": "APR-004",
        "rule_id": "R-009",
        "authority": "AUT-002",
        "source_ref": "SRC-001 Item 8(b)",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Plot area 2.5 ha < 50 ha and built-up area 12,000 m2 < 150,000 m2.",
    },
    "APR-006": {
        "approval_id": "APR-006",
        "rule_id": "R-011",
        "authority": "AUT-001",
        "source_ref": "SRC-001 Item 5(b)",
        "expected_applicability": "applies",
        "expected_readiness": "ready",
        "dependency": None,
        "documents": [],
        "portal_id": "POR-001",
        "portal_name": "MoEFCC / PARIVESH",
        "portal_url": "https://parivesh.nic.in/",
        "notes": (
            "Prior EC for pesticide technical intermediate manufacturing. "
            "Triggers via F-PRD-02. Zero blockers; fully handoff-ready."
        ),
    },
    "APR-007": {
        "approval_id": "APR-007",
        "rule_id": "R-012",
        "authority": "AUT-002",
        "source_ref": "SRC-001 Item 5(h)",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Unit does not manufacture integrated paint products.",
    },
    "APR-010": {
        "approval_id": "APR-010",
        "rule_id": "R-018",
        "authority": "AUT-003",
        "source_ref": "SRC-013 Rule 6(1)",
        "expected_applicability": "applies",
        "expected_readiness": "blocked_by_dependency",
        "dependency": "APR-008 (Consent to Establish), APR-009 (Consent to Operate)",
        "documents": ["DOC-001", "DOC-002", "DOC-003"],
        "portal_id": "POR-002",
        "portal_name": "MPCB ecMPCB consent system",
        "portal_url": "https://mpcb.gov.in/en/consent-status",
        "notes": (
            "Hazardous waste authorisation triggered by F-HW-01=True. "
            "Blocked by document prerequisites APR-008 and APR-009 via DEP-009. "
            "When dependencies are satisfied, status transitions to blocked_by_documents."
        ),
    },
    "APR-019": {
        "approval_id": "APR-019",
        "rule_id": "R-026",
        "authority": "AUT-006",
        "source_ref": "SRC-081 OSH Code 2020 s.45(2); SRC-026 OSH Code 2020 s.45(2)",
        "expected_applicability": "applies",
        "expected_readiness": "ready",
        "dependency": None,
        "documents": [],
        "portal_id": "POR-005",
        "portal_name": "Maharashtra Labour Department",
        "portal_url": "https://labour.maharashtra.gov.in/en/rts/rts-services",
        "notes": (
            "Registration of principal employer under OSH Code 2020 s.45(2). "
            "Triggered by F-LAB-03=60 (>= 50) and F-LAB-09=False. Status is ready."
        ),
    },
    "APR-022": {
        "approval_id": "APR-022",
        "rule_id": "R-089",
        "authority": "AUT-006",
        "source_ref": "SRC-081 s.59",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Inter-state migrant workers count F-LAB-08=0 (< 10).",
    },
    "APR-023": {
        "approval_id": "APR-023",
        "rule_id": "R-028",
        "authority": "AUT-007",
        "source_ref": "SRC-034 Boilers Act 2025 s.2(c)",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "No steam generated for external use (F-BLR-04=False).",
    },
    "APR-026": {
        "approval_id": "APR-026",
        "rule_id": "R-030",
        "authority": "AUT-008 / AUT-009",
        "source_ref": "SRC-092 Petroleum Act 1934 s.7(i); SRC-017 PESO SOP exemptions table",
        "expected_applicability": "applies",
        "expected_readiness": "blocked_by_documents",
        "dependency": None,
        "documents": ["DOC-008"],
        "portal_id": "POR-007",
        "portal_name": "PESO Online",
        "portal_url": "https://online.peso.gov.in/PesoOnline/",
        "notes": (
            "Petroleum Class B storage licence evaluated under R-030 "
            "(TRIGGER, retained per STOP verdict). Canonical facts satisfy "
            "the Class-B triple, so APR-026 APPLIES; DOC-008 is required and "
            "unuploaded, so readiness is BLOCKED_BY_DOCUMENTS."
        ),
    },
    "APR-029": {
        "approval_id": "APR-029",
        "rule_id": "R-035",
        "authority": "AUT-010",
        "source_ref": "SRC-043",
        "expected_applicability": "applies",
        "expected_readiness": "ready",
        "dependency": None,
        "documents": [],
        "portal_id": "POR-008G",
        "portal_name": "MIDC GIS map service",
        "portal_url": (
            "https://gis.midcindia.org/server/rest/services/"
            "CitizenPortal/MIDC_PUBLIC_MAIN_MAP_SERVICE/MapServer"
        ),
        "notes": "MIDC estate plot-holder branch guard (F-LOC-01=True).",
    },
    "APR-043": {
        "approval_id": "APR-043",
        "rule_id": "R-077",
        "authority": "AUT-013",
        "source_ref": "SRC-052 para 4.1",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": (
            "Assessment unit F-GW-01=SAFE (not OVER_EXPLOITED); composite trigger "
            "R-077 is FALSE. Status is not_applicable."
        ),
    },
    "APR-044": {
        "approval_id": "APR-044",
        "rule_id": "R-046",
        "authority": "AUT-013",
        "source_ref": "SRC-052",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "No construction dewatering (F-WAT-08=False).",
    },
    "APR-054": {
        "approval_id": "APR-054",
        "rule_id": "R-056",
        "authority": "AUT-003 (CPCB approval if no SOP)",
        "source_ref": "SRC-013 Rule 9",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "No on-site HW utilisation/recovery (F-HW-03=False).",
    },
    "APR-055": {
        "approval_id": "APR-055",
        "rule_id": "R-067",
        "authority": "Licensing officer (State; identity in MH UNKNOWN)",
        "source_ref": "SRC-100 s.13",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Unit does not manufacture finished insecticides (F-INS-01=False).",
    },
    "CMP-018": {
        "approval_id": "CMP-018",
        "rule_id": "R-070",
        "authority": "",
        "source_ref": "SRC-081 s.22(2)",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Worker count 60 < 250 statutory threshold for hazardous process.",
    },
    "CMP-024": {
        "approval_id": "CMP-024",
        "rule_id": "R-093",
        "authority": "",
        "source_ref": "SRC-102 r.131",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Unit does not consign CMVR Table III goods by road (F-TRN-01=False).",
    },
    "CMP-025": {
        "approval_id": "CMP-025",
        "rule_id": "R-094",
        "authority": "",
        "source_ref": "SRC-135 r.3; r.8",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Bulk E-waste count F-EEE-01=50 (< 1,000 units).",
    },
    "LOC-CRZ": {
        "approval_id": "LOC-CRZ",
        "rule_id": "R-083",
        "authority": "MCZMA / MoEFCC",
        "source_ref": "SRC-112 paras 4(i), 4(ii), 4(xi)",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "Inland site outside coastal regulation zone (F-GEO-01=NOT_IN_CRZ).",
    },
    "LOC-FOREST": {
        "approval_id": "LOC-FOREST",
        "rule_id": "R-084",
        "authority": "MoEFCC / Regional Office / State Forest Dept",
        "source_ref": "SRC-113 r.9, r.10",
        "expected_applicability": "does_not_apply",
        "expected_readiness": "not_applicable",
        "dependency": None,
        "documents": [],
        "notes": "No forest land diversion involved (F-LOC-15=False).",
    },
}


def load_canonical_mh_scenario() -> dict[str, Any]:
    """Return a copy of the canonical Maharashtra scenario facts."""
    return dict(CANONICAL_MH_SCENARIO_FACTS)


def load_canonical_mh_project_meta() -> dict[str, Any]:
    """Return a copy of the canonical Maharashtra project metadata."""
    return dict(CANONICAL_MH_PROJECT_META)


def load_canonical_mh_expected_assessments() -> dict[str, dict[str, Any]]:
    """Return a copy of the expected assessment outcomes for all approvals."""
    return {k: dict(v) for k, v in CANONICAL_MH_EXPECTED_ASSESSMENTS.items()}
