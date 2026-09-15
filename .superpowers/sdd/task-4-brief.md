## Task 4: Persist workflow events on transitions

**Files:**
- Modify: `backend/app/workflow/engine.py` (add optional `events_repository` param)
- Modify: `backend/app/api/workflow.py` (inject repository, pass to engine)
- Create: `backend/tests/test_workflow_events_persistence.py`

**Interfaces:**
- Consumes: `WorkflowEventsRepository.create()` from Task 2
- Produces: Events persisted to DB on every transition in workflow API

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_workflow_events_persistence.py
"""Tests that workflow events are persisted on transitions."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

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
            user_role="APPLICANT",
            workflow_def=self._make_workflow_def(),
            events_repository=mock_repo,
        )

        assert result.success
        mock_repo.create.assert_called_once()
        event_data = mock_repo.create.call_args[0][0]
        assert event_data["to_status"] == "submitted"
        assert event_data["action"] == "submit"

    def test_event_not_persisted_when_repository_not_provided(self):
        """When events_repository is not provided, no DB call is made."""
        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role="APPLICANT",
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

        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=user_id,
            user_role="APPLICANT",
            workflow_def=self._make_workflow_def(),
            events_repository=mock_repo,
        )

        event_data = mock_repo.create.call_args[0][0]
        assert event_data["application_id"] == str(app_id)
        assert event_data["performed_by"] == str(user_id)
        assert event_data["from_status"] is None  # DRAFT has no previous stage
        assert event_data["to_status"] == "submitted"
        assert event_data["action"] == "submit"
        assert "created_at" in event_data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_workflow_events_persistence.py -v`
Expected: FAIL â€” `TypeError: execute_transition() got an unexpected keyword argument 'events_repository'`

- [ ] **Step 3: Modify engine.py to accept optional events_repository**

In `backend/app/workflow/engine.py`, modify `execute_transition()`:

```python
def execute_transition(
    *,
    application_id: UUID,
    current_status: ApplicationStatus,
    action: str,
    user_id: UUID,
    user_role: SystemRole,
    current_stage: str | None = None,
    workflow_def: WorkflowDefinition | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    events_repository=None,  # NEW â€” optional, for persisting events
) -> TransitionResult:
```

Then after creating the `event` dataclass (around line 281), add persistence logic:

```python
    # Create workflow event
    event = WorkflowEvent(
        id=uuid4(),
        application_id=application_id,
        from_stage=current_stage,
        to_stage=to_stage,
        action=action,
        performed_by=user_id,
        metadata=metadata or {},
        created_at=datetime.now(),
    )

    # Persist event if repository provided
    if events_repository is not None:
        events_repository.create({
            "application_id": str(event.application_id),
            "from_status": event.from_stage,
            "to_status": event.to_stage,
            "action": event.action,
            "performed_by": str(event.performed_by) if event.performed_by else None,
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat(),
        })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_workflow_events_persistence.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Modify workflow API to inject repository**

In `backend/app/api/workflow.py`, add the import and modify each transition endpoint:

```python
# Add to imports at top:
from app.api.deps import get_workflow_events_repository
from app.repositories.workflow_events import WorkflowEventsRepository
```

Then modify each transition endpoint (submit, advance, request_info, respond, approve, refuse, withdraw) to:

1. Add `events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository)` parameter
2. Pass `events_repository=events_repo` to `execute_transition()`

Example for `submit_application`:

```python
@router.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: UUID,
    repo: ApplicationsRepository = Depends(get_applications_repository),
    events_repo: WorkflowEventsRepository = Depends(get_workflow_events_repository),
    user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
):
    # ... existing code ...
    result = execute_transition(
        application_id=application_id,
        current_status=current_status,
        action="submit",
        user_id=user.user_id,
        user_role=user.role,
        events_repository=events_repo,  # NEW
    )
    # ... rest unchanged ...
```

Apply the same pattern to all 7 transition endpoints.

- [ ] **Step 6: Run existing workflow tests to verify no regressions**

Run: `cd backend && python -m pytest tests/test_workflow_engine.py -v`
Expected: All existing tests PASS (they don't pass events_repository, so events are not persisted â€” backward compatible)

- [ ] **Step 7: Commit**

```bash
git add backend/app/workflow/engine.py backend/app/api/workflow.py backend/tests/test_workflow_events_persistence.py
git commit -m "feat: persist workflow events on transitions via optional repository parameter"
```

---

