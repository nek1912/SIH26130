"""Tests for application list endpoint."""

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.applications import ApplicationsRepository

# --- Repository unit tests ---


class TestListAllWithFilters:
    """Tests for ApplicationsRepository.list_all_with_filters."""

    def _make_repo(self, mock_data, mock_count):
        """Create a repo with a mocked PostgresDB handle."""
        from app.db.postgres import PostgresDB

        mock_client = MagicMock(spec=PostgresDB)
        mock_client.fetch_all.return_value = mock_data
        mock_client.fetch_one.return_value = {"n": mock_count}
        return ApplicationsRepository(mock_client), mock_client

    def test_no_filters(self):
        """Returns all applications when no filters applied."""
        repo, _ = self._make_repo(
            [{"id": "1", "status": "draft"}, {"id": "2", "status": "submitted"}],
            2,
        )
        items, total = repo.list_all_with_filters()
        assert len(items) == 2
        assert total == 2

    def test_status_filter(self):
        """Filters by status."""
        repo, mock_client = self._make_repo(
            [{"id": "1", "status": "submitted"}],
            1,
        )
        items, total = repo.list_all_with_filters(status=["submitted"])
        assert len(items) == 1
        assert items[0]["status"] == "submitted"
        where_sql = mock_client.fetch_all.call_args[0][0]
        assert "status IN (%s)" in where_sql

    def test_assigned_to_filter(self):
        """Filters by assigned officer."""
        officer_id = str(uuid4())
        repo, mock_client = self._make_repo(
            [{"id": "1", "assigned_officer_id": officer_id}],
            1,
        )
        items, total = repo.list_all_with_filters(assigned_to=officer_id)
        assert len(items) == 1
        where_sql = mock_client.fetch_all.call_args[0][0]
        assert "assigned_officer_id = %s" in where_sql

    def test_applicant_id_filter(self):
        """Filters by applicant."""
        applicant_id = str(uuid4())
        repo, mock_client = self._make_repo(
            [{"id": "1", "applicant_id": applicant_id}],
            1,
        )
        items, total = repo.list_all_with_filters(applicant_id=applicant_id)
        assert len(items) == 1
        where_sql = mock_client.fetch_all.call_args[0][0]
        assert "applicant_id = %s" in where_sql

    def test_pagination(self):
        """Applies correct pagination."""
        repo, mock_client = self._make_repo(
            [{"id": "3"}, {"id": "4"}],
            10,
        )
        items, total = repo.list_all_with_filters(page=2, page_size=2)
        assert len(items) == 2
        assert total == 10
        _, params = mock_client.fetch_all.call_args[0]
        assert params[-2:] == (2, 2)

    def test_empty_result(self):
        """Returns empty list when no matches."""
        repo, _ = self._make_repo([], 0)
        items, total = repo.list_all_with_filters(status=["nonexistent"])
        assert items == []
        assert total == 0

    def test_combined_filters(self):
        """Applies multiple filters together."""
        officer_id = str(uuid4())
        applicant_id = str(uuid4())
        repo, mock_client = self._make_repo(
            [{"id": "1"}],
            1,
        )
        items, total = repo.list_all_with_filters(
            status=["under_review"],
            assigned_to=officer_id,
            applicant_id=applicant_id,
            page=1,
            page_size=10,
        )
        assert len(items) == 1
        where_sql = mock_client.fetch_all.call_args[0][0]
        assert "status IN (%s)" in where_sql
        assert "assigned_officer_id = %s" in where_sql
        assert "applicant_id = %s" in where_sql


# --- API endpoint tests (auth required) ---


class TestListApplicationsEndpoint:
    """Tests for GET /applications endpoint behavior."""

    def test_requires_auth(self):
        """Endpoint requires authentication."""
        client = TestClient(app)
        response = client.get("/applications")
        assert response.status_code == 401

    def test_query_params_accepted(self):
        """Query params are accepted (auth blocks further processing)."""
        client = TestClient(app)
        response = client.get("/applications", params={
            "status": "draft",
            "page": 1,
            "page_size": 10,
        })
        assert response.status_code == 401

    def test_endpoint_exists(self):
        """The endpoint is registered and reachable."""
        client = TestClient(app)
        response = client.get("/applications")
        # Without auth: 401. With valid auth: would proceed to validation.
        assert response.status_code in (401, 422)
