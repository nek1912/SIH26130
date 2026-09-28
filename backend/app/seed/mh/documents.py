"""Maharashtra v5 batch-1 document requirements (Phase 4).

Only v5 document rows that are VERIFIED_CONDITIONAL (never
REQUIRES_CONFIRMATION / UNKNOWN) AND explicitly linked
(``used_for``) to a batch-1 approval enter the pack. Dict shapes
follow the existing document-requirement contract
(requirement_key, document_name, approval_ids, domain,
requirement_level, source_basis, source_url, ...).

Contract-field mapping decisions (documented, not invented facts):
- ``requirement_level`` "required": the ``mandatory_basis`` column
  states a requirement in every included row.
- ``domain``: closest existing domain vocabulary (ENVIRONMENT for
  consent/waste rows, PROCESS for the petroleum row); informational
  only — the readiness engine does not consume it.
- ``document_role`` mirrors the GJ pattern (authority-issued vs
  applicant-supplied).
- ``source_url``: verified URL looked up from sources.csv for the
  row's first source ID. ``size_limit`` is NOT_STATED in v5, so
  ``max_size_mb`` is None (no invented limit).

Deferred rows (never loaded):
- DOC-004, DOC-005, DOC-006, DOC-010: linked approvals outside batch-1.
- DOC-007, DOC-009: REQUIRES_OFFICIAL_CONFIRMATION.
- DOC-011: UNKNOWN status + inferred practice + out of scope.
- DOC-012: REQUIRES_OFFICIAL_CONFIRMATION (surfaced as evidence
  instead; see ``evidence.py``).
"""
from __future__ import annotations

from typing import Any

MH_DOCUMENT_REQUIREMENTS: list[dict[str, Any]] = [
    {
        "requirement_key": "DOC-001",
        "document_name": "Consent to Establish (copy)",
        "approval_ids": ["APR-010", "APR-030"],
        "domain": "ENVIRONMENT",
        "requirement_level": "required",
        "source_basis": (
            "HOWM r.6 requires CTE with Form 1 [SRC-013; SRC-044]"
        ),
        "source_url": (
            "https://upload.indiacode.nic.in/showfile"
            "?actid=AC_CH_60_926_00001_00001_1558607117075&type=rule"
            "&filename=final_hwm_rules_2016__english_.pdf"
        ),
        "document_role": "Authority document",
        "issuer": "MPCB",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": None,
    },
    {
        "requirement_key": "DOC-002",
        "document_name": "Consent to Operate (copy)",
        "approval_ids": ["APR-010", "APR-032"],
        "domain": "ENVIRONMENT",
        "requirement_level": "required",
        "source_basis": "HOWM r.6 [SRC-013; SRC-044]",
        "source_url": (
            "https://upload.indiacode.nic.in/showfile"
            "?actid=AC_CH_60_926_00001_00001_1558607117075&type=rule"
            "&filename=final_hwm_rules_2016__english_.pdf"
        ),
        "document_role": "Authority document",
        "issuer": "MPCB",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": None,
    },
    {
        "requirement_key": "DOC-003",
        "document_name": "Self-certified compliance report (HW renewal)",
        "approval_ids": ["APR-010"],
        "domain": "ENVIRONMENT",
        "requirement_level": "required",
        "source_basis": "HOWM r.6 [SRC-013]",
        "source_url": (
            "https://upload.indiacode.nic.in/showfile"
            "?actid=AC_CH_60_926_00001_00001_1558607117075&type=rule"
            "&filename=final_hwm_rules_2016__english_.pdf"
        ),
        "document_role": "Applicant document",
        "issuer": "Occupier",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": None,
    },
    {
        "requirement_key": "DOC-008",
        "document_name": "District Authority NOC (Rule 144)",
        "approval_ids": ["APR-026"],
        "domain": "PROCESS",
        "requirement_level": "required",
        "source_basis": "Petroleum Rules 2002 [SRC-017]",
        "source_url": (
            "https://www.peso.gov.in/sites/default/files/2025-01/"
            "Petroleum%20Rules%202002%20-%20SOP.pdf"
        ),
        "document_role": "Authority document",
        "issuer": "District Authority",
        "accepted_mime_types": ["application/pdf"],
        "max_size_mb": None,
    },
]

MH_DEFERRED_DOCUMENTS: dict[str, str] = {
    "DOC-004": "linked approval (APR-008) outside batch-1",
    "DOC-005": "linked approval (APR-030) outside batch-1",
    "DOC-006": "linked approval (APR-032) outside batch-1",
    "DOC-007": "REQUIRES_OFFICIAL_CONFIRMATION + out of batch-1 scope",
    "DOC-009": "REQUIRES_OFFICIAL_CONFIRMATION (MSIHC r.7/r.10 detail)",
    "DOC-010": "REQUIRES_OFFICIAL_CONFIRMATION + out of batch-1 scope",
    "DOC-011": "UNKNOWN status + inferred practice + out of batch-1 scope",
    "DOC-012": "REQUIRES_OFFICIAL_CONFIRMATION (surfaced as evidence)",
}


def load_mh_document_requirements() -> list[dict[str, Any]]:
    """Return the batch-1 MH document requirements (4 rows)."""
    requirements = [dict(req) for req in MH_DOCUMENT_REQUIREMENTS]
    keys = [req["requirement_key"] for req in requirements]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate MH document requirement keys")
    return requirements
