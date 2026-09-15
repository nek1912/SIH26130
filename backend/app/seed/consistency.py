"""Cross-document consistency rules from the frozen workbook.

Consistency_Fields Sheet
========================

18 canonical fields that MUST MATCH across affected systems/documents.
Each rule maps a canonical field to the document requirement keys
that should carry that field's value.

Source: SIH_130_Gujarat_Chemical_Final_Verified_Dataset.xlsx → Consistency_Fields
"""
from __future__ import annotations

from app.consistency.models import ConsistencyRule

CONSISTENCY_RULES: list[ConsistencyRule] = [
    ConsistencyRule(
        id="C01",
        canonical_field="plot_area_sqm",
        affected_systems="GIDC Plan",
        evidence_field="Land/title/GIS",
        requirement_key="MUST_MATCH",
        document_keys=["D01", "D02", "D03"],
    ),
    ConsistencyRule(
        id="C02",
        canonical_field="builtup_area_sqm",
        affected_systems="GIDC Plan / BU",
        evidence_field="Architectural drawings",
        requirement_key="MUST_MATCH",
        document_keys=["D04"],
    ),
    ConsistencyRule(
        id="C03",
        canonical_field="production_capacity",
        affected_systems="GPCB / EC",
        evidence_field="Process/product schedule",
        requirement_key="MUST_MATCH",
        document_keys=["D08", "D09"],
    ),
    ConsistencyRule(
        id="C04",
        canonical_field="product_names",
        affected_systems="GPCB / EC / factory",
        evidence_field="Product list",
        requirement_key="MUST_MATCH",
        document_keys=["D08", "D09"],
    ),
    ConsistencyRule(
        id="C05",
        canonical_field="raw_materials",
        affected_systems="GPCB / factory / MSIHC",
        evidence_field="Material list",
        requirement_key="MUST_MATCH",
        document_keys=["D09", "D14"],
    ),
    ConsistencyRule(
        id="C06",
        canonical_field="hazardous_chemical_max_quantity",
        affected_systems="MSIHC / GPCB / PESO",
        evidence_field="Storage inventory",
        requirement_key="MUST_MATCH",
        document_keys=["D11", "D16"],
    ),
    ConsistencyRule(
        id="C07",
        canonical_field="fresh_water_requirement",
        affected_systems="GIDC Water / GPCB / EC",
        evidence_field="Water balance",
        requirement_key="MUST_MATCH",
        document_keys=["D07"],
    ),
    ConsistencyRule(
        id="C08",
        canonical_field="effluent_generation",
        affected_systems="GIDC Drainage / GPCB / EC",
        evidence_field="Water balance + ETP",
        requirement_key="MUST_MATCH",
        document_keys=["D06", "D07"],
    ),
    ConsistencyRule(
        id="C09",
        canonical_field="ETP_capacity",
        affected_systems="GIDC Drainage / GPCB",
        evidence_field="ETP drawing",
        requirement_key="MUST_MATCH",
        document_keys=["D06"],
    ),
    ConsistencyRule(
        id="C10",
        canonical_field="hazardous_waste_quantity",
        affected_systems="GPCB / HOWM",
        evidence_field="Waste inventory",
        requirement_key="MUST_MATCH",
        document_keys=["D10"],
    ),
    ConsistencyRule(
        id="C11",
        canonical_field="power_demand_kVA",
        affected_systems="DISCOM / GERC / CEICED",
        evidence_field="Load list / estimate",
        requirement_key="MUST_MATCH",
        document_keys=["D13"],
    ),
    ConsistencyRule(
        id="C12",
        canonical_field="DG_capacity",
        affected_systems="DISCOM / CEICED / PESO if applicable",
        evidence_field="DG datasheet",
        requirement_key="MUST_MATCH",
        document_keys=["D13", "D16"],
    ),
    ConsistencyRule(
        id="C13",
        canonical_field="building_height",
        affected_systems="GIDC / Fire / BU / Lift",
        evidence_field="Architectural drawings",
        requirement_key="MUST_MATCH",
        document_keys=["D04", "D12"],
    ),
    ConsistencyRule(
        id="C14",
        canonical_field="worker_count",
        affected_systems="Factory / labour",
        evidence_field="Manpower plan",
        requirement_key="MUST_MATCH",
        document_keys=["D14"],
    ),
    ConsistencyRule(
        id="C15",
        canonical_field="plot_or_survey_identifier",
        affected_systems="GIDC / land / EC",
        evidence_field="All land documents",
        requirement_key="MUST_MATCH",
        document_keys=["D01", "D02", "D03"],
    ),
    ConsistencyRule(
        id="C16",
        canonical_field="applicant/company_name",
        affected_systems="All portals",
        evidence_field="Corporate documents",
        requirement_key="MUST_MATCH",
        document_keys=[
            "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09",
            "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17",
        ],
    ),
    ConsistencyRule(
        id="C17",
        canonical_field="address",
        affected_systems="All authorities",
        evidence_field="Registered/site address",
        requirement_key="MUST_MATCH",
        document_keys=[
            "D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09",
            "D10", "D11", "D12", "D13", "D14", "D15", "D16", "D17",
        ],
    ),
    ConsistencyRule(
        id="C18",
        canonical_field="legal_entity_type",
        affected_systems="IFP / labour / company docs",
        evidence_field="Constitution documents",
        requirement_key="MUST_MATCH",
        document_keys=["D14"],
    ),
]


def load_consistency_rules() -> list[ConsistencyRule]:
    """Return all cross-document consistency rules from the workbook."""
    return list(CONSISTENCY_RULES)
