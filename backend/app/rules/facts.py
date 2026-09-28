"""Jurisdiction-scoped fact registry (Phase 2).

Code-defined transcription of the Maharashtra v5 ``facts.csv`` research
artifact (``UdyamDwaar MH Chemical Pack``): 128 ACTIVE/VERIFIED facts
for jurisdiction IN-MH. ``F-BLD-02`` (DEPRECATED / DO_NOT_IMPLEMENT_YET)
is excluded and reported explicitly instead of being silently dropped.

Registry principle (from the artifact notes): UNKNOWN is always a
permitted value and is never coerced to FALSE. ``None`` (or an absent
key) means missing/unknown and is always valid input — missing is not
invalid. Supplied values that violate the spec are rejected.

No v5 rule conditions are encoded here. No CSV is read at runtime.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any

from app.rules.validation import ALLOWED_FIELDS

MH_JURISDICTION = "IN-MH"
GJ_JURISDICTION = "IN-GJ"

_UNKNOWN_TOKEN = "UNKNOWN"

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class FactValueType(StrEnum):
    """Machine value types for registry facts (not CSV display strings)."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    DATE = "date"
    ENUM = "enum"
    ENUM_SET = "enum_set"
    LIST = "list"
    OBJECT = "object"


@dataclass(frozen=True)
class FactSpec:
    """One jurisdiction-scoped fact definition."""

    key: str
    jurisdiction: str
    label: str
    value_type: FactValueType
    unit: str | None = None
    allowed_values: tuple[str, ...] = ()
    unknown_allowed: bool = False
    derived: bool = False
    group: str = ""
    description: str = ""
    used_in: tuple[str, ...] = ()


class FactValidationError(ValueError):
    """Explicit, machine-readable fact validation failure."""

    UNKNOWN_FIELD = "unknown_field"
    JURISDICTION_MISMATCH = "jurisdiction_mismatch"
    WRONG_TYPE = "wrong_type"
    INVALID_ENUM = "invalid_enum"
    INVALID_DATE = "invalid_date"
    DO_NOT_IMPLEMENT = "do_not_implement"
    UNKNOWN_JURISDICTION = "unknown_jurisdiction"

    def __init__(self, field: str, reason: str, code: str) -> None:
        self.field = field
        self.reason = reason
        self.code = code
        super().__init__(f"Invalid fact '{field}': {reason} [{code}]")


def _F(
    key: str,
    label: str,
    value_type: FactValueType,
    *,
    unit: str | None = None,
    allowed: tuple[str, ...] = (),
    unknown: bool = False,
    derived: bool = False,
    group: str = "",
    desc: str = "",
    used: tuple[str, ...] = (),
) -> FactSpec:
    return FactSpec(
        key=key,
        jurisdiction=MH_JURISDICTION,
        label=label,
        value_type=value_type,
        unit=unit,
        allowed_values=allowed,
        unknown_allowed=unknown,
        derived=derived,
        group=group,
        description=desc,
        used_in=used,
    )


B = FactValueType.BOOLEAN
I = FactValueType.INTEGER  # noqa: E741
N = FactValueType.NUMBER
S = FactValueType.STRING
D = FactValueType.DATE
E = FactValueType.ENUM
ES = FactValueType.ENUM_SET
L = FactValueType.LIST
O = FactValueType.OBJECT  # noqa: E741

