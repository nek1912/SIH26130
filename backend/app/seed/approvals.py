"""Approval rules from the frozen workbook.

Each workbook approval (A01-A18) is represented as an ApprovalRule
with handcrafted ConditionNode trees derived from the Rule_Register.

The workbook rules are plain-English factual statements.
These ConditionNode trees are the machine-parseable translation.
"""
from __future__ import annotations

from typing import Any

from app.rules.models import (
    AndNode,
    ApplicabilityCondition,
    ApplicabilityOp,
    ApprovalRule,
    NotNode,
    OrNode,
    SourceRef,
)


def _leaf(field: str, op: str, value: Any) -> ApplicabilityCondition:
    return ApplicabilityCondition(field=field, op=ApplicabilityOp(op), value=value)


def _and(*nodes: Any) -> AndNode:
    return AndNode(conditions=list(nodes))


def _or(*nodes: Any) -> OrNode:
    return OrNode(conditions=list(nodes))


def _not(node: Any) -> NotNode:
    return NotNode(condition=node)


def _ref(source_id: str, citation: str) -> list[SourceRef]:
    return [SourceRef(source_id=source_id, citation_span=citation)]


def load_approval_rules() -> list[ApprovalRule]:
    """Return all 18 approval rules from the workbook."""
    return [
        _a01_gidc_plan(),
        _a02_gidc_water(),
        _a03_gidc_drainage(),
        _a04_gpcb_cte(),
        _a05_eia(),
        _a06_fire_general(),
        _a06_fire_height(),
        _a07_factory_reg(),
        _a08_bocw(),
        _a09_ht_electricity(),
        _a10_ceiced(),
        _a11_howm(),
        _a12_msihc(),
        _a13_chemical_accidents(),
        _a14_bu_permission(),
        _a15_lift(),
        _a16_boiler(),
        _a17_peso(),
        _a18_cgwa(),
    ]


def load_approval_authorities() -> dict[str, str]:
    """Return approval_id -> authority mapping."""
    return {
        "A01": "GIDC",
        "A02": "GIDC",
        "A03": "GIDC",
        "A04": "GPCB via IFP/XGN",
        "A05": "MoEFCC / SEIAA / SEAC",
        "A06": "State Fire Prevention Services",
        "A07": "Labour & Employment / DISH",
        "A08": "Labour & Employment",
        "A09": "Applicable DISCOM",
        "A10": "CEICED / Electrical Inspector",
        "A11": "GPCB / SPCB",
        "A12": "Factory / environment / district",
        "A13": "State/district emergency authorities",
        "A14": "Urban Development / local authority",
        "A15": "Electrical Inspector / lift authority",
        "A16": "Boiler authority",
        "A17": "PESO",
        "A18": "CGWA",
    }


# -- A01: GIDC Plan Approval --
# R-GIDC-001: plot_area 10000-25000 -> High risk band for chemical industry
# R-GIDC-002: No physical site investigation (procedural, no condition tree)
def _a01_gidc_plan() -> ApprovalRule:
    return ApprovalRule(
        id="R-GIDC-001",
        approval_id="A01",
        applicability_conditions=[
            _and(
                _leaf(
                    "industry_type",
                    "eq",
                    "synthetic organic / specialty chemical manufacturing",
                ),
                _leaf("plot_area_sqm", "gte", 10000),
            )
        ],
        source_refs=_ref("S03", "GIDC Plan Approval page - risk table"),
        version="1",
    )


# -- A02: GIDC Water Connection --
# R-GIDC-003: Chemical unit needs GPCB NOC copy + possession
def _a02_gidc_water() -> ApprovalRule:
    return ApprovalRule(
        id="R-GIDC-003",
        approval_id="A02",
        applicability_conditions=[
            _leaf(
                "industry_type",
                "eq",
                "synthetic organic / specialty chemical manufacturing",
            )
        ],
        source_refs=_ref(
            "S04", "GIDC Water Connection page - chemical unit prerequisite"
        ),
        version="1",
    )


