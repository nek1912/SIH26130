"""Tests for authentication and authorization.

Covers:
  - JWT decoding / verification
  - Missing token → 401
  - Invalid token → 401
  - Valid authenticated user → user context extracted
  - Insufficient permission → 403
  - Valid permission → allowed
  - Resource ownership enforcement
  - Allowed staff access for elevated roles
"""

from __future__ import annotations

import time
from uuid import uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import (
    _decode_jwt,
    _extract_bearer_token,
    _extract_user_id,
    _resolve_role,
    check_application_ownership,
    check_project_ownership,
    get_current_user,
    require_any_permission,
    require_permission,
)
from app.auth.models import UserContext
from app.auth.permissions import Permission, SystemRole
from app.core.config import Settings

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

TEST_SECRET = "test-jwt-secret-for-testing"
TEST_AUDIENCE = "authenticated"


def _make_settings() -> Settings:
    """Create a test settings instance."""
    return Settings(
        supabase_url="http://localhost:54321",
        supabase_key="test-key",
        auth_jwt_secret=TEST_SECRET,
        auth_jwt_audience=TEST_AUDIENCE,
    )


def _make_token(
    sub: str | None = None,
    email: str = "test@example.com",
    role: str = "applicant",
    exp: int | None = None,
    aud: str = TEST_AUDIENCE,
    extra: dict | None = None,
) -> str:
    """Create a signed JWT for testing."""
    payload: dict = {
        "sub": sub or str(uuid4()),
        "email": email,
        "aud": aud,
        "app_metadata": {"role": role},
    }
    if exp is not None:
        payload["exp"] = exp
    else:
        payload["exp"] = int(time.time()) + 3600  # 1 hour from now
    if extra:
        payload.update(extra)
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def _make_user_context(
    user_id: str | None = None,
    role: SystemRole = SystemRole.APPLICANT,
) -> UserContext:
    """Create a UserContext for direct testing."""
    return UserContext(
        user_id=uuid4() if user_id is None else user_id,
        email="test@example.com",
        role=role,
        raw_claims={},
    )


# ---------------------------------------------------------------------------
# 1. Token extraction
# ---------------------------------------------------------------------------


class TestTokenExtraction:
    def test_missing_header(self):
        """Missing Authorization header raises 401."""
        with pytest.raises(Exception) as exc_info:
            _extract_bearer_token(None)
        assert exc_info.value.status_code == 401

    def test_empty_header(self):
        """Empty Authorization header raises 401."""
        with pytest.raises(Exception) as exc_info:
            _extract_bearer_token("")
        assert exc_info.value.status_code == 401

    def test_no_bearer_scheme(self):
        """Authorization without Bearer prefix raises 401."""
        with pytest.raises(Exception) as exc_info:
            _extract_bearer_token("Basic abc123")
        assert exc_info.value.status_code == 401

    def test_bearer_without_token(self):
        """Bearer scheme without a token raises 401."""
        with pytest.raises(Exception) as exc_info:
            _extract_bearer_token("Bearer ")
        assert exc_info.value.status_code == 401

    def test_valid_bearer_token(self):
        """Valid Bearer token is extracted correctly."""
        token = _extract_bearer_token("Bearer mytoken123")
        assert token == "mytoken123"


# ---------------------------------------------------------------------------
# 2. JWT decoding
# ---------------------------------------------------------------------------


