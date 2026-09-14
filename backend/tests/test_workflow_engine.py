"""Tests for workflow engine, transitions, and assignments.

Covers:
  - Valid transitions (all paths)
  - Invalid transitions (wrong status, wrong action)
  - Role/permission enforcement
  - Assignment logic
  - Ownership/access
  - Workflow event creation
  - Audit trail
  - Concurrency/duplicate transition protection
  - SLA state after workflow changes
  - Stage definitions
"""

from __future__ import annotations

from uuid import uuid4

from app.auth.permissions import Permission, SystemRole
from app.workflow.assignments import (
    can_assign,
    can_decide,
    can_review,
    get_active_statuses,
    get_staff_queue_filter,
    is_terminal_status,
    status_display_name,
)
from app.workflow.engine import (
    TRANSITION_RULES,
    can_transition,
    execute_transition,
)
from app.workflow.models import ApplicationStatus
from app.workflow.stages import StageType, WorkflowDefinition, WorkflowStage

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

SAMPLE_WORKFLOW = WorkflowDefinition(
    stages=[
        WorkflowStage(
            key="validation", label="Validation", order=0,
            type=StageType.VALIDATION, sla_business_days=5,
        ),
        WorkflowStage(
            key="review", label="Review", order=1,
            type=StageType.REVIEW, sla_business_days=10,
        ),
        WorkflowStage(
            key="decision", label="Decision", order=2,
            type=StageType.DECISION, sla_business_days=5,
        ),
    ]
)


# ---------------------------------------------------------------------------
# 1. Stage definitions
# ---------------------------------------------------------------------------


class TestWorkflowStage:
    def test_stage_creation(self):
        stage = WorkflowStage(
            key="review", label="Review", order=0, type=StageType.REVIEW
        )
        assert stage.key == "review"
        assert stage.type == StageType.REVIEW

    def test_stage_defaults(self):
        stage = WorkflowStage(
            key="x", label="X", order=0, type=StageType.CUSTOM
        )
        assert stage.sla_business_days is None
        assert stage.visible_to_applicant is True
        assert stage.required_actions == []


class TestWorkflowDefinition:
    def test_get_stage(self):
        assert SAMPLE_WORKFLOW.get_stage("review") is not None
        assert SAMPLE_WORKFLOW.get_stage("nonexistent") is None

    def test_get_first_stage(self):
        first = SAMPLE_WORKFLOW.get_first_stage()
        assert first is not None
        assert first.key == "validation"

    def test_get_next_stage(self):
        nxt = SAMPLE_WORKFLOW.get_next_stage("validation")
        assert nxt is not None
        assert nxt.key == "review"

    def test_get_next_stage_last(self):
        nxt = SAMPLE_WORKFLOW.get_next_stage("decision")
        assert nxt is None

    def test_is_terminal(self):
        assert SAMPLE_WORKFLOW.is_terminal("decision") is True
        assert SAMPLE_WORKFLOW.is_terminal("validation") is False

    def test_empty_workflow(self):
        empty = WorkflowDefinition(stages=[])
        assert empty.get_first_stage() is None
        assert empty.is_terminal("anything") is False


# ---------------------------------------------------------------------------
# 2. Transition rules completeness
# ---------------------------------------------------------------------------


class TestTransitionRules:
    def test_all_statuses_have_rules(self):
        """Every non-terminal status should have at least one outgoing rule."""
        terminal = {
            ApplicationStatus.APPROVED,
            ApplicationStatus.REFUSED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.CANCELLED,
        }
        for status in ApplicationStatus:
            if status in terminal:
                continue
            outgoing = [
                a for (s, a) in TRANSITION_RULES if s == status
            ]
            assert len(outgoing) > 0, f"Status {status} has no outgoing rules"

    def test_submit_goes_to_submitted(self):
        target, perm = TRANSITION_RULES[(ApplicationStatus.DRAFT, "submit")]
        assert target == ApplicationStatus.SUBMITTED
        assert perm == Permission.APPLICATION_CREATE

    def test_approve_goes_to_approved(self):
        target, perm = TRANSITION_RULES[(ApplicationStatus.UNDER_REVIEW, "approve")]
        assert target == ApplicationStatus.APPROVED
        assert perm == Permission.APPLICATION_DECIDE

    def test_refuse_goes_to_refused(self):
        target, perm = TRANSITION_RULES[(ApplicationStatus.UNDER_REVIEW, "refuse")]
        assert target == ApplicationStatus.REFUSED
        assert perm == Permission.APPLICATION_DECIDE

    def test_withdraw_from_multiple_statuses(self):
        """Withdraw should be possible from multiple active statuses."""
        withdrawable = [
            status
            for (status, action) in TRANSITION_RULES
            if action == "withdraw"
        ]
        assert ApplicationStatus.SUBMITTED in withdrawable
        assert ApplicationStatus.UNDER_REVIEW in withdrawable


