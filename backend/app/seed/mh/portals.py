"""Maharashtra v5 batch-1 portal catalog (Phase 5).

Navigation metadata ONLY — entries tell the user where an external
government workflow/reference can be accessed. They never alter
deterministic decisions and never claim workflow availability beyond
what the v5 portal register establishes.

Kind vocabulary (existing contract, exactly two values):
- ``portal``: the register confirms applications/documents can be
  acted on there (login/services documented). Only these may ever
  render as a portal CTA.
- ``reference``: official page useful as reference, or a service
  whose workflow availability is unconfirmed (PORTAL_LEGACY,
  catalogue-only, or check-aid pages). Never a submission CTA.

There is deliberately no third kind: a record without a usable URL
is ``reference`` with an empty URL (see ``is_portal_cta``), which the
POR-003-style test pins. No MAITRI entry (POR-013): service-level
integration is unconfirmed (UNK-009) and integration must never be
implied.
"""
from __future__ import annotations

from typing import Any

from app.seed.mh.approvals import load_mh_approval_authorities

_MH_AUTHORITIES = load_mh_approval_authorities()


def _entry(
    approval_code: str,
    portal_id: str,
    external_system: str,
    portal_url: str,
    portal_kind: str,
    service_note: str,
) -> dict[str, Any]:
    assert portal_kind in ("portal", "reference"), portal_id
    return {
        "approval_code": approval_code,
        "authority": _MH_AUTHORITIES.get(approval_code, ""),
        "external_system": external_system,
        "portal_url": portal_url,
        "portal_kind": portal_kind,
        "portal_id": portal_id,
        "service_note": service_note,
    }


MH_PORTAL_ENTRIES: list[dict[str, Any]] = [
    # EC approvals are filed on PARIVESH (applications require login).
    _entry("APR-001", "POR-001", "MoEFCC / PARIVESH",
           "https://parivesh.nic.in/", "portal",
           "EC/FC/WL/CRZ applications and compliance"),
    _entry("APR-003", "POR-001", "MoEFCC / PARIVESH",
           "https://parivesh.nic.in/", "portal",
           "EC/FC/WL/CRZ applications and compliance"),
    _entry("APR-004", "POR-001", "MoEFCC / PARIVESH",
           "https://parivesh.nic.in/", "portal",
           "EC/FC/WL/CRZ applications and compliance"),
    _entry("APR-006", "POR-001", "MoEFCC / PARIVESH",
           "https://parivesh.nic.in/", "portal",
           "EC/FC/WL/CRZ applications and compliance"),
    _entry("APR-007", "POR-001", "MoEFCC / PARIVESH",
           "https://parivesh.nic.in/", "portal",
           "EC/FC/WL/CRZ applications and compliance"),
    # HW authorisation via the MPCB consent system.
    _entry("APR-010", "POR-002", "MPCB ecMPCB consent system",
           "https://mpcb.gov.in/en/consent-status", "portal",
           "CTE, CTO, HW authorisation, EPR"),
    # MIDC planning page: provenance for DOC-001/002 (MIDC BP
    # acknowledgement practice), not a submission channel here.
    _entry("APR-010", "POR-008", "MIDC services portal",
           "https://services.midcindia.org/Services/"
           "AllServicesPortalAnon.aspx", "reference",
           "Provenance for DOC-001/002 MIDC acknowledgement practice"),
    # Labour RTS catalogue (no online application): reference only.
    _entry("APR-019", "POR-005", "Maharashtra Labour Department",
           "https://labour.maharashtra.gov.in/en/rts/rts-services",
           "reference", "RTS catalogue; no online application"),
    _entry("APR-022", "POR-005", "Maharashtra Labour Department",
           "https://labour.maharashtra.gov.in/en/rts/rts-services",
           "reference", "RTS catalogue; no online application"),
    # Boiler services: PORTAL_LEGACY workflow (CON-028/UR-09), so
    # reference until the 2025-Act workflow is confirmed.
    _entry("APR-023", "POR-006", "Maharashtra Steam Boilers",
           "https://www.mahaboiler.in/boiler/online_services.html",
           "reference",
           "Services listed under pre-2025-Act pages (PORTAL_LEGACY)"),
    # Petroleum licences on PESO Online.
    _entry("APR-026", "POR-007", "PESO Online",
           "https://online.peso.gov.in/PesoOnline/", "portal",
           "Licences under Petroleum, GCR, SMPV, Explosives"),
    # MIDC GIS: fact-check aid for F-LOC-01 (R-035), not a channel.
    _entry("APR-029", "POR-008G", "MIDC GIS map service",
           "https://gis.midcindia.org/server/rest/services/"
           "CitizenPortal/MIDC_PUBLIC_MAIN_MAP_SERVICE/MapServer",
           "reference", "Estate boundary/plot check aid for F-LOC-01"),
    # Groundwater NOC on CGWA NOCAP.
    _entry("APR-043", "POR-010", "CGWA NOCAP",
           "https://cgwa-noc.gov.in/LandingPage/index.htm", "portal",
           "Groundwater NOC"),
    _entry("APR-044", "POR-010", "CGWA NOCAP",
           "https://cgwa-noc.gov.in/LandingPage/index.htm", "portal",
           "Groundwater NOC"),
]


def is_portal_cta(entry: dict[str, Any]) -> bool:
    """True only for entries that may render as a portal CTA.

    A missing/unusable URL can never be a CTA: such records must be
    ``reference`` kind (POR-003-style safety), and this helper
    additionally refuses non-http(s) URLs defensively.
    """
    if entry.get("portal_kind") != "portal":
        return False
    url = entry.get("portal_url") or ""
    return url.startswith("https://") and "UNKNOWN" not in url


def load_mh_portal_entries() -> list[dict[str, Any]]:
    """Return the batch-1 MH portal catalog (14 entries)."""
    entries = [dict(entry) for entry in MH_PORTAL_ENTRIES]
    for entry in entries:
        if entry["portal_kind"] == "portal" and not is_portal_cta(entry):
            raise ValueError(
                f"Portal-kind entry {entry['portal_id']} for "
                f"{entry['approval_code']} has no usable URL"
            )
    return entries
