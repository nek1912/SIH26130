"""Tests for incentive API endpoints.

Covers:
- GET /incentives (list schemes)
- GET /incentives/{scheme_id} (get scheme)
- POST /incentives/assess (assess project)
- Auth requirements
- 404 for unknown scheme
- Category filtering
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.models import SystemRole, UserContext
from app.main import app


@pytest.fixture(autouse=True)
def _clear_overrides():
    """Reset dependency overrides between tests."""
    yield
    app.dependency_overrides.clear()


def _make_user() -> UserContext:
    return UserContext(
        user_id=uuid4(),
        email="test@test.com",
        role=SystemRole.APPLICANT,
        raw_claims={},
    )


def _make_test_client() -> TestClient:
    """Create test client with mocked auth."""
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    return TestClient(app)


class TestListIncentiveSchemes:
    """Test GET /incentives endpoint."""

    def test_list_schemes_returns_all(self):
        client = _make_test_client()
        response = client.get("/incentives")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6

    def test_list_schemes_filter_by_category(self):
        client = _make_test_client()
        response = client.get("/incentives?category=capital_subsidy")
        assert response.status_code == 200
        data = response.json()
        assert all(s["category"] == "capital_subsidy" for s in data)
        assert len(data) >= 2

    def test_list_schemes_no_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/incentives")
        assert response.status_code in (401, 403)


class TestGetIncentiveScheme:
    """Test GET /incentives/{scheme_id} endpoint."""

    def test_get_existing_scheme(self):
        client = _make_test_client()
        response = client.get("/incentives/INC-ELEC-DUTY")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "INC-ELEC-DUTY"
        assert data["name"] == "Electricity Duty Exemption"
        assert data["category"] == "tax_concession"

    def test_get_nonexistent_scheme(self):
        client = _make_test_client()
        response = client.get("/incentives/INC-DOES-NOT-EXIST")
        assert response.status_code == 404

    def test_get_scheme_no_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.get("/incentives/INC-ELEC-DUTY")
        assert response.status_code in (401, 403)


class TestAssessIncentives:
    """Test POST /incentives/assess endpoint."""

    def test_assess_with_matching_facts(self):
        client = _make_test_client()
        response = client.post(
            "/incentives/assess",
            json={
                "project_facts": {
                    "entity_type": "pvt-ltd",
                    "new_project": True,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "assessments" in data
        assert "relevant_count" in data
        assert data["relevant_count"] >= 1
        relevant_ids = {
            a["scheme_id"]
            for a in data["assessments"]
            if a["relevance"] == "potentially_relevant"
        }
        assert "INC-MSME-CAP" in relevant_ids

    def test_assess_with_empty_facts(self):
        client = _make_test_client()
        response = client.post(
            "/incentives/assess",
            json={"project_facts": {}},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["assessments"]) == 6

    def test_assess_with_scheme_filter(self):
        client = _make_test_client()
        response = client.post(
            "/incentives/assess",
            json={
                "project_facts": {"entity_type": "pvt-ltd"},
                "scheme_ids": ["INC-MSME-CAP"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["assessments"]) == 1
        assert data["assessments"][0]["scheme_id"] == "INC-MSME-CAP"

    def test_assessment_no_approval_fields(self):
        """Assessment result must not contain approval-related fields."""
        client = _make_test_client()
        response = client.post(
            "/incentives/assess",
            json={"project_facts": {"entity_type": "pvt-ltd"}},
        )
        assert response.status_code == 200
        data = response.json()
        for assessment in data["assessments"]:
            assert "approval_id" not in assessment

    def test_assess_no_auth(self):
        app.dependency_overrides.clear()
        client = TestClient(app)
        response = client.post(
            "/incentives/assess",
            json={"project_facts": {}},
        )
        assert response.status_code in (401, 403)

    def test_assessment_source_refs_preserved(self):
        """Source references are preserved in assessment results."""
        client = _make_test_client()
        response = client.post(
            "/incentives/assess",
            json={"project_facts": {"entity_type": "pvt-ltd"}},
        )
        assert response.status_code == 200
        data = response.json()
        for assessment in data["assessments"]:
            assert "source_refs" in assessment
            assert len(assessment["source_refs"]) >= 1

    def test_assessment_explanation_present(self):
        """Assessment includes a human-readable explanation."""
        client = _make_test_client()
        response = client.post(
            "/incentives/assess",
            json={"project_facts": {"entity_type": "pvt-ltd", "new_project": True}},
        )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert len(data["explanation"]) > 0
        assert "competent authority" in data["explanation"]