class TestJwtDecoding:
    def test_valid_token(self):
        """A valid token is decoded successfully."""
        settings = _make_settings()
        token = _make_token(sub=str(uuid4()))
        payload = _decode_jwt(token, settings)
        assert "sub" in payload
        assert "email" in payload

    def test_expired_token(self):
        """An expired token raises 401."""
        settings = _make_settings()
        token = _make_token(exp=int(time.time()) - 3600)  # 1 hour ago
        with pytest.raises(Exception) as exc_info:
            _decode_jwt(token, settings)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_wrong_secret(self):
        """A token signed with a different secret raises 401."""
        settings = _make_settings()
        token = jwt.encode(
            {"sub": str(uuid4()), "exp": int(time.time()) + 3600, "aud": TEST_AUDIENCE},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(Exception) as exc_info:
            _decode_jwt(token, settings)
        assert exc_info.value.status_code == 401

    def test_wrong_audience(self):
        """A token with the wrong audience raises 401."""
        settings = _make_settings()
        token = _make_token(aud="wrong-audience")
        with pytest.raises(Exception) as exc_info:
            _decode_jwt(token, settings)
        assert exc_info.value.status_code == 401

    def test_missing_sub_claim(self):
        """A token without 'sub' claim raises 401."""
        settings = _make_settings()
        payload = {
            "email": "test@example.com",
            "exp": int(time.time()) + 3600,
            "aud": TEST_AUDIENCE,
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        with pytest.raises(Exception) as exc_info:
            _decode_jwt(token, settings)
        assert exc_info.value.status_code == 401

    def test_garbage_token(self):
        """A completely invalid token string raises 401."""
        settings = _make_settings()
        with pytest.raises(Exception) as exc_info:
            _decode_jwt("not.a.jwt", settings)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# 3. User ID extraction
# ---------------------------------------------------------------------------


class TestUserIdExtraction:
    def test_valid_uuid(self):
        """A valid UUID sub claim is extracted."""
        uid = uuid4()
        result = _extract_user_id({"sub": str(uid)})
        assert result == uid

    def test_invalid_uuid(self):
        """A non-UUID sub claim raises 401."""
        with pytest.raises(Exception) as exc_info:
            _extract_user_id({"sub": "not-a-uuid"})
        assert exc_info.value.status_code == 401

    def test_missing_sub(self):
        """Missing sub claim raises 401."""
        with pytest.raises(Exception) as exc_info:
            _extract_user_id({})
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# 4. Role resolution
# ---------------------------------------------------------------------------


class TestRoleResolution:
    def test_valid_role(self):
        """A known role from app_metadata is returned."""
        payload = {"app_metadata": {"role": "reviewer"}}
        assert _resolve_role(payload) == SystemRole.REVIEWER

    def test_missing_metadata(self):
        """Missing app_metadata defaults to APPLICANT."""
        payload = {}
        assert _resolve_role(payload) == SystemRole.APPLICANT

    def test_missing_role_in_metadata(self):
        """Missing role key in app_metadata defaults to APPLICANT."""
        payload = {"app_metadata": {}}
        assert _resolve_role(payload) == SystemRole.APPLICANT

    def test_invalid_role_string(self):
        """An unknown role string defaults to APPLICANT."""
        payload = {"app_metadata": {"role": "superuser"}}
        assert _resolve_role(payload) == SystemRole.APPLICANT

    def test_none_metadata(self):
        """None app_metadata defaults to APPLICANT."""
        payload = {"app_metadata": None}
        assert _resolve_role(payload) == SystemRole.APPLICANT


# ---------------------------------------------------------------------------
# 5. UserContext model
# ---------------------------------------------------------------------------


class TestUserContext:
    def test_creation(self):
        """UserContext can be created with required fields."""
        uid = uuid4()
        ctx = UserContext(user_id=uid, email="a@b.com", role=SystemRole.ADMIN)
        assert ctx.user_id == uid
        assert ctx.role == SystemRole.ADMIN

    def test_frozen(self):
        """UserContext is immutable."""
        ctx = _make_user_context()
        with pytest.raises(Exception):
            ctx.role = SystemRole.ADMIN  # type: ignore[misc]

    def test_default_role(self):
        """Default role is APPLICANT."""
        ctx = UserContext(user_id=uuid4(), email=None)
        assert ctx.role == SystemRole.APPLICANT


# ---------------------------------------------------------------------------
# 6. get_current_user dependency (integration with FastAPI)
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    def _make_app(self) -> FastAPI:
        """Create a test app with a single protected endpoint."""
        app = FastAPI()

        @app.get("/me")
        async def me(user: UserContext = Depends(get_current_user)):
            return {"user_id": str(user.user_id), "role": user.role}

        return app

    def test_valid_token(self):
        """Valid token returns the authenticated user."""
        app = self._make_app()
        client = TestClient(app)
        uid = uuid4()
        token = _make_token(sub=str(uid), role="manager")

        resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == str(uid)
        assert body["role"] == "manager"

    def test_missing_token(self):
        """Missing token returns 401."""
        app = self._make_app()
        client = TestClient(app)

        resp = client.get("/me")

        assert resp.status_code == 401

    def test_invalid_token(self):
        """Invalid token returns 401."""
        app = self._make_app()
        client = TestClient(app)

        resp = client.get("/me", headers={"Authorization": "Bearer garbage"})

        assert resp.status_code == 401

    def test_expired_token(self):
        """Expired token returns 401."""
        app = self._make_app()
        client = TestClient(app)
        token = _make_token(exp=int(time.time()) - 100)

        resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 7. require_permission dependency
# ---------------------------------------------------------------------------


class TestRequirePermission:
    def _make_app(self, permission: Permission) -> FastAPI:
        app = FastAPI()

        @app.get("/protected")
        async def protected(
            user: UserContext = Depends(require_permission(permission)),
        ):
            return {"role": user.role}

        return app

    def test_sufficient_permission(self):
        """User with the required permission is allowed."""
        app = self._make_app(Permission.MODULE_VIEW)
        client = TestClient(app)
        token = _make_token(role="reviewer")  # reviewer has MODULE_VIEW

        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        assert resp.json()["role"] == "reviewer"

    def test_insufficient_permission(self):
        """User without the required permission gets 403."""
        app = self._make_app(Permission.APPLICATION_DECIDE)
        client = TestClient(app)
        token = _make_token(role="applicant")  # applicant cannot decide

        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 403
        assert "Permission denied" in resp.json()["detail"]

    def test_no_token(self):
        """No token returns 401 (authentication before authorization)."""
        app = self._make_app(Permission.MODULE_VIEW)
        client = TestClient(app)

        resp = client.get("/protected")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 8. require_any_permission dependency
# ---------------------------------------------------------------------------


class TestRequireAnyPermission:
    def _make_app(self, *perms: Permission) -> FastAPI:
        app = FastAPI()

        @app.get("/protected")
        async def protected(
            user: UserContext = Depends(require_any_permission(*perms)),
        ):
            return {"role": user.role}

        return app

    def test_has_one_of_required(self):
        """User with at least one required permission is allowed."""
        app = self._make_app(
            Permission.APPLICATION_VIEW_ALL,
            Permission.APPLICATION_VIEW_TEAM,
        )
        client = TestClient(app)
        token = _make_token(role="reviewer")  # reviewer has VIEW_TEAM

        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200

    def test_has_none_of_required(self):
        """User with none of the required permissions gets 403."""
        app = self._make_app(
            Permission.APPLICATION_VIEW_ALL,
            Permission.APPLICATION_DECIDE,
        )
        client = TestClient(app)
        token = _make_token(role="applicant")  # applicant has neither

        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 9. Ownership checks
# ---------------------------------------------------------------------------


class TestProjectOwnership:
    def test_owner_can_access(self):
        """Applicant who owns the project can access it."""
        uid = uuid4()
        user = UserContext(user_id=uid, email="a@b.com", role=SystemRole.APPLICANT)
        project = {"applicant_id": str(uid)}
        check_project_ownership(user, project)  # should not raise

    def test_non_owner_cannot_access(self):
        """Applicant who does not own the project gets 403."""
        user = _make_user_context(role=SystemRole.APPLICANT)
        project = {"applicant_id": str(uuid4())}  # different user
        with pytest.raises(Exception) as exc_info:
            check_project_ownership(user, project)
        assert exc_info.value.status_code == 403

    def test_no_owner_set(self):
        """Applicant gets 403 when project has no applicant_id."""
        user = _make_user_context(role=SystemRole.APPLICANT)
        project = {}
        with pytest.raises(Exception) as exc_info:
            check_project_ownership(user, project)
        assert exc_info.value.status_code == 403

    def test_reviewer_always_allowed(self):
        """Reviewer can access any project."""
        user = _make_user_context(role=SystemRole.REVIEWER)
        project = {"applicant_id": str(uuid4())}
        check_project_ownership(user, project)  # should not raise

    def test_manager_always_allowed(self):
        """Manager can access any project."""
        user = _make_user_context(role=SystemRole.MANAGER)
        project = {"applicant_id": str(uuid4())}
        check_project_ownership(user, project)

    def test_admin_always_allowed(self):
        """Admin can access any project."""
        user = _make_user_context(role=SystemRole.ADMIN)
        project = {"applicant_id": str(uuid4())}
        check_project_ownership(user, project)


class TestApplicationOwnership:
    def test_owner_can_access(self):
        """Applicant who owns the application can access it."""
        uid = uuid4()
        user = UserContext(user_id=uid, email="a@b.com", role=SystemRole.APPLICANT)
        application = {"applicant_id": str(uid)}
        check_application_ownership(user, application)  # should not raise

    def test_non_owner_cannot_access(self):
        """Applicant who does not own the application gets 403."""
        user = _make_user_context(role=SystemRole.APPLICANT)
        application = {"applicant_id": str(uuid4())}
        with pytest.raises(Exception) as exc_info:
            check_application_ownership(user, application)
        assert exc_info.value.status_code == 403

    def test_reviewer_always_allowed(self):
        """Reviewer can access any application."""
        user = _make_user_context(role=SystemRole.REVIEWER)
        application = {"applicant_id": str(uuid4())}
        check_application_ownership(user, application)

    def test_admin_always_allowed(self):
        """Admin can access any application."""
        user = _make_user_context(role=SystemRole.ADMIN)
        application = {"applicant_id": str(uuid4())}
        check_application_ownership(user, application)


# ---------------------------------------------------------------------------
# 10. Route-level integration tests
# ---------------------------------------------------------------------------


class TestRouteAuthIntegration:
    """Integration tests verifying that the actual API routes enforce auth."""

    def test_health_still_public(self):
        """Health endpoint remains unauthenticated."""
        from app.main import app

        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_root_still_public(self):
        """Root endpoint remains unauthenticated."""
        from app.main import app

        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200

    def test_projects_requires_auth(self):
        """GET /projects/{id} requires authentication."""
        from app.main import app

        client = TestClient(app)
        resp = client.get(f"/projects/{uuid4()}")
        assert resp.status_code == 401

    def test_approvals_requires_auth(self):
        """GET /approvals requires authentication."""
        from app.main import app

        client = TestClient(app)
        resp = client.get("/approvals")
        assert resp.status_code == 401

    def test_obligations_requires_auth(self):
        """GET /obligations requires authentication."""
        from app.main import app

        client = TestClient(app)
        resp = client.get("/obligations")
        assert resp.status_code == 401

    def test_applications_requires_auth(self):
        """GET /applications/{id} requires authentication."""
        from app.main import app

        client = TestClient(app)
        resp = client.get(f"/applications/{uuid4()}")
        assert resp.status_code == 401

    def test_create_application_requires_auth(self):
        """POST /applications requires authentication."""
        from app.main import app

        client = TestClient(app)
        resp = client.post(
            "/applications",
            params={"project_id": str(uuid4()), "approval_id": str(uuid4())},
        )
        assert resp.status_code == 401