# -- A03: GIDC Drainage Connection --
# R-GIDC-005: Approved ETP/STP plan + GPCB NOC + water connection
def _a03_gidc_drainage() -> ApprovalRule:
    return ApprovalRule(
        id="R-GIDC-005",
        approval_id="A03",
        applicability_conditions=[
            _and(
                _leaf("effluent_generation", "gt", 0),
                _leaf("ETP_capacity", "gte", 1),
            )
        ],
        source_refs=_ref(
            "S05", "GIDC Drainage Connection page - ETP/GPCB requirement"
        ),
        version="1",
    )


# -- A04: GPCB CTE --
# R-IFP-001: IFP 46-item checklist - applies to chemical industry
def _a04_gpcb_cte() -> ApprovalRule:
    return ApprovalRule(
        id="R-IFP-001",
        approval_id="A04",
        applicability_conditions=[
            _leaf(
                "industry_type",
                "eq",
                "synthetic organic / specialty chemical manufacturing",
            )
        ],
        source_refs=_ref(
            "S01", "Gujarat IFP Pre-Establishment - GPCB CTE checklist"
        ),
        version="1",
    )


# -- A05: Environmental Clearance (EIA 5(f)) --
# R-EIA-001: Synthetic organic chemicals are EIA Schedule 5(f) candidate
def _a05_eia() -> ApprovalRule:
    return ApprovalRule(
        id="R-EIA-001",
        approval_id="A05",
        applicability_conditions=[
            _and(
                _leaf(
                    "industry_type",
                    "eq",
                    "synthetic organic / specialty chemical manufacturing",
                ),
                _leaf("production_capacity", "gte", 20000),
            )
        ],
        source_refs=_ref("S14", "PARIVESH KYA - EIA 5(f) candidate"),
        version="1",
    )


# -- A06: Fire Safety (split into two aspects) --
# R-FIRE-001: General applicability — buildings in Third Schedule require
#   Fire Safety Certificate. Applies when hazardous_process=True and
#   building exists (height>0).
# R-FIRE-004: Height prohibition — C9H1/C9H2 hazardous buildings must not
#   exceed 15m. The approval can only be obtained when building_height <= 15.
def _a06_fire_general() -> ApprovalRule:
    return ApprovalRule(
        id="R-FIRE-001",
        approval_id="A06",
        applicability_conditions=[
            _and(
                _leaf("hazardous_process", "eq", True),
                _leaf("building_height", "gt", 0),
            )
        ],
        source_refs=_ref(
            "S07",
            "Gujarat Fire Prevention and Life Safety Measures Regulations 2023",
        ),
        version="1",
    )


def _a06_fire_height() -> ApprovalRule:
    return ApprovalRule(
        id="R-FIRE-004",
        approval_id="A06",
        applicability_conditions=[
            _and(
                _leaf("hazardous_process", "eq", True),
                _leaf("building_height", "lte", 15),
            )
        ],
        source_refs=_ref(
            "S07",
            "Gujarat Fire Prevention and Life Safety Measures Regulations 2023 — "
            "C9H1/C9H2 max height 15m",
        ),
        version="1",
    )


# -- A07: Factory Registration --
# R-LAB-001: ShramSetu provides OSH&WC registration/licence
def _a07_factory_reg() -> ApprovalRule:
    return ApprovalRule(
        id="R-LAB-001",
        approval_id="A07",
        applicability_conditions=[
            _and(
                _leaf("workers_total", "gte", 1),
                _leaf("hazardous_process", "eq", True),
            )
        ],
        source_refs=_ref(
            "S09", "ShramSetu Online Application - OSH&WC registration"
        ),
        version="1",
    )


# -- A08: BOCW Registration --
# Construction-phase: new_project + workers present
def _a08_bocw() -> ApprovalRule:
    return ApprovalRule(
        id="R-BOCW-001",
        approval_id="A08",
        applicability_conditions=[
            _and(
                _leaf("new_project", "eq", True),
                _leaf("workers_total", "gte", 1),
            )
        ],
        source_refs=_ref(
            "S01", "Gujarat IFP Pre-Establishment - BOCW service"
        ),
        version="1",
    )


# -- A09: HT Electricity Connection --
# R-GERC-001/002: >100/150 kVA -> HT 11/22 kV
def _a09_ht_electricity() -> ApprovalRule:
    return ApprovalRule(
        id="R-GERC-002",
        approval_id="A09",
        applicability_conditions=[_leaf("power_demand", "gte", 100)],
        source_refs=_ref(
            "S12", "GERC Fourth Amendment 2024 - HT supply range"
        ),
        version="1",
    )


