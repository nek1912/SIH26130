"""Audit logging models and service.

Ported from Digital-Permit-Platform/src/lib/audit.ts.

Immutable append-only audit trail. Every mutation records actor, entity,
action, and optional before/after value snapshots.

Source: Digital-Permit-Platform/src/lib/audit.ts (70 lines)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class AuditEntry:
    """An audit log entry to be written."""

    action: str
    entity_type: str
    entity_id: str
    user_id: str | None = None
    application_id: str | None = None
    previous_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class AuditRecord:
    """A persisted audit log record."""

    id: UUID
    action: str
    entity_type: str
    entity_id: str
    user_id: str | None
    application_id: str | None
    previous_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


def create_audit_record(entry: AuditEntry) -> AuditRecord:
    """Create an audit record from an entry (in-memory, no DB).

    This is the deterministic part. The actual DB write is handled
    by the data access layer (not yet implemented).
    """
    return AuditRecord(
        id=uuid4(),
        action=entry.action,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        user_id=entry.user_id,
        application_id=entry.application_id,
        previous_values=entry.previous_values,
        new_values=entry.new_values,
        ip_address=entry.ip_address,
        user_agent=entry.user_agent,
        created_at=datetime.now(),
    )
