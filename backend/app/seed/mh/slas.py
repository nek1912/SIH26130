"""Maharashtra v5 batch-1 SLA display metadata (Phase 6).

READ-ONLY data: target durations, units, clock-start events, and
provenance for the 10 SLA rows referenced by batch-1 rule timelines
(reference audit: R-002→SLA-032, R-018→SLA-004, R-026→SLA-008,
R-028→SLA-013/040/047, R-030→SLA-045, R-043/R-044→SLA-031,
R-089→SLA-011/012). The Phase-5 list additionally named SLA-009
(APR-020, rule R-027 deferred), SLA-029 (APR-045, no batch-1 rule),
and SLA-039 (APR-058, rule R-065 deferred) — all three corrected to
deferred below. The other 37 register rows are out of batch-1 scope.

Every value is verbatim register text: UNKNOWN / "-" / NOT_STATED
clock-starts and values are preserved, never substituted; working
days are never converted to calendar days; no deadline is computed.
SLA-013 is REQUIRES_OFFICIAL_CONFIRMATION and travels with that
status (display metadata blocks nothing).
"""
from __future__ import annotations

from app.workflow.sla import SlaMetadata


def _S(
    sla_id: str,
    approval_id: str,
    service: str,
    target_value: str,
    target_unit: str,
    clock_start: str,
    sla_source_type: str,
    timeline_type: str,
    source_ids: tuple[str, ...],
    conflict_id: str = "",
    notes: str = "",
    effective_date: str = "",
    exact_locator: str = "",
    final_status: str = "",
    consent_types: str = "",
) -> SlaMetadata:
    return SlaMetadata(
        sla_id=sla_id,
        approval_id=approval_id,
        service=service,
        target_value=target_value,
        target_unit=target_unit,
        clock_start=clock_start,
        sla_source_type=sla_source_type,
        timeline_type=timeline_type,
        source_ids=source_ids,
        conflict_id=conflict_id,
        notes=notes,
        effective_date=effective_date,
        exact_locator=exact_locator,
        final_status=final_status,
        consent_types=consent_types,
        record_state="ACTIVE",
    )


MH_SLA_RECORDS: list[SlaMetadata] = [
    _S("SLA-004", "APR-010", "HW authorisation", "120", "DAYS",
       "Receipt of complete application", "STATUTORY_RULE", "LEGAL",
       ("SRC-013",), final_status="VERIFIED"),
    _S("SLA-008", "APR-019", "CLRA principal employer registration",
       "7", "DAYS", "RTS", "RTS_NOTIFIED", "RTS/SERVICE", ("SRC-031",),
       notes="Deemed registration on expiry (SRC-070)",
       final_status="VERIFIED"),
    _S("SLA-011", "APR-022", "ISMW registration", "21", "DAYS", "RTS",
       "RTS_NOTIFIED", "RTS/SERVICE", ("SRC-031",),
       final_status="VERIFIED"),
    _S("SLA-012", "APR-022", "ISMW licences", "7", "DAYS", "RTS",
       "RTS_NOTIFIED", "RTS/SERVICE", ("SRC-031",),
       final_status="VERIFIED"),
    _S("SLA-013", "APR-023", "Boiler registration",
       "43 (boiler made in MH) / 50 (made outside MH) per mahaboiler; "
       "50 per Labour RTS page", "DAYS", "RTS", "RTS_NOTIFIED",
       "RTS/SERVICE", ("SRC-031",), conflict_id="CON-008",
       notes="Notified under legacy framework",
       final_status="REQUIRES_OFFICIAL_CONFIRMATION"),
    _S("SLA-031", "APR-043", "CGWA NOC", "NOT_STATED", "-",
       "-", "STATUTORY_GUIDELINE", "LEGAL", ("SRC-052",),
       notes="Guidelines state no decision timeline",
       final_status="UNKNOWN"),
    _S("SLA-032", "APR-001", "EC appraisal", "UNKNOWN", "-",
       "-", "-", "ADMINISTRATIVE", (),
       notes="Not extracted in this pack", final_status="UNKNOWN"),
    _S("SLA-040", "APR-023",
       "Boiler registration - Inspector fixes examination date",
       "30 (or shorter State period); notice >=10; report to CI "
       "within 7", "DAYS", "Receipt of application", "STATUTE",
       "LEGAL", ("SRC-034",), conflict_id="CON-020",
       notes="Statutory step timeline, not end-to-end",
       final_status="VERIFIED"),
    _S("SLA-045", "APR-026",
       "District Authority NOC for petroleum licence", "3", "MONTHS",
       "Receipt of application by DA", "STATUTE (rules)", "LEGAL",
       ("SRC-117",), final_status="VERIFIED_CONDITIONAL"),
    _S("SLA-047", "APR-023", "Boiler registration (portal)", "30",
       "DAYS", "Portal-stated", "PORTAL (legacy basis 'not stated')",
       "PORTAL", ("SRC-136",), conflict_id="CON-020",
       final_status="VERIFIED_CONDITIONAL"),
]

MH_LOADED_SLA_IDS: frozenset[str] = frozenset({
    "SLA-004", "SLA-008", "SLA-011", "SLA-012", "SLA-013", "SLA-031",
    "SLA-032", "SLA-040", "SLA-045", "SLA-047",
})

MH_DEFERRED_SLAS: dict[str, str] = {
    "SLA-009": "approval APR-020 has no batch-1 rule (R-027 deferred)",
    "SLA-029": "approval APR-045 has no batch-1 rule",
    "SLA-039": "approval APR-058 has no batch-1 rule (R-065 deferred)",
}


def load_mh_sla_records() -> list[SlaMetadata]:
    """Return the 10 batch-1-referenced MH SLA records (display only)."""
    records = list(MH_SLA_RECORDS)
    ids = [r.sla_id for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate MH SLA IDs")
    if set(ids) != set(MH_LOADED_SLA_IDS):
        raise ValueError("MH SLA contents drifted from MH_LOADED_SLA_IDS")
    return records