# -- A10: CEICED Inspection --
# R-CEA-001: Electrical safety regulation - applies to HT installations
def _a10_ceiced() -> ApprovalRule:
    return ApprovalRule(
        id="R-CEA-001",
        approval_id="A10",
        applicability_conditions=[_leaf("power_demand", "gte", 100)],
        source_refs=_ref(
            "S11", "CEA Safety & Electric Supply Regulations 2023"
        ),
        version="1",
    )


# -- A11: HOWM Authorization --
# R-HW-001: HOWM Rule 6 authorization for hazardous waste
def _a11_howm() -> ApprovalRule:
    return ApprovalRule(
        id="R-HW-001",
        approval_id="A11",
        applicability_conditions=[
            _leaf("hazardous_waste_generated", "eq", True)
        ],
        source_refs=_ref(
            "S16", "CPCB HOWM 2024 Amendment - Rule 6 authorization"
        ),
        version="1",
    )


# -- A12: MSIHC Compliance --
# R-MSIHC-001: MSIHC Schedule 1/2/3 - hazardous chemicals
def _a12_msihc() -> ApprovalRule:
    return ApprovalRule(
        id="R-MSIHC-001",
        approval_id="A12",
        applicability_conditions=[
            _leaf("hazardous_chemicals_handled", "eq", True)
        ],
        source_refs=_ref(
            "S17",
            "CPCB Hazardous chemical integrated guidance - MSIHC mechanism",
        ),
        version="1",
    )


# -- A13: Chemical Accidents Rules --
# Applicable alongside MSIHC for covered hazardous chemical activities
def _a13_chemical_accidents() -> ApprovalRule:
    return ApprovalRule(
        id="R-CA-001",
        approval_id="A13",
        applicability_conditions=[
            _leaf("hazardous_chemicals_handled", "eq", True)
        ],
        source_refs=_ref(
            "S17",
            "CPCB Hazardous chemical integrated guidance - Chemical Accidents Rules",
        ),
        version="1",
    )


# -- A14: BU Permission --
# IFP pre-operation: completion/as-built + fire clearance + lift evidence
def _a14_bu_permission() -> ApprovalRule:
    return ApprovalRule(
        id="R-BU-001",
        approval_id="A14",
        applicability_conditions=[_leaf("new_project", "eq", True)],
        source_refs=_ref(
            "S02", "Gujarat IFP Pre-Operation - BU permission"
        ),
        version="1",
    )


# -- A15: Lift Approval --
# Conditional on lift_present
def _a15_lift() -> ApprovalRule:
    return ApprovalRule(
        id="R-LIFT-001",
        approval_id="A15",
        applicability_conditions=[_leaf("lift_present", "eq", True)],
        source_refs=_ref(
            "S30", "CEICED official checklist - lift/escalator"
        ),
        version="1",
    )


# -- A16: Boiler Registration --
# Conditional on boiler_present
def _a16_boiler() -> ApprovalRule:
    return ApprovalRule(
        id="R-BOILER-001",
        approval_id="A16",
        applicability_conditions=[_leaf("boiler_present", "eq", True)],
        source_refs=_ref(
            "S31", "Gujarat Directorate of Boilers - Acts & Rules"
        ),
        version="1",
    )


# -- A17: PESO Licence --
# R-PESO-001: PESO petroleum rules - substance/class/quantity dependent
def _a17_peso() -> ApprovalRule:
    return ApprovalRule(
        id="R-PESO-001",
        approval_id="A17",
        applicability_conditions=[
            _leaf("hazardous_chemicals_handled", "eq", True)
        ],
        source_refs=_ref(
            "S18", "PESO petroleum storage licence requirement"
        ),
        version="1",
    )


# -- A18: CGWA Groundwater NOC --
# Conditional on groundwater_use
def _a18_cgwa() -> ApprovalRule:
    return ApprovalRule(
        id="R-CGWA-001",
        approval_id="A18",
        applicability_conditions=[_leaf("groundwater_use", "eq", True)],
        source_refs=_ref(
            "S19", "CGWA consolidated guidelines - groundwater NOC"
        ),
        version="1",
    )
