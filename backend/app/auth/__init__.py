"""Auth package — authentication and authorization for the API."""
from app.auth.dependencies import (
    check_application_ownership,
    check_project_ownership,
    get_current_user,
    require_any_permission,
    require_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission, SystemRole, has_any_permission, has_permission

__all__ = [
    "UserContext",
    "get_current_user",
    "require_permission",
    "require_any_permission",
    "check_project_ownership",
    "check_application_ownership",
    "Permission",
    "SystemRole",
    "has_permission",
    "has_any_permission",
]