_MH_FACT_LIST: list[FactSpec] = [
    _F("F-LOC-01", "site_in_midc_estate", B, unknown=True, group="LOC",
       desc="Can be checked against MIDC GIS (POR-008G)",
       used=("MIDC vs non-MIDC branch",)),
    _F("F-LOC-02",
       "site_in_notified_industrial_area_or_estate (EIA sense)", B,
       unknown=True, group="LOC",
       desc=("MIDC estate is not automatically 'notified' for EIA "
             "purposes - confirm"),
       used=("EIA 5(f) A/B",)),
    _F("F-LOC-03", "estate_holds_prior_EC_covering_units", B,
       unknown=True, group="LOC", used=("EIA SC",)),
    _F("F-LOC-04", "taluka", S, group="LOC",
       desc="Map via IISP Annexure 1", used=("Incentive basket",)),
    _F("F-LOC-05", "planning_authority", E, group="LOC",
       allowed=("MIDC", "MUNICIPAL_CORP:<name>",
                "MUNICIPAL_COUNCIL:<name>", "NAGAR_PANCHAYAT:<name>",
                "SPA:<name>", "RP_AREA_COLLECTOR", "GAOTHAN_PANCHAYAT",
                "UNKNOWN"),
       used=("R-041", "R-078", "R-080", "R-082")),
    _F("F-LOC-06", "urban_area", B, unknown=True, group="LOC",
       used=("Tree Act",)),
    _F("F-LOC-07",
       "gc_within_5km (protected area / CPCB critically polluted area / "
       "ESZ / inter-state or international boundary)", O, unknown=True,
       group="LOC", desc="Four sub-facts", used=("EIA GC",)),
    _F("F-LOC-08", "distribution_licence_area", E, group="LOC",
       allowed=("MSEDCL", "TATA_POWER", "AEML", "BEST",
                "TORRENT_FRANCHISE", "OTHER", "UNKNOWN"),
       used=("Electricity",)),
    _F("F-PRD-01", "product_in_EIA_5f_scope", B, unknown=True,
       group="PRD",
       desc="Expert/appraisal classification; never inferred from name",
       used=("EC",)),
    _F("F-PRD-02", "product_type_special", ES, group="PRD",
       allowed=("PESTICIDE_TECHNICAL", "BULK_DRUG", "DYE_INTERMEDIATE",
                "PAINT_INTEGRATED", "NONE", "UNKNOWN"),
       used=("EC 5(b)/5(h)", "conditional regs")),
    _F("F-PRD-03", "process_mode", E, group="PRD",
       allowed=("SYNTHESIS", "FORMULATION_ONLY", "BLENDING_ONLY", "MIXED",
                "UNKNOWN"),
       used=("MPCB sector code", "EC")),
    _F("F-PRD-04", "special_substance_flags", ES, group="PRD",
       allowed=("EXPLOSIVE", "NDPS", "CWC", "ODS", "EXCISE", "NONE",
                "UNKNOWN"),
       desc="All not researched", used=("Conditional regs",)),
    _F("F-PRC-01", "water_consumption_m3_per_day", N, unit="m3/day",
       group="PRC", used=("EIA small-unit exception",)),
    _F("F-PRC-02", "fuel_consumption_tpd", N, unit="tonnes/day",
       group="PRC", used=("EIA small-unit exception",)),
    _F("F-PRC-03", "is_MAH_under_MSIHC", B, derived=True, group="PRC",
       desc="Derived from F-HAZ-01",
       used=("EIA small-unit exception", "DISH category")),
    _F("F-PRC-04", "dg_set_present", B, unknown=True, group="PRC",
       used=("MPCB",)),
    _F("F-MPCB-01", "cpcb_sector_codes", L, group="MPCB",
       desc="Per activity, e.g. 111.1,111.2,42.1,76",
       used=("MPCB category",)),
    _F("F-BLD-01", "total_built_up_area_m2", N, unit="m2", group="BLD",
       used=("EIA 8(a)/8(b)",)),
    _F("F-BLD-03", "project_area_ha", N, unit="ha", group="BLD",
       used=("EIA 8(b)",)),
    _F("F-HAZ-01", "hazardous_chemical_inventory", L, group="HAZ",
       desc="[{chemical, cas, max_qty_t, storage_type ISOLATED/PROCESS}]",
       used=("MSIHC",)),
    _F("F-HAZ-02", "msihc_schedule_mapping", L, group="HAZ",
       desc="Must be sourced from Sch 2/3; "
            "[{chemical, schedule, col3_t, col4_t}]",
       used=("MSIHC",)),
    _F("F-PET-01", "petroleum_class", E, group="PET",
       allowed=("A", "B", "C", "NOT_PETROLEUM", "UNKNOWN"),
       desc="Flash point basis", used=("PESO",)),
    _F("F-PET-02", "petroleum_qty_litres", N, unit="L", group="PET",
       desc="Quantity per class", used=("PESO",)),
    _F("F-PET-03", "storage_mode", E, group="PET",
       allowed=("BULK", "NON_BULK"), used=("PESO",)),
    _F("F-PET-04", "max_receptacle_litres", N, unit="L", group="PET",
       used=("PESO exemptions",)),
    _F("F-GAS-01", "gas_cylinder_inventory", L, group="GAS",
       desc="[{gas, n_cylinders, kg}]", used=("GCR",)),
    _F("F-GAS-02", "lpg_own_use_kg", N, unit="kg", group="GAS",
       used=("GCR r.44",)),
    _F("F-PV-01", "pressure_vessels", L, group="PV",
       desc="[{water_capacity_L, gas, is_process_vessel}]",
       used=("SMPV",)),
    _F("F-PV-02", "cryogenic_vessel", B, group="PV", used=("SMPV",)),
    _F("F-BLR-01", "boiler_volume_L", N, unit="L", group="BLR",
       used=("Boilers Act",)),
    _F("F-BLR-02", "boiler_pressure_kgcm2", N, unit="kg/cm2",
       group="BLR", used=("Boilers Act",)),
    _F("F-BLR-03", "boiler_water_temp_C", N, unit="C", group="BLR",
       used=("Boilers Act",)),
    _F("F-WAT-01", "water_source", ES, group="WAT",
       allowed=("MIDC", "MUNICIPAL", "GROUNDWATER", "SURFACE", "TANKER",
                "UNKNOWN"),
       used=("Water approvals",)),
    _F("F-WAT-02", "effluent_generated", B, unknown=True, group="WAT",
       used=("Consent",)),
    _F("F-WAT-03", "discharge_mode", E, group="WAT",
       allowed=("CETP", "ZLD", "SEWER", "SURFACE", "UNKNOWN"),
       used=("Consent/MIDC drainage",)),
    _F("F-WAT-04", "cetp_available_and_accepting", B, unknown=True,
       group="WAT", desc="Never default TRUE", used=("CETP",)),
    _F("F-WAT-05", "groundwater_abstraction_m3_per_day", N,
       unit="m3/day", group="WAT", used=("CGWA",)),
    _F("F-WAT-06", "groundwater_purpose", E, group="WAT",
       allowed=("INDUSTRIAL", "DOMESTIC_ONLY", "BOTH"), used=("CGWA",)),
    _F("F-WAT-07", "surface_water_drawal", B, unknown=True,
       group="WAT", used=("WRD",)),
    _F("F-WAT-08", "construction_dewatering", B, unknown=True,
       group="WAT", used=("CGWA",)),
    _F("F-WAT-09", "assessment_unit_category", E, group="WAT",
       allowed=("SAFE", "SEMI_CRITICAL", "CRITICAL", "OVER_EXPLOITED",
                "UNKNOWN"),
       used=("CGWA",)),
    _F("F-ELE-01", "connection_voltage_kV", N, unit="kV", group="ELE",
       used=("Electrical inspection",)),
    _F("F-ELE-02", "state_notified_self_cert_voltage_kV", N,
       unit="kV", unknown=True, group="ELE",
       desc="Value UNKNOWN (UNK-005)", used=("Electrical inspection",)),
    _F("F-ELE-03", "connected_load_kW", N, unit="kW", group="ELE",
       used=("Connection",)),
    _F("F-LFT-01", "lift_count", I, group="LFT", used=("Lifts",)),
    _F("F-LAB-01", "max_workers_any_day_prev_12_months", I,
       group="LAB", used=("Factory threshold",)),
    _F("F-LAB-02", "manufacturing_with_power", B, group="LAB",
       used=("Factory threshold",)),
    _F("F-LAB-03", "max_contract_labour", I, group="LAB",
       used=("Contract labour",)),
    _F("F-LAB-04", "is_contractor", B, group="LAB",
       used=("Contractor licence",)),
    _F("F-LAB-05", "construction_workers", I, group="LAB",
       desc="Threshold unverified", used=("BOCW",)),
    _F("F-LAB-06", "total_employees", I, group="LAB",
       used=("OSH registration",)),
    _F("F-HW-01", "hw_generated", B, unknown=True, group="HW",
       used=("HW authorisation",)),
    _F("F-HW-02", "hw_streams", L, group="HW",
       desc="Entry numbers must be supplied, not inferred; "
            "[{description, schedule, entry_no, qty_tpa}]",
       used=("HW",)),
    _F("F-HW-03", "hw_utilisation_or_recovery", B, unknown=True,
       group="HW", used=("HW r.9",)),
    _F("F-SITE-01", "trees_to_fell", B, unknown=True, group="SITE",
       used=("Tree permission",)),
    _F("F-EXP-01", "is_expansion_or_modernisation", B, group="EXP",
       used=("EC 7(ii)", "MPCB")),
    _F("F-EXP-02", "pollution_load_increase", B, unknown=True,
       group="EXP", used=("EC 7(ii)(b)",)),
    _F("F-INC-01", "msme_class", E, derived=True, group="INC",
       allowed=("MICRO", "SMALL", "MEDIUM", "LARGE", "UNKNOWN"),
       desc="Requires both investment AND turnover",
       used=("Incentives",)),
    _F("F-INC-02", "pm_investment_cr", N, unit="Rs crore", group="INC",
       used=("MSME class",)),
    _F("F-INC-03", "sector_thrust_flag", B, derived=True, group="INC",
       used=("Incentives",)),
    _F("F-INC-04", "taluka_basket", E, derived=True, group="INC",
       allowed=("A", "B", "C", "D", "D+", "SPECIAL_REGION",
                "NO_INDUSTRY_NAXAL_ASPIRATIONAL", "UNKNOWN"),
       desc="From taluka via Annexure 1", used=("Incentives",)),
    _F("F-INC-05", "export_share_pct", N, unit="%", group="INC",
       used=("Capital subsidy / ED",)),
    _F("F-INC-06", "ownership_category", E, group="INC",
       allowed=("WOMEN", "SC", "ST", "PWD", "GENERAL", "UNKNOWN"),
       used=("Incentives",)),
    _F("F-INC-07", "women_staff_share_pct", N, unit="%", group="INC",
       used=("Capital subsidy",)),
    _F("F-INC-08", "fci_cr_and_direct_jobs", O, group="INC",
       desc="Pair: Rs crore and direct job count",
       used=("LSI thresholds",)),
    _F("F-INC-09", "turnover_cr", N, unit="Rs crore", group="INC",
       used=("MSME class",)),
    _F("F-OTH-01", "sells_prepackaged_commodities", B, unknown=True,
       group="OTH", used=("Legal metrology",)),
    _F("F-OTH-02", "within_aerodrome_height_zone", B, unknown=True,
       group="OTH", used=("AAI",)),
    _F("F-OTH-03", "annual_energy_consumption_toe", N, unit="toe",
       group="OTH", desc="Applicability UNKNOWN", used=("EC Act",)),
    _F("F-OTH-04", "transports_hazardous_goods", B, unknown=True,
       group="OTH", used=("CMVR",)),
    _F("F-OTH-05", "epr_role", ES, group="OTH",
       allowed=("PIBO", "BATTERY", "EWASTE", "NONE", "UNKNOWN"),
       used=("EPR",)),
    _F("F-LOC-09", "site_coordinates", O, unknown=True, group="LOC",
       desc="lat,lon (WGS84)",
       used=("GC distances", "CRZ", "ESZ", "AAI")),
    _F("F-LOC-10", "in_estate_notified_for_consent_guidelines", B,
       unknown=True, group="LOC", used=("R-016 deemed CTE",)),
    _F("F-LOC-11", "district", S, unknown=True, group="LOC",
       used=("Authorities", "incentives")),
    _F("F-LOC-12", "industrial_estate_name", S, unknown=True,
       group="LOC", used=("Estate EC", "CETP")),
    _F("F-LOC-13", "gc_distances_km", O, unknown=True, group="LOC",
       desc="km each: protected_area, cpa, esa, interstate_boundary",
       used=("EIA GC (whole or part within 5 km)",)),
    _F("F-LOC-14", "in_crz", B, unknown=True, group="LOC",
       used=("CRZ",)),
    _F("F-LOC-15", "forest_land_involved", B, unknown=True,
       group="LOC", used=("Van Adhiniyam",)),
    _F("F-LOC-16", "in_esz_or_wildlife_area", B, unknown=True,
       group="LOC", used=("WLPA / ESZ",)),
    _F("F-LOC-17", "structure_height_m_amsl", N, unit="m",
       unknown=True, group="LOC", used=("AAI height NOC",)),
    _F("F-LOC-18", "plot_area_m2 / land_tenure", O, unknown=True,
       group="LOC", desc="m2 plus MIDC_LEASE/OWNED/LEASED/UNKNOWN",
       used=("MIDC", "planning")),
    _F("F-PRD-05", "products", L, unknown=True, group="PRD",
       desc="[{name, CAS, product_family, capacity_tpa}]",
       used=("EIA scope", "CWC", "CPCB code")),
    _F("F-PRD-06", "raw_materials", L, unknown=True, group="PRD",
       desc="[{name, CAS, hazard_class, max_inventory_t}]",
       used=("MSIHC", "PESO", "NDPS")),
    _F("F-HAZ-03", "storage_units", L, unknown=True, group="HAZ",
       desc="[{chemical, mode TANK/DRUM/CYLINDER/VESSEL, capacity, "
            "location_group}]",
       used=("MSIHC aggregation", "PESO")),
    _F("F-GAS-03", "gas_type_group", E, unknown=True, group="GAS",
       allowed=("FLAMMABLE_NONTOXIC", "NONFLAMMABLE_NONTOXIC", "TOXIC",
                "DISSOLVED_ACETYLENE", "LPG"),
       used=("GCR r.44",)),
    _F("F-BLR-04", "steam_generated_for_external_use", B,
       unknown=True, group="BLR", used=("Boilers Act s.2(c)",)),
    _F("F-BLR-05", "boiler_design_gauge_pressure_kgcm2", N,
       unit="kg/cm2", unknown=True, group="BLR",
       used=("Boilers Act s.2(c)(ii)",)),
    _F("F-BLR-06", "total_boiler_heating_surface_m2", N, unit="m2",
       unknown=True, group="BLR", used=("BOE Rules 2025",)),
    _F("F-LAB-07", "hazardous_process_first_schedule", B,
       unknown=True, group="LAB", used=("OSH s.22", "s.2(1)(za)")),
    _F("F-LAB-08", "interstate_migrant_workers", N, unit="count",
       unknown=True, group="LAB", used=("ISMW provisions",)),
    _F("F-LAB-09", "work_intermittent_or_casual_only", B,
       unknown=True, group="LAB", used=("OSH s.45(2)",)),
    _F("F-CWC-01", "unscheduled_DOC_synthesised_t_prev_year", N,
       unit="t/yr", unknown=True, group="CWC", used=("CWC OCPF",)),
    _F("F-CWC-02", "psf_chemical_synthesised_t_prev_year", N,
       unit="t/yr", unknown=True, group="CWC", used=("CWC OCPF",)),
    _F("F-CWC-03", "cwc_scheduled_chemicals", L, unknown=True,
       group="CWC", desc="[{schedule, qty}]", used=("CWC Sch 2/3",)),
    _F("F-NDPS-01", "controlled_substances_handled", L, unknown=True,
       group="NDPS", used=("RCS Order",)),
    _F("F-INS-01", "manufactures_insecticide", B, unknown=True,
       group="INS", used=("Insecticides Act",)),
    _F("F-DRG-01", "manufactures_drug_for_sale", B, unknown=True,
       group="DRG", used=("Drugs Rules",)),
    _F("F-LM-01", "max_package_size_kg_or_L", N, unit="kg_or_L",
       unknown=True, group="LM", used=("LM(PC) r.3",)),
    _F("F-LM-02", "buyer_type", E, unknown=True, group="LM",
       allowed=("RETAIL", "INDUSTRIAL_CONSUMER",
                "INSTITUTIONAL_CONSUMER", "MIXED"),
       used=("LM(PC) r.2(bb), r.3",)),
    _F("F-CHG-01", "change_types", L, unknown=True, group="CHG",
       desc="PRODUCT, PROCESS, INVENTORY, WASTE_STREAM, WATER, FUEL, "
            "CAPACITY, NAME",
       used=("EC 7(ii)", "MPCB amendment/fresh", "MSIHC r.8/r.11")),
    _F("F-WAT-10", "river_or_surface_source_name", S, unknown=True,
       group="WAT", used=("WRD permission",)),
    _F("F-FUEL-01", "fuel_types_and_tpd", L, unknown=True,
       group="FUEL", used=("EIA small-unit", "consent")),
    _F("F-EFF-01", "effluent_destination_and_qty", O, unknown=True,
       group="EFF", desc="CETP/ZLD/SEWER/SURFACE/NONE/UNKNOWN plus m3/day",
       used=("Consent", "CETP")),
    _F("F-INC-10", "ownership_structure", E, unknown=True,
       group="INC",
       allowed=("PROPRIETORSHIP", "PARTNERSHIP", "LLP", "COMPANY",
                "UNKNOWN"),
       used=("Incentive documents",)),
    _F("F-PA-02", "planning_or_local_authority_has_CFO", B,
       unknown=True, group="PA", used=("R-078",)),
    _F("F-BLD-10", "MFPLSM_Schedule_I_building_class", E, unknown=True,
       group="BLD",
       allowed=("G-1", "G-2", "G-3", "H", "J", "OTHER", "UNKNOWN"),
       used=("R-079",)),
    _F("F-BLD-11", "aggregate_floor_area_largest_building_m2", N,
       unit="m2", unknown=True, group="BLD", used=("R-079",)),
    _F("F-GEO-01", "CRZ_category_of_site", E, unknown=True,
       group="GEO",
       allowed=("CRZ-I", "CRZ-II", "CRZ-III", "CRZ-IV", "NOT_IN_CRZ",
                "UNKNOWN"),
       desc="From approved CZMP", used=("R-083",)),
    _F("F-GEO-03", "forest_area_ha", N, unit="ha", unknown=True,
       group="GEO", used=("R-084",)),
    _F("F-GEO-04", "site_within_notified_ESZ", B, unknown=True,
       group="GEO", used=("R-085",)),
    _F("F-GEO-05", "distance_to_nearest_NP_or_WLS_km", N, unit="km",
       unknown=True, group="GEO", used=("R-085",)),
    _F("F-GEO-06", "ESZ_notified_for_that_PA", B, unknown=True,
       group="GEO", used=("R-085",)),
    _F("F-GW-01", "CGWB_assessment_unit_category", E, unknown=True,
       group="GW",
       allowed=("SAFE", "SEMI_CRITICAL", "CRITICAL", "OVER_EXPLOITED",
                "UNKNOWN"),
       used=("R-077",)),
    _F("F-GW-02", "well_depth_m", N, unit="m", unknown=True,
       group="GW", used=("R-097",)),
    _F("F-GW-03", "MWRRA_notified_area", B, unknown=True, group="GW",
       used=("R-097",)),
    _F("F-BLR-07", "boiler_registration_status", E, unknown=True,
       group="BLR",
       allowed=("REGISTERED_UNDER_1923_ACT", "REGISTERED_UNDER_2025_ACT",
                "NOT_REGISTERED", "UNKNOWN"),
       used=("R-086", "R-087")),
    _F("F-BLR-08", "boiler_certificate_expiry_date", D, unknown=True,
       group="BLR", used=("R-087", "R-088")),
    _F("F-LAB-10", "engages_workers_in_Mathadi_scheduled_employment",
       B, unknown=True, group="LAB", used=("R-098",)),
    _F("F-LOC-19", "locality_covered_by_Mathadi_board_notification",
       B, unknown=True, group="LOC", used=("R-098",)),
    _F("F-HAZ-04", "chemical_inventory", L, unknown=True, group="HAZ",
       desc="CAS or name; physical state; flash/boiling point; "
            "LD50/LC50; max qty t; installation id; distance matrix",
       used=("R-091",)),
    _F("F-HW-04", "lab_results_for_Schedule_II_tests", L, unknown=True,
       group="HW", used=("R-096",)),
    _F("F-TRN-01", "consigns_CMVR_Table_III_goods_by_road", B,
       unknown=True, group="TRN", used=("R-093",)),
    _F("F-EEE-01", "units_of_Schedule_I_EEE_used_in_FY", N, unit="units",
       unknown=True, group="EEE", used=("R-094",)),
    _F("F-ODS-01", "uses_ODS_in_Schedule_IV_activity", B, unknown=True,
       group="ODS", used=("R-095",)),
    _F("F-FIR-20",
       "separate_act_or_rule_specifically_requires_fire_approval_renewal",
       B, unknown=True, group="FIR",
       desc=("Answer from the other statute's text; Petroleum/GCR "
             "claim in PA-7 order unverified (FR-03)"),
       used=("R-099",)),
    _F("F-PLN-02", "zone", S, unknown=True, group="PLN",
       desc="DP/RP land-use zone of site", used=("R-105",)),
    _F("F-PLN-03", "proposed_use", S, unknown=True, group="PLN",
       used=("R-105",)),
    _F("F-PLN-04", "existing_use", S, unknown=True, group="PLN",
       used=("R-105",)),
]

