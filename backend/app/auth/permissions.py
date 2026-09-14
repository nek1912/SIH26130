"""RBAC / permissions helper.

Ported from Digital-Permit-Platform/src/lib/permissions.ts.

Static role-to-permission mapping. 4 roles, 18 permissions.
No session enforcement (that will use Supabase Auth in Phase 2).

Source: Digital-Permit-Platform/src/lib/permissions.ts (101 lines)
"""
from __future__ import annotations

from enum import StrEnum


class SystemRole(StrEnum):
    APPLICANT = "applicant"
    REVIEWER = "reviewer"
    MANAGER = "manager"
    ADMIN = "admin"


class Permission(StrEnum):
    APPLICATION_CREATE = "application:create"
    APPLICATION_VIEW_OWN = "application:view_own"
    APPLICATION_VIEW_TEAM = "application:view_team"
    APPLICATION_VIEW_ALL = "application:view_all"
    APPLICATION_ASSIGN = "application:assign"
    APPLICATION_REVIEW = "application:review"
    APPLICATION_DECIDE = "application:decide"
    APPLICATION_DELETE = "application:delete"
    MODULE_VIEW = "module:view"
    MODULE_EDIT = "module:edit"
    MODULE_CREATE = "module:create"
    MODULE_TOGGLE = "module:toggle"
    USER_VIEW = "user:view"
    USER_MANAGE = "user:manage"
    TEAM_MANAGE = "team:manage"
    AUDIT_VIEW = "audit:view"
    REPORT_VIEW = "report:view"
    ADMIN_ACCESS = "admin:access"


# From Digital-Permit-Platform/src/lib/permissions.ts lines 28-67
ROLE_PERMISSIONS: dict[SystemRole, list[Permission]] = {
    SystemRole.APPLICANT: [
        Permission.APPLICATION_CREATE,
        Permission.APPLICATION_VIEW_OWN,
    ],
    SystemRole.REVIEWER: [
        Permission.APPLICATION_VIEW_TEAM,
        Permission.APPLICATION_REVIEW,
        Permission.MODULE_VIEW,
        Permission.REPORT_VIEW,
    ],
    SystemRole.MANAGER: [
        Permission.APPLICATION_VIEW_ALL,
        Permission.APPLICATION_ASSIGN,
        Permission.APPLICATION_REVIEW,
        Permission.APPLICATION_DECIDE,
        Permission.MODULE_VIEW,
        Permission.MODULE_EDIT,
        Permission.REPORT_VIEW,
        Permission.AUDIT_VIEW,
        Permission.TEAM_MANAGE,
    ],
    SystemRole.ADMIN: [
        Permission.APPLICATION_VIEW_ALL,
        Permission.APPLICATION_ASSIGN,
        Permission.APPLICATION_REVIEW,
        Permission.APPLICATION_DECIDE,
        Permission.APPLICATION_DELETE,
        Permission.MODULE_VIEW,
        Permission.MODULE_EDIT,
        Permission.MODULE_CREATE,
        Permission.MODULE_TOGGLE,
        Permission.USER_VIEW,
        Permission.USER_MANAGE,
        Permission.TEAM_MANAGE,
        Permission.AUDIT_VIEW,
        Permission.REPORT_VIEW,
        Permission.ADMIN_ACCESS,
    ],
}


def has_permission(role: SystemRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, [])


def has_any_permission(role: SystemRole, permissions: list[Permission]) -> bool:
    """Check if a role has any of the listed permissions."""
    return any(has_permission(role, p) for p in permissions)