# ---------------------------------------------------------------------------
# 3. can_transition — valid transitions
# ---------------------------------------------------------------------------


class TestCanTransition:
    def test_draft_submit_applicant(self):
        ok, target, err = can_transition(
            ApplicationStatus.DRAFT, "submit", SystemRole.APPLICANT
        )
        assert ok is True
        assert target == ApplicationStatus.SUBMITTED
        assert err is None

    def test_submitted_advance_reviewer(self):
        ok, target, err = can_transition(
            ApplicationStatus.SUBMITTED, "advance", SystemRole.REVIEWER
        )
        assert ok is True
        assert target == ApplicationStatus.UNDER_REVIEW

    def test_under_review_approve_manager(self):
        ok, target, err = can_transition(
            ApplicationStatus.UNDER_REVIEW, "approve", SystemRole.MANAGER
        )
        assert ok is True
        assert target == ApplicationStatus.APPROVED

    def test_under_review_refuse_admin(self):
        ok, target, err = can_transition(
            ApplicationStatus.UNDER_REVIEW, "refuse", SystemRole.ADMIN
        )
        assert ok is True
        assert target == ApplicationStatus.REFUSED

    def test_submitted_withdraw_applicant(self):
        ok, target, err = can_transition(
            ApplicationStatus.SUBMITTED, "withdraw", SystemRole.APPLICANT
        )
        assert ok is True
        assert target == ApplicationStatus.WITHDRAWN

    def test_returned_respond_applicant(self):
        ok, target, err = can_transition(
            ApplicationStatus.RETURNED, "respond", SystemRole.APPLICANT
        )
        assert ok is True
        assert target == ApplicationStatus.UNDER_REVIEW

    def test_incomplete_respond_applicant(self):
        ok, target, err = can_transition(
            ApplicationStatus.INCOMPLETE, "respond", SystemRole.APPLICANT
        )
        assert ok is True
        assert target == ApplicationStatus.UNDER_REVIEW

    def test_under_review_request_info_reviewer(self):
        ok, target, err = can_transition(
            ApplicationStatus.UNDER_REVIEW, "request_info", SystemRole.REVIEWER
        )
        assert ok is True
        assert target == ApplicationStatus.RETURNED


# ---------------------------------------------------------------------------
# 4. can_transition — invalid transitions
# ---------------------------------------------------------------------------


class TestCanTransitionInvalid:
    def test_unknown_action(self):
        ok, target, err = can_transition(
            ApplicationStatus.DRAFT, "bogus", SystemRole.APPLICANT
        )
        assert ok is False
        assert target is None
        assert "not allowed" in err

    def test_submit_from_submitted(self):
        ok, target, err = can_transition(
            ApplicationStatus.SUBMITTED, "submit", SystemRole.APPLICANT
        )
        assert ok is False
        assert "not allowed" in err

    def test_approve_from_draft(self):
        ok, target, err = can_transition(
            ApplicationStatus.DRAFT, "approve", SystemRole.ADMIN
        )
        assert ok is False

    def test_advance_from_approved(self):
        ok, target, err = can_transition(
            ApplicationStatus.APPROVED, "advance", SystemRole.REVIEWER
        )
        assert ok is False

    def test_respond_from_draft(self):
        ok, target, err = can_transition(
            ApplicationStatus.DRAFT, "respond", SystemRole.APPLICANT
        )
        assert ok is False


# ---------------------------------------------------------------------------
# 5. Role/permission enforcement
# ---------------------------------------------------------------------------


