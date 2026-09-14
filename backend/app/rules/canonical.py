"""Canonical key generation and versioning for obligations.

Ported from compliance-grid/src/gates/canonicalize.ts and version.ts.

The canonical key uniquely identifies an obligation within the system.
Format: {instrument_id}|{section}|{type}

Source: compliance-grid/src/gates/canonicalize.ts (29 lines)
        compliance-grid/src/gates/version.ts (14 lines)
"""
from __future__ import annotations

import re

from app.rules.models import ObligationType


def canonicalize(
    instrument_id: str,
    section: str | None,
    type: ObligationType,
) -> str:
    """Compute the deterministic canonical key for an obligation.

    Format uses '|' as separator. instrument_id may contain '/' so that
    separator is unsafe. Section may be None (whole-instrument obligations);
    we emit an empty middle segment so the format stays sortable and parseable.

    Examples:
        canonicalize("IN/companies-act-2013", None, "filing")
        -> "IN/companies-act-2013||filing"

        canonicalize("IN-KA/factories-rules-1969", "r.105", "filing")
        -> "IN-KA/factories-rules-1969|r.105|filing"
    """
    if not instrument_id:
        raise ValueError("canonicalize: instrument_id must be a non-empty string")
    if not type:
        raise ValueError("canonicalize: type must be a non-empty string")
    return f"{instrument_id}|{section or ''}|{type.value}"


_VERSION_RE = re.compile(r"^\d+$")


def version(current: str | None = None) -> str:
    """Mint the next version string for an obligation.

    Uses monotonic integer-strings ('1', '2', '3', ...).
    When current is None (first commit), returns '1'.
    """
    if current is None:
        return "1"
    if not current or not _VERSION_RE.match(current):
        raise ValueError(
            f"version: expected a non-negative integer-string, got {current!r}"
        )
    return str(int(current) + 1)
