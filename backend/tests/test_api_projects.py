"""Project endpoints — integration tests against local PostgreSQL.

These replace the former Supabase-gated placeholders. They run against
the gaia_dev database (DATABASE_URL) and clean up every row they
create. Skipped only when no local PostgreSQL is reachable.
"""
from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext


def _db_available() -> bool:
    try:
        from app.db.postgres import create_pool

        pool = create_pool(
            os.environ.get(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/gaia_dev",
            ),
            min_size=1,
            max_size=1,
            open=True,
        )
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        pool.close()
        return True
    except Exception:
        return False


needs_db = pytest.mark.skipif(
    not _db_available(), reason="local PostgreSQL gaia_dev unreachable"
)

USER_ID = "00000000-0000-0000-0000-000000000001"


def _user():
    return UserContext(
        user_id=USER_ID, email="t@t.com", role=SystemRole.APPLICANT, raw_claims={}
    )


def _ensure_user():
    from app.db.postgres import PostgresDB, create_pool

    pool = create_pool(
        os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/gaia_dev",
        )
    )
    try:
        PostgresDB(pool).execute(
            "INSERT INTO auth.users (id) VALUES (%s) "
            "ON CONFLICT (id) DO NOTHING",
            (USER_ID,),
        )
    finally:
        pool.close()


def _client():
    from app.main import app

    client = TestClient(app)
    client.app.dependency_overrides[get_current_user] = _user
    return client


@pytest.fixture(autouse=True)
def _clean_overrides():
    from app.main import app

    yield
    app.dependency_overrides.clear()


def _cleanup_project(project_id: str):
    from app.db.postgres import PostgresDB, create_pool

    db = PostgresDB(create_pool(
        os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/gaia_dev",
        )
    ))
    db.execute("DELETE FROM applications WHERE project_id = %s", (project_id,))
    db.execute("DELETE FROM project_facts WHERE project_id = %s", (project_id,))
    db.execute("DELETE FROM projects WHERE id = %s", (project_id,))


@needs_db
def test_create_project():
    """POST /projects persists a project in local PostgreSQL."""
    _ensure_user()
    client = _client()
    name = f"itest-{uuid.uuid4().hex[:8]}"
    resp = client.post("/projects", params={"name": name})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    try:
        assert body["name"] == name
        assert body["jurisdiction"] == "IN-GJ"
        assert body["pack_version"] == "gj-legacy-unversioned"
    finally:
        _cleanup_project(body["id"])


@needs_db
def test_get_project():
    """GET /projects/{id} reads the persisted project."""
    _ensure_user()
    client = _client()
    name = f"itest-{uuid.uuid4().hex[:8]}"
    created = client.post("/projects", params={"name": name}).json()
    try:
        resp = client.get(f"/projects/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]
    finally:
        _cleanup_project(created["id"])


@needs_db
def test_get_project_not_found():
    """GET unknown project is 404 (no DB error)."""
    client = _client()
    resp = client.get(f"/projects/{uuid.uuid4()}")
    assert resp.status_code == 404


@needs_db
def test_get_project_facts():
    """Facts round-trip through project_facts storage."""
    _ensure_user()
    client = _client()
    name = f"itest-{uuid.uuid4().hex[:8]}"
    created = client.post("/projects", params={"name": name}).json()
    try:
        put = client.post(
            f"/projects/{created['id']}/facts",
            params={
                "entity_type": "pvt-ltd",
                "sector": "chemical",
                "headcount": 60,
                "annual_turnover_inr": 0,
            },
        )
        assert put.status_code == 200, put.text
        got = client.get(f"/projects/{created['id']}/facts")
        assert got.status_code == 200
        assert got.json()["headcount"] == 60
    finally:
        _cleanup_project(created["id"])