class TestPermissionEnforcement:
    def test_applicant_cannot_approve(self):
        ok, target, err = can_transition(
            ApplicationStatus.UNDER_REVIEW, "approve", SystemRole.APPLICANT
        )
        assert ok is False
        assert "Permission" in err

    def test_reviewer_cannot_decide(self):
        ok, target, err = can_transition(
            ApplicationStatus.UNDER_REVIEW, "approve", SystemRole.REVIEWER
        )
        assert ok is False
        assert "Permission" in err

    def test_applicant_cannot_advance(self):
        ok, target, err = can_transition(
            ApplicationStatus.SUBMITTED, "advance", SystemRole.APPLICANT
        )
        assert ok is False

    def test_reviewer_cannot_assign(self):
        ok, target, err = can_transition(
            ApplicationStatus.UNDER_REVIEW, "assign", SystemRole.REVIEWER
        )
        assert ok is False

    def test_manager_can_assign(self):
        ok, target, err = can_transition(
            ApplicationStatus.UNDER_REVIEW, "assign", SystemRole.MANAGER
        )
        assert ok is True

    def test_admin_can_delete_cancel(self):
        ok, target, err = can_transition(
            ApplicationStatus.DRAFT, "cancel", SystemRole.ADMIN
        )
        assert ok is True

    def test_manager_cannot_delete_cancel(self):
        ok, target, err = can_transition(
            ApplicationStatus.DRAFT, "cancel", SystemRole.MANAGER
        )
        assert ok is False


# ---------------------------------------------------------------------------
# 6. execute_transition
# ---------------------------------------------------------------------------


class TestExecuteTransition:
    def test_submit_creates_events(self):
        app_id = uuid4()
        user_id = uuid4()
        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=user_id,
            user_role=SystemRole.APPLICANT,
            workflow_def=SAMPLE_WORKFLOW,
        )
        assert result.success is True
        assert result.new_status == ApplicationStatus.SUBMITTED
        assert result.stage_key == "validation"
        assert result.workflow_event is not None
        assert result.workflow_event["action"] == "submit"
        assert result.audit_record is not None
        assert result.audit_record.action == "workflow.submit"

    def test_submit_with_workflow_sets_first_stage(self):
        app_id = uuid4()
        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
            workflow_def=SAMPLE_WORKFLOW,
        )
        assert result.stage_key == "validation"

    def test_advance_moves_to_next_stage(self):
        app_id = uuid4()
        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.SUBMITTED,
            action="advance",
            user_id=uuid4(),
            user_role=SystemRole.REVIEWER,
            current_stage="validation",
            workflow_def=SAMPLE_WORKFLOW,
        )
        assert result.success is True
        assert result.stage_key == "review"

    def test_approve_records_decision(self):
        app_id = uuid4()
        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.UNDER_REVIEW,
            action="approve",
            user_id=uuid4(),
            user_role=SystemRole.MANAGER,
            current_stage="review",
            metadata={"reason": "All documents verified"},
        )
        assert result.success is True
        assert result.new_status == ApplicationStatus.APPROVED
        assert result.workflow_event["metadata"]["reason"] == "All documents verified"

    def test_invalid_transition_returns_error(self):
        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.APPROVED,
            action="advance",
            user_id=uuid4(),
            user_role=SystemRole.REVIEWER,
        )
        assert result.success is False
        assert result.error is not None

    def test_event_has_correct_ids(self):
        app_id = uuid4()
        user_id = uuid4()
        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=user_id,
            user_role=SystemRole.APPLICANT,
        )
        assert result.workflow_event["application_id"] == str(app_id)
        assert result.workflow_event["performed_by"] == str(user_id)

    def test_audit_record_has_application_id(self):
        app_id = uuid4()
        result = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        assert result.audit_record.application_id == str(app_id)


# ---------------------------------------------------------------------------
# 7. Assignment logic
# ---------------------------------------------------------------------------


class TestAssignment:
    def test_manager_can_assign(self):
        assert can_assign(SystemRole.MANAGER) is True

    def test_admin_can_assign(self):
        assert can_assign(SystemRole.ADMIN) is True

    def test_reviewer_cannot_assign(self):
        assert can_assign(SystemRole.REVIEWER) is False

    def test_applicant_cannot_assign(self):
        assert can_assign(SystemRole.APPLICANT) is False

    def test_reviewer_can_review(self):
        assert can_review(SystemRole.REVIEWER) is True

    def test_applicant_cannot_review(self):
        assert can_review(SystemRole.APPLICANT) is False

    def test_manager_can_decide(self):
        assert can_decide(SystemRole.MANAGER) is True

    def test_reviewer_cannot_decide(self):
        assert can_decide(SystemRole.REVIEWER) is False


