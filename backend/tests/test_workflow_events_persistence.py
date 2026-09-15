"""Tests that workflow events are persisted on transitions."""
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from app.auth.permissions import SystemRole
from app.workflow.engine import execute_transition
from app.workflow.models import ApplicationStatus
from app.workflow.stages import StageType, WorkflowDefinition, WorkflowStage


class TestExecuteTransitionEventPersistence:
    """Test that execute_transition persists events when repository is provided."""

    def _make_workflow_def(self):
        """Create a simple workflow definition for testing."""
        return WorkflowDefinition(
            stages=[
                WorkflowStage(
                    key="validation",
                    label="Validation",
                    order=0,
                    type=StageType.VALIDATION,
                    sla_business_days=5,
                ),
                WorkflowStage(
                    key="review",
                    label="Review",
                    order=1,
                    type=StageType.REVIEW,
                    sla_business_days=10,
                ),
            ]
        )

    def test_event_persisted_when_repository_provided(self):
        """When events_repository is provided, event is persisted."""
        mock_repo = MagicMock()
        mock_repo.create.return_value = {"id": "event-1"}

        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
            workflow_def=self._make_workflow_def(),
            events_repository=mock_repo,
        )

        assert result.success
        mock_repo.create.assert_called_once()
        event_data = mock_repo.create.call_args[0][0]
        assert event_data["to_stage"] == "validation"
        assert event_data["action"] == "submit"

    def test_event_not_persisted_when_repository_not_provided(self):
        """When events_repository is not provided, no DB call is made."""
        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
            workflow_def=self._make_workflow_def(),
        )

        assert result.success
        # workflow_event is still in the result dict (in-memory)
        assert result.workflow_event is not None

    def test_event_includes_correct_fields(self):
        """Persisted event includes all required fields."""
        mock_repo = MagicMock()
        mock_repo.create.return_value = {"id": "event-1"}
        app_id = uuid4()
        user_id = uuid4()

        execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=user_id,
            user_role=SystemRole.APPLICANT,
            workflow_def=self._make_workflow_def(),
            events_repository=mock_repo,
        )

        event_data = mock_repo.create.call_args[0][0]
        assert event_data["application_id"] == str(app_id)
        assert event_data["performed_by_id"] == str(user_id)
        assert event_data["from_stage"] is None  # DRAFT has no previous stage
        assert event_data["to_stage"] == "validation"
        assert event_data["action"] == "submit"
        assert "created_at" in event_data
