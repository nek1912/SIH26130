"""Tests for RBAC permissions."""
from __future__ import annotations

from app.auth.permissions import (
    Permission,
    SystemRole,
    has_any_permission,
    has_permission,
)


class TestHasPermission:
    def test_applicant_can_create(self):
        assert has_permission(SystemRole.APPLICANT, Permission.APPLICATION_CREATE) is True

    def test_applicant_cannot_review(self):
        assert has_permission(SystemRole.APPLICANT, Permission.APPLICATION_REVIEW) is False

    def test_reviewer_can_review(self):
        assert has_permission(SystemRole.REVIEWER, Permission.APPLICATION_REVIEW) is True

    def test_reviewer_cannot_decide(self):
        assert has_permission(SystemRole.REVIEWER, Permission.APPLICATION_DECIDE) is False

    def test_manager_can_decide(self):
        assert has_permission(SystemRole.MANAGER, Permission.APPLICATION_DECIDE) is True

    def test_manager_cannot_delete(self):
        assert has_permission(SystemRole.MANAGER, Permission.APPLICATION_DELETE) is False

    def test_admin_can_delete(self):
        assert has_permission(SystemRole.ADMIN, Permission.APPLICATION_DELETE) is True

    def test_admin_can_manage_users(self):
        assert has_permission(SystemRole.ADMIN, Permission.USER_MANAGE) is True


class TestHasAnyPermission:
    def test_applicant_has_any_create(self):
        assert has_any_permission(
            SystemRole.APPLICANT,
            [Permission.APPLICATION_CREATE, Permission.APPLICATION_REVIEW],
        ) is True

    def test_applicant_has_none_review_decide(self):
        assert has_any_permission(
            SystemRole.APPLICANT,
            [Permission.APPLICATION_REVIEW, Permission.APPLICATION_DECIDE],
        ) is False

    def test_empty_permissions(self):
        assert has_any_permission(SystemRole.ADMIN, []) is False


class TestRoleCompleteness:
    """Verify every role has at least one permission."""

    def test_all_roles_have_permissions(self):
        for role in SystemRole:
            assert len([p for p in Permission if has_permission(role, p)]) > 0
