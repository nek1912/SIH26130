"""Canonical approval catalog (A01-A18) for database seeding.

Identity key: ``code``. Names are copied verbatim from the frozen workbook
``Approval_Register.approval`` column
(``SIH_130_Gujarat_Chemical_Final_Verified_Dataset.xlsx``); authorities reuse
``load_approval_authorities()`` (verified seed) so rule/dependency references
stay on a single source. Where workbook authority strings are longer variants
of the seed strings (A05, A06, A07, A14), the seed form governs here and the
workbook variants are preserved in docs/approval-identity-verification.md.

This module transcribes canonical data with provenance — it asserts no
mapping between database UUIDs and codes. Seeding fresh rows from this
catalog creates new identities; it never re-identifies existing rows
(mismatched same-code rows fail loudly in the seed endpoint instead).
"""
from __future__ import annotations

from typing import Any

from app.seed.approvals import load_approval_authorities

# Exact Approval_Register.approval values, transcribed 2026-09-25.
_APPROVAL_NAMES: dict[str, str] = {
    "A01": "GIDC Plan Approval",
    "A02": "GIDC Water Connection",
    "A03": "GIDC Drainage Connection",
    "A04": "GPCB Consent to Establish (CTE)",
    "A05": "Environmental Clearance \u2014 EIA item 5(f) candidate",
    "A06": "Gujarat Fire Safety Plan Approval / Fire Safety Certificate",
    "A07": "Factory establishment registration / licence under OSH&WC",
    "A08": "Building & Other Construction Workers registration",
    "A09": "HT Electricity Connection",
    "A10": "Electrical installation inspection/certification",
    "A11": "Hazardous & Other Waste authorization",
    "A12": "MSIHC compliance",
    "A13": "Chemical Accidents Rules compliance",
    "A14": "Building Use (BU) Permission",
    "A15": "Lift approval/inspection",
    "A16": "Boiler approval/registration",
    "A17": "PESO licence/permission for petroleum storage",
    "A18": "CGWA groundwater NOC",
}


def load_approval_catalog() -> list[dict[str, Any]]:
    """Return the 18 canonical approval records for database seeding."""
    authorities = load_approval_authorities()
    return [
        {
            "code": code,
            "name": _APPROVAL_NAMES[code],
            "authority": authorities[code],
            "description": None,
            "category": "general",
            "active": True,
        }
        for code in sorted(_APPROVAL_NAMES)
    ]