# ---------------------------------------------------------------------------
# 8. Queue filter
# ---------------------------------------------------------------------------


class TestQueueFilter:
    def test_empty_filter(self):
        f = get_staff_queue_filter()
        assert f == {}

    def test_status_filter(self):
        f = get_staff_queue_filter(status=["draft", "submitted"])
        assert "draft" in f["status"]

    def test_invalid_status_filtered(self):
        f = get_staff_queue_filter(status=["draft", "bogus_status"])
        assert "bogus_status" not in f["status"]

    def test_assigned_to_filter(self):
        uid = uuid4()
        f = get_staff_queue_filter(assigned_to=uid)
        assert f["assigned_officer_id"] == str(uid)


# ---------------------------------------------------------------------------
# 9. Status helpers
# ---------------------------------------------------------------------------


class TestStatusHelpers:
    def test_active_statuses(self):
        active = get_active_statuses()
        assert "submitted" in active
        assert "draft" not in active
        assert "approved" not in active

    def test_terminal_statuses(self):
        assert is_terminal_status(ApplicationStatus.APPROVED) is True
        assert is_terminal_status(ApplicationStatus.REFUSED) is True
        assert is_terminal_status(ApplicationStatus.WITHDRAWN) is True
        assert is_terminal_status(ApplicationStatus.CANCELLED) is True
        assert is_terminal_status(ApplicationStatus.DRAFT) is False
        assert is_terminal_status(ApplicationStatus.UNDER_REVIEW) is False

    def test_display_names(self):
        assert status_display_name(ApplicationStatus.APPROVED) == "Approved"
        assert status_display_name(ApplicationStatus.DRAFT) == "Draft"
        assert status_display_name(ApplicationStatus.RETURNED) == "Returned for Information"


# ---------------------------------------------------------------------------
# 10. SLA state after workflow changes
# ---------------------------------------------------------------------------


class TestSlaAfterWorkflow:
    def test_submitted_has_active_status(self):
        """After submit, status should be in ACTIVE_STATUSES for SLA."""
        from app.workflow.models import ACTIVE_STATUSES

        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        assert result.new_status in ACTIVE_STATUSES

    def test_approved_not_in_active_statuses(self):
        """After approval, SLA should no longer apply."""
        from app.workflow.models import ACTIVE_STATUSES

        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.UNDER_REVIEW,
            action="approve",
            user_id=uuid4(),
            user_role=SystemRole.MANAGER,
        )
        assert result.new_status not in ACTIVE_STATUSES

    def test_withdrawn_not_in_active_statuses(self):
        from app.workflow.models import ACTIVE_STATUSES

        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.SUBMITTED,
            action="withdraw",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        assert result.new_status not in ACTIVE_STATUSES

    def test_returned_is_in_active_statuses(self):
        """Returned (query) status should still have SLA clock running."""
        from app.workflow.models import ACTIVE_STATUSES

        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.UNDER_REVIEW,
            action="request_info",
            user_id=uuid4(),
            user_role=SystemRole.REVIEWER,
        )
        assert result.new_status in ACTIVE_STATUSES


# ---------------------------------------------------------------------------
# 11. Full lifecycle integration
# ---------------------------------------------------------------------------