MH_FACTS: dict[str, FactSpec] = {spec.key: spec for spec in _MH_FACT_LIST}

# Facts excluded by the research baseline itself (never encodable).
EXCLUDED_MH_FACTS: dict[str, str] = {
    "F-BLD-02": "DEPRECATED / DO_NOT_IMPLEMENT_YET (EIA 8(a) exclusion)",
}


def _gj_known(key: str) -> bool:
    """Gujarat legacy field names (rule-condition vocabulary)."""
    return key in ALLOWED_FIELDS


def get_fact_spec(jurisdiction: str, key: str) -> FactSpec:
    """Look up a fact spec, enforcing jurisdiction scoping.

    Raises FactValidationError with a machine-readable code:
    unknown jurisdiction, jurisdiction mismatch (a field known only
    to the other jurisdiction), do-not-implement, or unknown field.
    """
    if jurisdiction != MH_JURISDICTION and jurisdiction != GJ_JURISDICTION:
        raise FactValidationError(
            key,
            f"unknown jurisdiction {jurisdiction!r}",
            FactValidationError.UNKNOWN_JURISDICTION,
        )
    if key in EXCLUDED_MH_FACTS:
        raise FactValidationError(
            key,
            f"fact is excluded by the research baseline: "
            f"{EXCLUDED_MH_FACTS[key]}",
            FactValidationError.DO_NOT_IMPLEMENT,
        )
    if jurisdiction == MH_JURISDICTION:
        spec = MH_FACTS.get(key)
        if spec is not None:
            return spec
        if _gj_known(key):
            raise FactValidationError(
                key,
                "fact belongs to the IN-GJ vocabulary, not IN-MH",
                FactValidationError.JURISDICTION_MISMATCH,
            )
        raise FactValidationError(
            key, "unknown IN-MH fact field", FactValidationError.UNKNOWN_FIELD
        )
    # IN-GJ lookups are served by the legacy validation path; the MH
    # registry only reports whether the key collides with MH.
    if key in MH_FACTS:
        raise FactValidationError(
            key,
            "fact belongs to the IN-MH registry, not IN-GJ",
            FactValidationError.JURISDICTION_MISMATCH,
        )
    raise FactValidationError(
        key,
        "IN-GJ facts are validated by the legacy path "
        "(validation.ALLOWED_FIELDS), not the MH registry",
        FactValidationError.UNKNOWN_FIELD,
    )


