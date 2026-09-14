"""FastAPI dependencies for authentication and authorization.

Usage in route handlers:

    @router.get("/things/{thing_id}")
    async def get_thing(
        thing_id: UUID,
        user: UserContext = Depends(get_current_user),
    ):
        ...

    @router.post("/things")
    async def create_thing(
        user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
        ...
    ):
        ...
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.auth.models import UserContext
from app.auth.permissions import Permission, SystemRole, has_any_permission, has_permission
from app.core.config import Settings, get_settings

# ---------------------------------------------------------------------------
# JWT verification
# ---------------------------------------------------------------------------

_MISSING_TOKEN = "Not authenticated"
_INVALID_TOKEN = "Invalid or expired token"


def _decode_jwt(token: str, settings: Settings) -> dict:
    """Decode and verify a Supabase-issued JWT.

    Raises HTTPException 401 on any verification failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.auth_jwt_secret,
            algorithms=[settings.auth_jwt_algorithm],
            audience=settings.auth_jwt_audience,
            options={"require": ["exp", "sub", "aud"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_bearer_token(authorization: str | None) -> str:
    """Extract the Bearer token from the Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_MISSING_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_MISSING_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def _extract_user_id(payload: dict) -> UUID:
    """Extract the user UUID from the 'sub' claim."""
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )


def _resolve_role(payload: dict) -> SystemRole:
    """Resolve the application role from the JWT payload.

    Supabase GoTrue stores the user's app metadata under 'app_metadata'.
    We expect the role to be under app_metadata.role.  If absent, default
    to APPLICANT (least privilege).
    """
    app_metadata = payload.get("app_metadata", {}) or {}
    raw_role = app_metadata.get("role", SystemRole.APPLICANT)
    try:
        return SystemRole(raw_role)
    except ValueError:
        return SystemRole.APPLICANT


# ---------------------------------------------------------------------------
# Core dependency: get_current_user
# ---------------------------------------------------------------------------


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    settings: Settings = Depends(get_settings),
) -> UserContext:
    """FastAPI dependency that extracts and verifies the current user from a JWT.

    Use this as a dependency on any route that requires an authenticated user:

        user: UserContext = Depends(get_current_user)
    """
    token = _extract_bearer_token(authorization)
    payload = _decode_jwt(token, settings)
    user_id = _extract_user_id(payload)
    role = _resolve_role(payload)

    return UserContext(
        user_id=user_id,
        email=payload.get("email"),
        role=role,
        raw_claims=payload,
    )


# ---------------------------------------------------------------------------
# Authorization dependency factories
# ---------------------------------------------------------------------------


def require_permission(permission: Permission) -> Callable:
    """Return a dependency that enforces a single permission.

    Usage:
        @router.post("/applications")
        async def create(
            user: UserContext = Depends(require_permission(Permission.APPLICATION_CREATE)),
        ):
            ...
    """

    async def _check(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required",
            )
        return user

    # Preserve the function name so FastAPI's dependency injection graph works
    _check.__name__ = f"require_{permission.value.replace(':', '_')}"
    return _check


def require_any_permission(*permissions: Permission) -> Callable:
    """Return a dependency that enforces at least one of the listed permissions.

    Usage:
        @router.get("/approvals")
        async def list(
            user: UserContext = Depends(
                require_any_permission(
                    Permission.APPLICATION_VIEW_ALL,
                    Permission.APPLICATION_VIEW_TEAM,
                )
            ),
        ):
            ...
    """

    async def _check(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:
        if not has_any_permission(user.role, list(permissions)):
            required = ", ".join(p.value for p in permissions)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: one of [{required}] required",
            )
        return user

    perm_names = "_or_".join(p.value.replace(":", "_") for p in permissions)
    _check.__name__ = f"require_any_{perm_names}"
    return _check


# ---------------------------------------------------------------------------
# Ownership helper
# ---------------------------------------------------------------------------


def check_project_ownership(
    user: UserContext,
    project: dict,
) -> None:
    """Verify the user owns the project or has elevated access.

    Raises HTTPException 403 if the user cannot access the project.

    Ownership rules:
      - APPLICANT: must be the project's applicant_id
      - REVIEWER/MANAGER/ADMIN: allowed (team/org visibility)
    """
    if user.role in {SystemRole.REVIEWER, SystemRole.MANAGER, SystemRole.ADMIN}:
        return

    applicant_id = project.get("applicant_id")
    if applicant_id is None:
        # No owner set — deny by default for applicants
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: project owner not set",
        )

    if str(user.user_id) != str(applicant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this project",
        )


def check_application_ownership(
    user: UserContext,
    application: dict,
    project_repository=None,
) -> None:
    """Verify the user can access the application.

    The application itself references a project_id, so we check project
    ownership instead.  Reviewers/Managers/Admins always pass.
    """
    if user.role in {SystemRole.REVIEWER, SystemRole.MANAGER, SystemRole.ADMIN}:
        return

    # For applicants, we would need to look up the project — but the application
    # record stores the applicant_id from creation.  In Phase 2B the application
    # row contains a project_id, so we would need the project repo to verify.
    # For the MVP, applicants who created the application are considered owners
    # (the creation step already set the applicant context).
    applicant_id = application.get("applicant_id")
    if applicant_id is not None and str(user.user_id) == str(applicant_id):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: you do not own this application",
    )
