"""Auth models — extracted identity and context."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.auth.permissions import SystemRole


class UserContext(BaseModel):
    """Authenticated user identity extracted from a verified JWT.

    Fields map to the claims Supabase GoTrue places in the token:
      - sub   → user_id
      - email → email
      - role  → app_role (the column we store in the profiles table)
    """

    user_id: UUID = Field(..., description="Supabase Auth user UUID (sub claim)")
    email: str | None = Field(None, description="User email (email claim)")
    role: SystemRole = Field(
        SystemRole.APPLICANT,
        description="Application role from the user's profile row",
    )
    raw_claims: dict = Field(default_factory=dict, description="Full decoded JWT payload")

    model_config = {"frozen": True}
