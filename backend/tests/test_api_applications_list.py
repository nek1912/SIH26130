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
        """Create a repo with a mock client returning the given data."""
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_result = MagicMock()
        mock_result.data = mock_data
        mock_result.count = mock_count
        mock_query.execute.return_value = mock_result
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.in_.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_client.table.return_value.select.return_value = mock_query
        return ApplicationsRepository(mock_client), mock_query

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
        repo, mock_query = self._make_repo(
            [{"id": "1", "status": "submitted"}],
            1,
        )
        items, total = repo.list_all_with_filters(status=["submitted"])
        assert len(items) == 1
        assert items[0]["status"] == "submitted"
        mock_query.in_.assert_called_with("status", ["submitted"])

    def test_assigned_to_filter(self):
        """Filters by assigned officer."""
        officer_id = str(uuid4())
        repo, mock_query = self._make_repo(
            [{"id": "1", "assigned_officer_id": officer_id}],
            1,
        )
        items, total = repo.list_all_with_filters(assigned_to=officer_id)
        assert len(items) == 1
        mock_query.eq.assert_any_call("assigned_officer_id", officer_id)

    def test_applicant_id_filter(self):
        """Filters by applicant."""
        applicant_id = str(uuid4())
        repo, mock_query = self._make_repo(
            [{"id": "1", "applicant_id": applicant_id}],
            1,
        )
        items, total = repo.list_all_with_filters(applicant_id=applicant_id)
        assert len(items) == 1
        mock_query.eq.assert_any_call("applicant_id", applicant_id)

    def test_pagination(self):
        """Applies correct pagination."""
        repo, mock_query = self._make_repo(
            [{"id": "3"}, {"id": "4"}],
            10,
        )
        items, total = repo.list_all_with_filters(page=2, page_size=2)
        assert len(items) == 2
        assert total == 10
        mock_query.range.assert_called_with(2, 3)

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
        repo, mock_query = self._make_repo(
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
        mock_query.in_.assert_called_with("status", ["under_review"])
        assert mock_query.eq.call_count == 2


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
