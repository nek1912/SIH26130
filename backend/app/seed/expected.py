"""Expected_Test_Results from the frozen workbook.

These are the acceptance targets — the oracle for evaluating the engine.
Each entry maps a test scenario to an expected engine outcome.
"""
from __future__ import annotations

from typing import Any


def load_expected_results() -> list[dict[str, Any]]:
    """Return expected test results from the workbook."""
    return [dict(r) for r in EXPECTED_RESULTS]


EXPECTED_RESULTS: list[dict[str, Any]] = [
    {
        "test_id": "T01",
        "rule_id": "R-GIDC-001",
        "approval_id": "A01",
        "description": "GIDC CA-I Chemical risk band: plot area 12000 sqm -> High Risk",
        "expected_outcome": "applies",
        "type": "DETERMINISTIC",
        "source": "S03",
    },
    {
        "test_id": "T02",
        "rule_id": "R-GIDC-001",
        "approval_id": "A01",
        "description": "No physical site investigation for fresh GIDC applications (procedural)",
        "expected_outcome": "applies",
        "type": "DETERMINISTIC",
        "source": "S06",
    },
    {
        "test_id": "T03",
        "rule_id": "R-GIDC-003",
        "approval_id": "A02",
        "description": "Chemical unit + GIDC water: GPCB NOC required",
        "expected_outcome": "applies",
        "type": "PREREQUISITE",
        "source": "S04",
    },
    {
        "test_id": "T04",
        "rule_id": "R-GIDC-005",
        "approval_id": "A03",
        "description": "GIDC drainage: ETP/GPCB requirements",
        "expected_outcome": "applies",
        "type": "PREREQUISITE",
        "source": "S05",
    },
    {
        "test_id": "T05",
        "rule_id": "R-EIA-001",
        "approval_id": "A05",
        "description": "EIA Schedule 5(f) candidate - synthetic organic chemicals",
        "expected_outcome": "applies",
        "type": "CONDITIONAL",
        "source": "S14",
    },
    {
        "test_id": "T06",
        "rule_id": "R-FIRE-001",
        "approval_id": "A06",
        "description": "Fire: hazardous building >15m not permitted (CONFLICT)",
        "expected_outcome": "applies",
        "type": "CONFLICT",
        "source": "S07",
        "note": (
            "Engine returns APPLIES with conflict in reason text; "
            "no separate CONFLICT outcome"
        ),
    },
    {
        "test_id": "T07",
        "rule_id": "R-FIRE-004",
        "approval_id": "A06",
        "description": "Fire height prohibition: C9H1/C9H2 up to 15m; 18m exceeds limit",
        "expected_outcome": "does_not_apply",
        "type": "CONDITIONAL",
        "source": "S07",
        "note": (
            "Building height 18m > 15m; R-FIRE-004 condition "
            "(hazardous_process AND building_height<=15) fails"
        ),
    },
    {
        "test_id": "T08",
        "rule_id": "R-GERC-002",
        "approval_id": "A09",
        "description": "HT supply path: 1000 kVA -> 11/22 kV",
        "expected_outcome": "applies",
        "type": "DETERMINISTIC",
        "source": "S12",
    },
    {
        "test_id": "T09",
        "rule_id": "R-CEA-001",
        "approval_id": "A10",
        "description": "CEICED inspection for HT installation",
        "expected_outcome": "applies",
        "type": "CONDITIONAL",
        "source": "S11",
    },
    {
        "test_id": "T10",
        "rule_id": "R-LAB-001",
        "approval_id": "A07",
        "description": "OSH&WC registration: 60 workers + hazardous process",
        "expected_outcome": "applies",
        "type": "PREREQUISITE",
        "source": "S09",
    },
    {
        "test_id": "T11",
        "rule_id": "R-HW-001",
        "approval_id": "A11",
        "description": "HOWM authorization: hazardous waste generated",
        "expected_outcome": "applies",
        "type": "CONDITIONAL",
        "source": "S16",
    },
    {
        "test_id": "T12",
        "rule_id": "R-CGWA-001",
        "approval_id": "A18",
        "description": "CGWA: groundwater use = false -> not triggered",
        "expected_outcome": "does_not_apply",
        "type": "NEGATIVE_BRANCH",
        "source": "S19",
    },
    {
        "test_id": "T13",
        "rule_id": "R-LIFT-001",
        "approval_id": "A15",
        "description": "Lift present = true -> lift approval branch",
        "expected_outcome": "applies",
        "type": "CONDITIONAL",
        "source": "S30",
    },
    {
        "test_id": "T14",
        "rule_id": "R-BOILER-001",
        "approval_id": "A16",
        "description": "Boiler present = true -> boiler registration branch",
        "expected_outcome": "applies",
        "type": "CONDITIONAL",
        "source": "S31",
    },
    {
        "test_id": "T15",
        "rule_id": None,
        "approval_id": None,
        "description": "Cross-document inconsistency detection (SYSTEM_TEST)",
        "expected_outcome": "system_test",
        "type": "SYSTEM_TEST",
        "source": None,
        "note": "Outside applicability engine scope - tests data consistency layer",
    },
]