def is_unknown_value(spec: FactSpec, value: Any) -> bool:
    """True when a value represents unknown (never coerced to FALSE).

    ``None`` (or an absent key) is always unknown. The ``"UNKNOWN"``
    token is unknown only where the spec permits it.
    """
    if value is None:
        return True
    return spec.unknown_allowed and value == _UNKNOWN_TOKEN


def _is_enum_member(spec: FactSpec, value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if value in spec.allowed_values:
        return True
    for allowed in spec.allowed_values:
        if "<name>" in allowed:
            prefix = allowed.split("<name>")[0]
            if prefix and value.startswith(prefix):
                return True
    return spec.unknown_allowed and value == _UNKNOWN_TOKEN


def validate_fact_value(jurisdiction: str, key: str, value: Any) -> None:
    """Validate one supplied fact value against the registry.

    ``None`` is always valid: missing/unknown is not invalid. Anything
    else must satisfy the spec's type (and enum/date membership).
    Raises FactValidationError; returns None on success.
    """
    if value is None:
        return
    spec = get_fact_spec(jurisdiction, key)
    kind = spec.value_type

    if kind == FactValueType.BOOLEAN:
        if isinstance(value, bool):
            return
        if spec.unknown_allowed and value == _UNKNOWN_TOKEN:
            return
        raise FactValidationError(
            key,
            "value must be a boolean"
            + (" or 'UNKNOWN'" if spec.unknown_allowed else ""),
            FactValidationError.WRONG_TYPE,
        )

    if kind == FactValueType.INTEGER:
        if isinstance(value, bool) or not isinstance(value, int):
            raise FactValidationError(
                key, "value must be an integer",
                FactValidationError.WRONG_TYPE,
            )
        return

    if kind == FactValueType.NUMBER:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise FactValidationError(
                key, "value must be a number",
                FactValidationError.WRONG_TYPE,
            )
        return

    if kind == FactValueType.STRING:
        if not isinstance(value, str):
            raise FactValidationError(
                key, "value must be a string",
                FactValidationError.WRONG_TYPE,
            )
        return

    if kind == FactValueType.DATE:
        if isinstance(value, date):
            return
        if isinstance(value, str) and _ISO_DATE_RE.match(value):
            return
        raise FactValidationError(
            key, "value must be an ISO date string (YYYY-MM-DD)",
            FactValidationError.INVALID_DATE,
        )

    if kind == FactValueType.ENUM:
        if _is_enum_member(spec, value):
            return
        raise FactValidationError(
            key, "value must be one of the allowed enum values",
            FactValidationError.INVALID_ENUM,
        )

    if kind == FactValueType.ENUM_SET:
        if isinstance(value, list) and all(
            _is_enum_member(spec, item) for item in value
        ):
            return
        raise FactValidationError(
            key, "value must be a list of allowed enum values",
            FactValidationError.INVALID_ENUM,
        )

    if kind == FactValueType.LIST:
        if isinstance(value, list):
            return
        raise FactValidationError(
            key, "value must be a list", FactValidationError.WRONG_TYPE
        )

    if kind == FactValueType.OBJECT:
        if isinstance(value, dict | list):
            return
        raise FactValidationError(
            key, "value must be an object (dict) or list",
            FactValidationError.WRONG_TYPE,
        )

    raise FactValidationError(  # pragma: no cover - exhaustive enum
        key, f"unsupported fact type {kind}", FactValidationError.WRONG_TYPE
    )


def mh_fact_keys() -> list[str]:
    """Sorted IN-MH registry keys (stable, deterministic)."""
    return sorted(MH_FACTS)
