"""Deadline computation for obligations.

Ported from compliance-grid/src/gates/compute-due-date.ts.

Computes the deadline for an obligation given an EntityProfile and a
reference date. Returns None when the deadline cannot be computed
(e.g. event-offset deadline with no matching event on the entity).

Indian fiscal year awareness:
- Annual: year ends March 31
- Quarterly: months 3, 6, 9, 12
- Half-yearly: March 31 and September 30

Source: compliance-grid/src/gates/compute-due-date.ts (79 lines)
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.rules.models import EntityProfile, Obligation


def _current_period_end(frequency: str, reference: date) -> date | None:
    """Compute the last day of the current period for the given frequency.

    Returns None for frequencies where 'current period' is not meaningful
    with a period-offset deadline.
    """
    year = reference.year
    month = reference.month

    match frequency:
        case "monthly":
            # Last day of current month
            if month == 12:
                return date(year + 1, 1, 1) - timedelta(days=1)
            return date(year, month + 1, 1) - timedelta(days=1)

        case "quarterly":
            # Indian fiscal quarters end: Mar 31, Jun 30, Sep 30, Dec 31
            quarter_end_month = month - (month % 3) + 3
            if quarter_end_month == 12:
                return date(year, 12, 31)
            return date(year, quarter_end_month + 1, 1) - timedelta(days=1)

        case "half-yearly":
            # Indian fiscal half-years end: Sep 30, Mar 31
            if month < 6:
                return date(year, 9, 30) if month < 3 else date(year, 9, 30)
            return date(year, 3, 31) if month < 9 else date(year, 3, 31)

        case "annual":
            # Indian fiscal year ends March 31
            fy_end = date(year, 3, 31)
            if reference > fy_end:
                fy_end = date(year + 1, 3, 31)
            return fy_end

        case "one-time" | "event-driven":
            return None

    return None


def compute_due_date(
    obligation: Obligation,
    entity: EntityProfile,
    reference: date,
) -> date | None:
    """Compute the deadline for an obligation.

    Returns None when the deadline cannot be determined (e.g. event-offset
    with no matching event field on the entity).

    Callers decide what to do with a deadline that is in the past relative
    to 'today' (typically: flag as missed).
    """
    rule = obligation.deadline_rule

    if rule.kind == "fixed-date":
        candidate = date(reference.year, rule.month, rule.day)
        if candidate < reference:
            candidate = date(reference.year + 1, rule.month, rule.day)
        return candidate

    if rule.kind == "event-offset":
        entity_dict: dict[str, Any] = entity.model_dump()
        raw = entity_dict.get(rule.event)
        if raw is None:
            return None
        if isinstance(raw, str):
            try:
                event_date = date.fromisoformat(raw)
            except (ValueError, TypeError):
                return None
            return event_date + timedelta(days=rule.days)
        if isinstance(raw, date):
            return raw + timedelta(days=rule.days)
        return None

    if rule.kind == "period-offset":
        period_end = _current_period_end(obligation.frequency, reference)
        if period_end is None:
            return None
        return period_end + timedelta(days=rule.days)

    return None
