"""SLA computation for applications.

Ported from Digital-Permit-Platform/src/lib/sla.ts.

Each workflow stage can define slaBusinessDays (a target number of working
days to complete that stage). This module computes where an application is
against that target.

Uses python-dateutil for business day calculation.

Source: Digital-Permit-Platform/src/lib/sla.ts (137 lines)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from dateutil.relativedelta import relativedelta

from app.workflow.models import ACTIVE_STATUSES, ApplicationStatus


@dataclass
class SlaInfo:
    stage_key: str
    stage_label: str
    sla_business_days: int
    entered_at: date
    due_date: date
    used_business_days: int
    remaining_business_days: int
    overdue_business_days: int
    state: str  # "on_track" | "due_soon" | "due_today" | "breached"


def _to_date(value: Any) -> date | None:
    """Convert a date, datetime, or ISO string to a date."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except (ValueError, TypeError):
            return None
    return None


def _add_business_days(start: date, days: int) -> date:
    """Add business days to a date (excluding weekends).

    This is a simplified implementation. For production use with Indian
    holidays, a proper holiday calendar should be used.
    """
    current = start
    added = 0
    while added < days:
        current += relativedelta(days=1)
        # Monday=0 ... Sunday=6; skip weekends
        if current.weekday() < 5:
            added += 1
    return current


def _difference_in_business_days(start: date, end: date) -> int:
    """Count business days between two dates (end - start).

    Negative if end is before start.
    """
    if end < start:
        return -_difference_in_business_days(end, start)

    count = 0
    current = start
    while current < end:
        current += relativedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return count


def compute_application_sla(
    status: str | ApplicationStatus,
    current_stage: str | None,
    submitted_at: Any,
    created_at: Any,
    workflow_events: list[dict[str, Any]] | None,
    stages: list[dict[str, Any]],
    now: date | None = None,
) -> SlaInfo | None:
    """Compute the SLA position for an application against its current stage.

    Returns None when no SLA applies (inactive status, no stages, or
    the current stage has no SLA target).
    """
    if now is None:
        now = date.today()

    # Normalize status
    if isinstance(status, str):
        try:
            status = ApplicationStatus(status)
        except ValueError:
            return None

    if status not in ACTIVE_STATUSES:
        return None

    if not stages:
        return None

    # Find the current stage
    stage = None
    if current_stage:
        stage = next((s for s in stages if s.get("key") == current_stage), None)
    if not stage:
        # Fall back to the earliest stage with an SLA target
        stage = next(
            (
                s
                for s in sorted(stages, key=lambda s: s.get("order", 0))
                if s.get("slaBusinessDays") and s.get("slaBusinessDays", 0) > 0
            ),
            None,
        )

    sla_days = stage.get("slaBusinessDays") if stage else None
    if not sla_days or sla_days <= 0:
        return None

    # Determine when the application entered this stage
    entered_at: date | None = None
    if workflow_events and stage:
        stage_events = [
            e for e in workflow_events if e.get("toStage") == stage["key"]
        ]
        for e in sorted(stage_events, key=lambda x: x.get("createdAt", ""), reverse=True):
            d = _to_date(e.get("createdAt"))
            if d:
                entered_at = d
                break

    if not entered_at:
        entered_at = _to_date(submitted_at)
    if not entered_at:
        entered_at = _to_date(created_at)
    if not entered_at:
        return None

    due_date = _add_business_days(entered_at, sla_days)
    used = _difference_in_business_days(entered_at, now)
    remaining = _difference_in_business_days(now, due_date)
    reminder = stage.get("reminderDays", 2) if stage else 2

    if remaining < 0:
        state = "breached"
    elif remaining == 0:
        state = "due_today"
    elif remaining <= reminder:
        state = "due_soon"
    else:
        state = "on_track"

    return SlaInfo(
        stage_key=stage["key"] if stage else "",
        stage_label=stage.get("label", "") if stage else "",
        sla_business_days=sla_days,
        entered_at=entered_at,
        due_date=due_date,
        used_business_days=max(0, used),
        remaining_business_days=remaining,
        overdue_business_days=max(0, -remaining),
        state=state,
    )


def summarise_sla(
    applications: list[dict[str, Any]],
    now: date | None = None,
) -> dict[str, int]:
    """Roll up a list of applications into headline SLA counts for a banner."""
    breached = 0
    due_today = 0
    due_soon = 0

    for app in applications:
        sla = compute_application_sla(
            status=app.get("status", ""),
            current_stage=app.get("currentStage"),
            submitted_at=app.get("submittedAt"),
            created_at=app.get("createdAt"),
            workflow_events=app.get("workflowEvents"),
            stages=app.get("stages", []),
            now=now,
        )
        if sla is None:
            continue
        if sla.state == "breached":
            breached += 1
        elif sla.state == "due_today":
            due_today += 1
        elif sla.state == "due_soon":
            due_soon += 1

    return {
        "breached": breached,
        "dueToday": due_today,
        "dueSoon": due_soon,
        "total": breached + due_today + due_soon,
    }
