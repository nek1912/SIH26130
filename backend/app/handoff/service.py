"""Manual handoff service — pure transition logic, no I/O.

Nothing here contacts a government system: there is no HTTP client, no
polling, no scraping. Functions build or transform plain record dicts;
persistence and orchestration checks happen at the API layer.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.handoff.models import HandoffStatus, Verification
from app.seed.handoff import get_portal_entry

# Explicit allowed transitions over persisted statuses.
_TRANSITIONS: dict[HandoffStatus, frozenset[HandoffStatus]] = {
    HandoffStatus.HANDED_OFF: frozenset({HandoffStatus.SUBMITTED_EXTERNALLY}),
    HandoffStatus.SUBMITTED_EXTERNALLY: frozenset(
        {
            HandoffStatus.UNDER_EXTERNAL_REVIEW,
            HandoffStatus.APPROVED_EXTERNAL,
            HandoffStatus.REJECTED_EXTERNAL,
            HandoffStatus.RETURNED_FOR_CORRECTION,
        }
    ),
    HandoffStatus.UNDER_EXTERNAL_REVIEW: frozenset(
        {
            HandoffStatus.APPROVED_EXTERNAL,
            HandoffStatus.REJECTED_EXTERNAL,
            HandoffStatus.RETURNED_FOR_CORRECTION,
        }
    ),
    HandoffStatus.RETURNED_FOR_CORRECTION: frozenset(
        {HandoffStatus.SUBMITTED_EXTERNALLY}
    ),
    HandoffStatus.APPROVED_EXTERNAL: frozenset(),
    HandoffStatus.REJECTED_EXTERNAL: frozenset(),
}


class HandoffStateError(ValueError):
    """Raised for invalid handoff transitions or payloads (API -> 409/422)."""

    def __init__(self, detail: str, *, conflict: bool = False) -> None:
        super().__init__(detail)
        self.detail = detail
        self.conflict = conflict


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def is_ready_to_handoff(orchestration_status: str) -> bool:
    """Only a computed READY approval may be handed off. Nothing else."""
    return orchestration_status == "ready"


def can_transition(from_status: str, to_status: str) -> bool:
    try:
        current = HandoffStatus(from_status)
        target = HandoffStatus(to_status)
    except ValueError:
        return False
    return target in _TRANSITIONS.get(current, frozenset())


def prepare_initiation(
    application_id: str,
    approval_code: str,
    orchestration_status: str,
    reported_by: str,
    portal_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a handed_off record. Raises unless orchestration says READY.

    ``portal_entry`` overrides the legacy Gujarat portal catalog lookup
    (used by the jurisdiction-aware API layer, which resolves entries
    from the active RegulatoryPack). When None, the legacy lookup
    applies — GJ behavior is unchanged.
    """
    if not is_ready_to_handoff(orchestration_status):
        raise HandoffStateError(
            f"Approval {approval_code} is '{orchestration_status}', "
            "only READY approvals can be handed off",
            conflict=True,
        )
    entry = portal_entry if portal_entry is not None else get_portal_entry(
        approval_code
    )
    if entry is None:
        raise HandoffStateError(f"Unknown approval_code '{approval_code}'")
    return {
        "application_id": application_id,
        "approval_code": approval_code,
        "authority": entry["authority"],
        "external_system": entry["external_system"],
        "portal_url": entry["portal_url"],
        "portal_kind": entry["portal_kind"],
        "status": HandoffStatus.HANDED_OFF.value,
        "external_reference": None,
        "submitted_at": None,
        "last_external_update_at": None,
        "applicant_note": None,
        "reported_by": reported_by,
        "verification": Verification.USER_REPORTED.value,
        "verified_by": None,
        "verified_at": None,
    }


def _require_transition(record: dict[str, Any], to_status: HandoffStatus) -> None:
    if not can_transition(str(record.get("status")), to_status.value):
        raise HandoffStateError(
            f"Cannot move handoff from '{record.get('status')}' to '{to_status.value}'",
            conflict=True,
        )


def apply_submission(
    record: dict[str, Any],
    external_reference: str,
    actor: str,
    applicant_note: str | None = None,
) -> dict[str, Any]:
    """Record a manual external submission (HANDED_OFF or resubmit path)."""
    reference = (external_reference or "").strip()
    if not reference:
        raise HandoffStateError("external_reference must be a non-empty string")
    if len(reference) > 200:
        raise HandoffStateError("external_reference is unreasonably long")
    _require_transition(record, HandoffStatus.SUBMITTED_EXTERNALLY)
    updated = dict(record)
    updated.update(
        {
            "status": HandoffStatus.SUBMITTED_EXTERNALLY.value,
            "external_reference": reference,
            "submitted_at": _now_iso(),
            "last_external_update_at": _now_iso(),
            "reported_by": actor,
        }
    )
    if applicant_note is not None:
        updated["applicant_note"] = applicant_note
    return updated


def apply_report(
    record: dict[str, Any],
    to_status: str,
    actor: str,
    applicant_note: str | None = None,
) -> dict[str, Any]:
    """Record an applicant/staff-reported external status. Never verifies."""
    try:
        target = HandoffStatus(to_status)
    except ValueError:
        raise HandoffStateError(f"Unknown handoff status '{to_status}'") from None
    if target == HandoffStatus.HANDED_OFF:
        raise HandoffStateError("Cannot report back to handed_off")
    _require_transition(record, target)
    updated = dict(record)
    updated.update(
        {
            "status": target.value,
            "last_external_update_at": _now_iso(),
            "reported_by": actor,
            # Reporting never confers verification, even for approvals.
            "verification": Verification.USER_REPORTED.value,
            "verified_by": None,
            "verified_at": None,
        }
    )
    if applicant_note is not None:
        updated["applicant_note"] = applicant_note
    return updated


def apply_verification(
    record: dict[str, Any],
    verified_status: str,
    verifier: str,
) -> dict[str, Any]:
    """Staff-only: confirm the reported external status as authoritative."""
    try:
        target = HandoffStatus(verified_status)
    except ValueError:
        raise HandoffStateError(f"Unknown handoff status '{verified_status}'") from None
    current = str(record.get("status"))
    if current != target.value and not can_transition(current, target.value):
        raise HandoffStateError(
            f"Cannot verify handoff from '{current}' as '{target.value}'",
            conflict=True,
        )
    updated = dict(record)
    updated.update(
        {
            "status": target.value,
            "last_external_update_at": _now_iso(),
            "verification": Verification.STAFF_VERIFIED.value,
            "verified_by": verifier,
            "verified_at": _now_iso(),
        }
    )
    return updated


def handoff_event_metadata(
    record: dict[str, Any], action: str, actor: str
) -> dict[str, Any]:
    """Metadata payload for the workflow_events trail entry."""
    return {
        "handoff_id": record.get("id"),
        "approval_code": record.get("approval_code"),
        "external_system": record.get("external_system"),
        "external_reference": record.get("external_reference"),
        "status": record.get("status"),
        "verification": record.get("verification"),
        "action": action,
        "actor": actor,
    }
