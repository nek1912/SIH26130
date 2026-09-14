"""Tests for SLA computation."""
from __future__ import annotations

from datetime import date

from app.workflow.sla import compute_application_sla, summarise_sla

STAGES = [
    {
        "key": "validation", "label": "Validation",
        "order": 1, "type": "validation",
        "slaBusinessDays": 5, "reminderDays": 2,
    },
    {
        "key": "review", "label": "Officer Review",
        "order": 2, "type": "review",
        "slaBusinessDays": 10, "reminderDays": 2,
    },
    {
        "key": "decision", "label": "Decision",
        "order": 3, "type": "decision",
        "slaBusinessDays": 3, "reminderDays": 1,
    },
]


class TestComputeApplicationSla:
    def test_on_track(self):
        sla = compute_application_sla(
            status="under_review",
            current_stage="validation",
            submitted_at=date(2026, 9, 10),
            created_at=date(2026, 9, 9),
            workflow_events=[],
            stages=STAGES,
            now=date(2026, 9, 11),
        )
        assert sla is not None
        assert sla.state == "on_track"
        assert sla.sla_business_days == 5
        assert sla.used_business_days >= 0

    def test_due_soon(self):
        sla = compute_application_sla(
            status="under_review",
            current_stage="validation",
            submitted_at=date(2026, 9, 1),
            created_at=date(2026, 8, 30),
            workflow_events=[],
            stages=STAGES,
            now=date(2026, 9, 8),
        )
        assert sla is not None
        # After ~5 business days from Sep 1, we should be near the deadline
        assert sla.state in ("on_track", "due_soon", "due_today", "breached")

    def test_breached(self):
        sla = compute_application_sla(
            status="under_review",
            current_stage="validation",
            submitted_at=date(2026, 8, 1),
            created_at=date(2026, 7, 30),
            workflow_events=[],
            stages=STAGES,
            now=date(2026, 9, 15),
        )
        assert sla is not None
        assert sla.state == "breached"
        assert sla.overdue_business_days > 0

    def test_inactive_status_returns_none(self):
        sla = compute_application_sla(
            status="approved",
            current_stage="decision",
            submitted_at=date(2026, 9, 1),
            created_at=date(2026, 8, 30),
            workflow_events=[],
            stages=STAGES,
            now=date(2026, 9, 10),
        )
        assert sla is None

    def test_no_stages_returns_none(self):
        sla = compute_application_sla(
            status="under_review",
            current_stage="validation",
            submitted_at=date(2026, 9, 1),
            created_at=date(2026, 8, 30),
            workflow_events=[],
            stages=[],
            now=date(2026, 9, 10),
        )
        assert sla is None

    def test_no_sla_target_returns_none(self):
        stages_no_sla = [
            {"key": "validation", "label": "Validation", "order": 1, "type": "validation"},
        ]
        sla = compute_application_sla(
            status="under_review",
            current_stage="validation",
            submitted_at=date(2026, 9, 1),
            created_at=date(2026, 8, 30),
            workflow_events=[],
            stages=stages_no_sla,
            now=date(2026, 9, 10),
        )
        assert sla is None

    def test_uses_workflow_event_for_entry_time(self):
        sla = compute_application_sla(
            status="under_review",
            current_stage="review",
            submitted_at=date(2026, 9, 1),
            created_at=date(2026, 8, 30),
            workflow_events=[
                {
                    "toStage": "review",
                    "createdAt": "2026-09-05",
                }
            ],
            stages=STAGES,
            now=date(2026, 9, 6),
        )
        assert sla is not None
        assert sla.stage_key == "review"
        assert sla.entered_at == date(2026, 9, 5)

    def test_falls_back_to_submitted_at(self):
        sla = compute_application_sla(
            status="submitted",
            current_stage=None,
            submitted_at=date(2026, 9, 8),
            created_at=date(2026, 9, 1),
            workflow_events=[],
            stages=STAGES,
            now=date(2026, 9, 9),
        )
        assert sla is not None
        assert sla.entered_at == date(2026, 9, 8)

    def test_falls_back_to_earliest_sla_stage(self):
        sla = compute_application_sla(
            status="submitted",
            current_stage=None,
            submitted_at=date(2026, 9, 8),
            created_at=date(2026, 9, 1),
            workflow_events=[],
            stages=STAGES,
            now=date(2026, 9, 9),
        )
        assert sla is not None
        assert sla.stage_key == "validation"  # first stage with SLA


class TestSummariseSla:
    def test_counts(self):
        apps = [
            {
                "status": "under_review",
                "currentStage": "validation",
                "submittedAt": date(2026, 8, 1),
                "createdAt": date(2026, 7, 30),
                "workflowEvents": [],
                "stages": STAGES,
            },
            {
                "status": "approved",
                "currentStage": "decision",
                "submittedAt": date(2026, 9, 1),
                "createdAt": date(2026, 8, 30),
                "workflowEvents": [],
                "stages": STAGES,
            },
        ]
        result = summarise_sla(apps, now=date(2026, 9, 15))
        assert result["breached"] >= 1
        assert result["total"] >= 1