class TestFullLifecycle:
    def test_complete_happy_path(self):
        """Test a complete application lifecycle: submit → review → approve."""
        app_id = uuid4()
        user_id = uuid4()

        # Step 1: Submit
        r1 = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=user_id,
            user_role=SystemRole.APPLICANT,
            workflow_def=SAMPLE_WORKFLOW,
        )
        assert r1.success
        assert r1.new_status == ApplicationStatus.SUBMITTED
        assert r1.stage_key == "validation"

        # Step 2: Advance to review
        r2 = execute_transition(
            application_id=app_id,
            current_status=r1.new_status,
            action="advance",
            user_id=uuid4(),
            user_role=SystemRole.REVIEWER,
            current_stage=r1.stage_key,
            workflow_def=SAMPLE_WORKFLOW,
        )
        assert r2.success
        assert r2.new_status == ApplicationStatus.UNDER_REVIEW
        assert r2.stage_key == "review"

        # Step 3: Approve
        r3 = execute_transition(
            application_id=app_id,
            current_status=r2.new_status,
            action="approve",
            user_id=uuid4(),
            user_role=SystemRole.MANAGER,
            current_stage=r2.stage_key,
            workflow_def=SAMPLE_WORKFLOW,
        )
        assert r3.success
        assert r3.new_status == ApplicationStatus.APPROVED

    def test_query_and_respond(self):
        """Test: submit → review → request_info → respond → review → approve."""
        app_id = uuid4()

        # Submit
        r1 = execute_transition(
            application_id=app_id,
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        # Advance
        r2 = execute_transition(
            application_id=app_id,
            current_status=r1.new_status,
            action="advance",
            user_id=uuid4(),
            user_role=SystemRole.REVIEWER,
            current_stage=r1.stage_key,
        )
        # Request info
        r3 = execute_transition(
            application_id=app_id,
            current_status=r2.new_status,
            action="request_info",
            user_id=uuid4(),
            user_role=SystemRole.REVIEWER,
            current_stage=r2.stage_key,
        )
        assert r3.new_status == ApplicationStatus.RETURNED

        # Respond
        r4 = execute_transition(
            application_id=app_id,
            current_status=r3.new_status,
            action="respond",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        assert r4.new_status == ApplicationStatus.UNDER_REVIEW

    def test_withdraw_after_submit(self):
        """Test: submit → withdraw."""
        r1 = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        r2 = execute_transition(
            application_id=uuid4(),
            current_status=r1.new_status,
            action="withdraw",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        assert r2.success
        assert r2.new_status == ApplicationStatus.WITHDRAWN

    def test_refuse_path(self):
        """Test: submit → review → refuse."""
        r1 = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        r2 = execute_transition(
            application_id=uuid4(),
            current_status=r1.new_status,
            action="advance",
            user_id=uuid4(),
            user_role=SystemRole.REVIEWER,
            current_stage=r1.stage_key,
        )
        r3 = execute_transition(
            application_id=uuid4(),
            current_status=r2.new_status,
            action="refuse",
            user_id=uuid4(),
            user_role=SystemRole.ADMIN,
            current_stage=r2.stage_key,
        )
        assert r3.success
        assert r3.new_status == ApplicationStatus.REFUSED


# ---------------------------------------------------------------------------
# 12. Audit trail
# ---------------------------------------------------------------------------


class TestAuditTrail:
    def test_every_transition_creates_audit(self):
        """Every successful transition should produce an audit record."""
        transitions = [
            (ApplicationStatus.DRAFT, "submit", SystemRole.APPLICANT),
            (ApplicationStatus.SUBMITTED, "advance", SystemRole.REVIEWER),
            (ApplicationStatus.UNDER_REVIEW, "approve", SystemRole.MANAGER),
        ]
        for from_status, action, role in transitions:
            result = execute_transition(
                application_id=uuid4(),
                current_status=from_status,
                action=action,
                user_id=uuid4(),
                user_role=role,
            )
            if result.success:
                assert result.audit_record is not None
                assert result.audit_record.action == f"workflow.{action}"

    def test_audit_record_has_previous_and_new_values(self):
        result = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.DRAFT,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        assert result.audit_record.previous_values["status"] == "draft"
        assert result.audit_record.new_values["status"] == "submitted"


# ---------------------------------------------------------------------------
# 13. Duplicate transition protection
# ---------------------------------------------------------------------------


class TestDuplicateTransitionProtection:
    def test_cannot_submit_twice(self):
        """An already-submitted application cannot be submitted again."""
        r1 = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.SUBMITTED,
            action="submit",
            user_id=uuid4(),
            user_role=SystemRole.APPLICANT,
        )
        assert r1.success is False

    def test_cannot_approve_already_approved(self):
        r1 = execute_transition(
            application_id=uuid4(),
            current_status=ApplicationStatus.APPROVED,
            action="approve",
            user_id=uuid4(),
            user_role=SystemRole.MANAGER,
        )
        assert r1.success is False

    def test_cannot_advance_from_terminal(self):
        terminals = [
            ApplicationStatus.APPROVED,
            ApplicationStatus.REFUSED,
            ApplicationStatus.WITHDRAWN,
        ]
        for terminal in terminals:
            r = execute_transition(
                application_id=uuid4(),
                current_status=terminal,
                action="advance",
                user_id=uuid4(),
                user_role=SystemRole.REVIEWER,
            )
            assert r.success is False
