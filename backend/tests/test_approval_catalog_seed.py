"""Canonical approval-catalog seeding (A01-A18) — Phase 1.

Proves the fresh-database path: the canonical catalog seeds exactly once
into `approvals` (code = stable identity, UUID = persistence id), re-seeds
are idempotent, and a same-code row with different name/authority fails
loudly (409) instead of being re-identified. Also locks the
rule/dependency/hint integrity against the single catalog source.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import approvals as approvals_api
from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.repositories.approvals import ApprovalsRepository
from app.seed.approval_catalog import load_approval_catalog
from app.seed.approvals import load_approval_authorities, load_approval_rules
from app.seed.dependencies import load_approval_dependencies
from app.seed.evidence_gaps import EVIDENCE_TO_APPROVALS

_EXPECTED_CODES = [f"A{i:02d}" for i in range(1, 19)]


def _make_user() -> UserContext:
    return UserContext(
        user_id="00000000-0000-0000-0000-000000000001",
        email="test@test.com",
        role=SystemRole.ADMIN,
        raw_claims={},
    )


def _build_client(repo) -> TestClient:
    app = FastAPI()
    app.include_router(approvals_api.router)

    def override_get_user():
        return _make_user()

    app.dependency_overrides[get_current_user] = override_get_user

    from app.api.deps import get_approvals_repository

    app.dependency_overrides[get_approvals_repository] = lambda: repo
    return TestClient(app)


def _make_repo(rows: list[dict] | None = None) -> MagicMock:
    """Dict-backed fake: get_by_code/create behave like the real table."""
    store: dict[str, dict] = {r["code"]: dict(r) for r in (rows or [])}
    repo = MagicMock(spec=ApprovalsRepository)

    def fake_get_by_code(code: str):
        row = store.get(code)
        return dict(row) if row else None

    def fake_create(data: dict):
        row = dict(data)
        row.setdefault("id", f"00000000-0000-0000-0000-00000000{len(store) + 100:04d}")
        store[row["code"]] = row
        return dict(row)

    repo.get_by_code.side_effect = fake_get_by_code
    repo.create.side_effect = fake_create
    return repo


class TestCatalogIntegrity:
    def test_catalog_has_a01_through_a18_exactly_once(self):
        catalog = load_approval_catalog()
        assert [r["code"] for r in catalog] == _EXPECTED_CODES

    def test_catalog_records_carry_seed_authorities(self):
        authorities = load_approval_authorities()
        for record in load_approval_catalog():
            assert record["authority"] == authorities[record["code"]]
            assert record["active"] is True

    def test_rules_dependencies_and_hints_reference_catalog_codes_only(self):
        codes = {r["code"] for r in load_approval_catalog()}
        for rule in load_approval_rules():
            assert rule.approval_id in codes
        for dep in load_approval_dependencies():
            assert dep.approval_id in codes
            assert dep.prerequisite_approval_id in codes
        for evidence_id, approval_codes in EVIDENCE_TO_APPROVALS.items():
            for code in approval_codes:
                assert code in codes, evidence_id


class TestApprovalSeedEndpoint:
    def test_seed_creates_all_18_on_empty_database(self):
        client = _build_client(_make_repo([]))
        response = client.post("/approvals/seed")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["approvals_seeded"] == 18
        assert data["approvals_skipped"] == 0
        assert data["total_catalog"] == 18

    def test_seed_is_idempotent(self):
        client = _build_client(_make_repo(load_approval_catalog()))
        response = client.post("/approvals/seed")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["approvals_seeded"] == 0
        assert data["approvals_skipped"] == 18

    def test_seed_seeds_only_missing_codes(self):
        existing = load_approval_catalog()[:5]
        client = _build_client(_make_repo(existing))
        response = client.post("/approvals/seed")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["approvals_seeded"] == 13
        assert data["approvals_skipped"] == 5

    def test_seed_fails_loudly_on_mismatched_same_code_row(self):
        """A same-code row with a different name/authority is never
        re-identified: 409, and nothing is written for that code."""
        catalog = load_approval_catalog()
        impostor = dict(catalog[3])
        impostor["name"] = "Something Else Entirely"
        repo = _make_repo([impostor])
        client = _build_client(repo)
        response = client.post("/approvals/seed")
        assert response.status_code == 409, response.text
        created_codes = [
            call.args[0]["code"] for call in repo.create.call_args_list
        ]
        assert "A04" not in created_codes

    def test_seed_requires_auth(self):
        app = FastAPI()
        app.include_router(approvals_api.router)
        client = TestClient(app)
        response = client.post("/approvals/seed")
        assert response.status_code in (401, 403)
