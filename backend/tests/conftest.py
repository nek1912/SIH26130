"""Shared test configuration — sets env vars for auth settings before any imports."""

from __future__ import annotations

import os

# These env vars must be set before Settings() is first instantiated.
# pydantic-settings reads them at __init__ time.
os.environ.setdefault("AUTH_JWT_SECRET", "test-jwt-secret-for-testing")
os.environ.setdefault("AUTH_JWT_AUDIENCE", "authenticated")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_KEY", "test-key")
