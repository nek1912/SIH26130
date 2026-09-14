"""Tests for audit logging models."""
from __future__ import annotations

from app.audit.service import AuditEntry, create_audit_record


class TestAuditEntry:
    def test_create_record(self):
        entry = AuditEntry(
            action="application.submit",
            entity_type="Application",
            entity_id="app-123",
            user_id="user-456",
            application_id="app-123",
            new_values={"status": "submitted"},
        )
        record = create_audit_record(entry)
        assert record.action == "application.submit"
        assert record.entity_type == "Application"
        assert record.entity_id == "app-123"
        assert record.user_id == "user-456"
        assert record.application_id == "app-123"
        assert record.new_values == {"status": "submitted"}
        assert record.previous_values is None
        assert record.id is not None
        assert record.created_at is not None

    def test_with_previous_values(self):
        entry = AuditEntry(
            action="workflow.advance",
            entity_type="Application",
            entity_id="app-1",
            previous_values={"stage": "validation", "status": "under_review"},
            new_values={"stage": "review", "status": "under_review"},
        )
        record = create_audit_record(entry)
        assert record.previous_values is not None
        assert record.previous_values["stage"] == "validation"

    def test_minimal_entry(self):
        entry = AuditEntry(
            action="test.action",
            entity_type="Test",
            entity_id="t-1",
        )
        record = create_audit_record(entry)
        assert record.user_id is None
        assert record.ip_address is None
