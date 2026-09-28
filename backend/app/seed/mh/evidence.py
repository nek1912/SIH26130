"""Maharashtra v5 batch-1 evidence gaps (Phase 4).

Advisory/traceability metadata only. These records NEVER create
applicability rules and NEVER flip a deterministic result to APPLIES
or DOES_NOT_APPLY; relevant gaps surface through the existing
fail-closed evidence path as INSUFFICIENT_DATA.

Included (explicit v5 linkage to a batch-1 approval):
- UR-06 (EIA 5(f)+8(a) combination, OPEN) -> APR-001 via R-074.
- UR-11 (Insecticides licensing-officer identity, OPEN) -> APR-055
  (R-067's own authority string records the same gap).
- DOC-012 (NOCAP abstraction-detail list not extracted,
  REQUIRES_CONFIRMATION, LOW) -> APR-043 via documents.csv used_for.

Evaluated but NOT surfaced (with reason):
- CON-004 (boiler citation conflict): resolution adopts the 2025
  statute, which R-028 already encodes; no open question remains.
- CON-009 (shed exclusion): resolved by quashing; F-BLD-02 already
  deprecated.
- CON-011 (Class-B wording): resolution implements the Act test,
  which R-030 already encodes.
- CON-014: concerns R-029 (do-not-implement).
- CON-019 (GW parallel regimes): encodable part (CGWA NOC) is in
  R-043/044/046; the MH-Act overlay belongs to R-097 (held).
- UR-09 (DSB/LMS workflow): procedure display, not a registration
  trigger; no open applicability question for R-028.
- UR-15 (MWRRA areas): belongs to R-097 (held), not the exemption
  rules.
"""
from __future__ import annotations

from app.regulatory.evidence import EvidenceRecord, EvidenceStatus

MH_EVIDENCE_GAPS: list[EvidenceRecord] = [
    EvidenceRecord(
        evidence_id="UR-06",
        subject="EIA 5(f) + 8(a) combination (R-074)",
        status=EvidenceStatus.NOT_ESTABLISHED,
        verified_scope=(
            "No authoritative statement on the 5(f)+8(a) combination "
            "found in the v5 research (cut-off 26-09-2026)."
        ),
        unresolved_question=(
            "Authoritative statement on 5(f)+8(a) duplicate-EC risk "
            "(MoEFCC OM/notification/court order)."
        ),
        source_reference="v5 unresolved_items UR-06 (OPEN)",
        notes="Fail closed: R-074 stays out of deterministic orchestration.",
        flags=["v5:UR-06", "OPEN"],
    ),
    EvidenceRecord(
        evidence_id="UR-11",
        subject=(
            "Chemical branch authorities in Maharashtra "
            "(Insecticides licensing officer)"
        ),
        status=EvidenceStatus.NOT_ESTABLISHED,
        verified_scope=(
            "Notified licensing officer and forms not located; R-067 "
            "authority recorded as UNKNOWN identity."
        ),
        unresolved_question=(
            "State notification under Insecticides Act s.13 naming "
            "the licensing officer."
        ),
        source_reference="v5 unresolved_items UR-11 (OPEN, carried from v4)",
        notes="Authority routing gap; R-067 applicability unaffected.",
        flags=["v5:UR-11", "OPEN"],
    ),
    EvidenceRecord(
        evidence_id="DOC-012",
        subject="Hydrogeological/abstraction details for NOCAP",
        status=EvidenceStatus.PARTIAL,
        verified_scope=(
            "CGWA guidelines require hydrogeological/abstraction "
            "details for NOCAP (SRC-052)."
        ),
        unresolved_question=(
            "Exact detail list not extracted from the guidelines."
        ),
        source_reference="v5 documents DOC-012 (REQUIRES_OFFICIAL_CONFIRMATION)",
        notes="Document-readiness gap for APR-043 dossiers.",
        flags=["v5:DOC-012", "REQUIRES_OFFICIAL_CONFIRMATION"],
    ),
]

# Hint-only approval mapping (never a rule). Mirrors the GJ
# EVIDENCE_TO_APPROVALS contract consumed by the pack helper.
MH_EVIDENCE_HINTS: dict[str, list[str]] = {
    "UR-06": ["APR-001"],
    "UR-11": ["APR-055"],
    "DOC-012": ["APR-043"],
}


def load_mh_evidence_gaps() -> list[EvidenceRecord]:
    """Return the batch-1 MH evidence records (3, advisory only)."""
    return list(MH_EVIDENCE_GAPS)
