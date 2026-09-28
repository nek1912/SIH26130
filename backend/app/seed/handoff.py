"""Static government portal catalog for manual handoff.

Every URL below is transcribed from the verified seed dataset (source
records in app.seed.sources and document source_urls in
app.seed.documents). Nothing is invented or substituted.

Kinds:
- "portal": an official page where an applicant can act (application
  pages, checklists, catalogue, FAQ).
- "reference": an official document/index useful as reference, but NOT
  an application portal. The UI must label these differently and must
  never present them as a place to submit.

This catalog is provenance/configuration, not a decision engine:
presence here never implies an approval applies.
"""
from __future__ import annotations

from app.seed.approvals import load_approval_authorities

# approval_code -> (external_system, portal_url, portal_kind)
_PORTALS: dict[str, tuple[str, str, str]] = {
    "A01": (
        "GIDC",
        "https://gidc.gujarat.gov.in/Pages/Contents/application-for-plan-approval",
        "portal",
    ),
    "A02": (
        "GIDC",
        "https://gidc.gujarat.gov.in/Pages/Contents/application-for-water-connection",
        "portal",
    ),
    "A03": (
        "GIDC",
        "https://gidc.gujarat.gov.in/Pages/Contents/application-for-drainage-connection",
        "portal",
    ),
    "A04": (
        "GPCB (via Gujarat IFP)",
        "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_establishment_approvals.jsp?pagedisp=static",
        "portal",
    ),
    "A05": ("MoEFCC / PARIVESH", "https://parivesh.nic.in/kya/", "portal"),
    "A06": (
        "State Fire Prevention Services",
        "https://fscop.gujfiresafetycop.in/Front/FAQ.aspx",
        "portal",
    ),
    "A07": (
        "Labour & Employment (ShramSetu)",
        "https://shramsetu.gujarat.gov.in/Pages/OnlineApplication",
        "portal",
    ),
    "A08": (
        "Labour & Employment (ShramSetu)",
        "https://shramsetu.gujarat.gov.in/Pages/OnlineApplication",
        "portal",
    ),
    "A09": (
        "Applicable DISCOM (via Gujarat IFP)",
        "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_establishment_approvals.jsp?pagedisp=static",
        "portal",
    ),
    "A10": ("CEICED Gujarat", "https://ceiced.gujarat.gov.in/rcps-act-gujarat", "portal"),
    "A11": (
        "GPCB / SPCB (via Gujarat IFP)",
        "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_establishment_approvals.jsp?pagedisp=static",
        "portal",
    ),
    # No application portal in the verified dataset: official guidance PDF only.
    "A12": (
        "Factory / environment / district authorities",
        "https://cpcb.nic.in/uploads/Guidelines_integrated_guidance_framework.pdf",
        "reference",
    ),
    "A13": (
        "Relevant state/district emergency authorities",
        "https://cpcb.nic.in/uploads/Guidelines_integrated_guidance_framework.pdf",
        "reference",
    ),
    "A14": (
        "Urban Development / local authority (via Gujarat IFP)",
        "https://ifp.gujarat.gov.in/DIGIGOV/IFP-pages/pre_operation_approvals.jsp?pagedisp=static",
        "portal",
    ),
    "A15": ("CEICED Gujarat", "https://ceiced.gujarat.gov.in/rcps-act-gujarat", "portal"),
    # Rules index only; no application portal in the verified dataset.
    "A16": (
        "Gujarat Directorate of Boilers",
        "https://boiler.gujarat.gov.in/acts-rules.htm",
        "reference",
    ),
    "A17": (
        "PESO",
        "https://www.peso.gov.in/web/en/requirement-license-under-petroleum-rules-2002-storage-petroleum",
        "portal",
    ),
    # Consolidated guidelines PDF only; no application portal verified.
    "A18": (
        "CGWA",
        "https://cgwa-noc.gov.in/landingpage/Guidlines/ConsolidateGuidline.pdf",
        "reference",
    ),
}


def get_portal_entry(approval_code: str) -> dict[str, str] | None:
    """Return the catalog entry for an approval code, or None if unmapped."""
    authorities = load_approval_authorities()
    entry = _PORTALS.get(approval_code)
    if entry is None:
        return None
    system, url, kind = entry
    return {
        "approval_code": approval_code,
        "authority": authorities.get(approval_code, system),
        "external_system": system,
        "portal_url": url,
        "portal_kind": kind,
    }


def all_portal_entries() -> list[dict[str, str]]:
    """Return all catalog entries in approval-code order."""
    return [e for code in sorted(_PORTALS) if (e := get_portal_entry(code)) is not None]
