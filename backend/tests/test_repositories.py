"""Tests for repository layer with mocked PostgresDB handle."""

from unittest.mock import MagicMock

import pytest

from app.repositories.applications import ApplicationsRepository
from app.repositories.approvals import ApprovalsRepository
from app.repositories.base import BaseRepository
from app.repositories.obligations import ObligationsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.sources import SourcesRepository


@pytest.fixture
def mock_client():
    """Create a mock PostgresDB handle."""
    return MagicMock()


class TestBaseRepository:
    """Tests for BaseRepository."""

    def test_get_by_id(self, mock_client):
        """Test get_by_id returns record."""
        repo = BaseRepository(mock_client, "test_table")
        mock_client.fetch_one.return_value = {"id": "123", "name": "test"}

        result = repo.get_by_id("123")
        assert result == {"id": "123", "name": "test"}
        mock_client.fetch_one.assert_called_once()

    def test_get_by_id_not_found(self, mock_client):
        """Test get_by_id returns None when not found."""
        repo = BaseRepository(mock_client, "test_table")
        mock_client.fetch_one.return_value = None

        result = repo.get_by_id("123")
        assert result is None

    def test_get_all(self, mock_client):
        """Test get_all returns list of records."""
        repo = BaseRepository(mock_client, "test_table")
        mock_client.fetch_all.return_value = [{"id": "1"}, {"id": "2"}]

        result = repo.get_all()
        assert len(result) == 2

    def test_create(self, mock_client):
        """Test create returns created record."""
        repo = BaseRepository(mock_client, "test_table")
        mock_client.insert_one.return_value = {"id": "123", "name": "test"}

        result = repo.create({"name": "test"})
        assert result == {"id": "123", "name": "test"}

    def test_parameterized_sql_no_interpolation(self, mock_client):
        """User values travel as params, never interpolated into SQL."""
        repo = BaseRepository(mock_client, "test_table")
        mock_client.fetch_one.return_value = None
        repo.get_by_id("x'; DROP TABLE test_table; --")
        _sql, params = mock_client.fetch_one.call_args[0]
        assert "DROP TABLE" not in _sql
        assert params == ("x'; DROP TABLE test_table; --",)


class TestProjectRepository:
    """Tests for ProjectRepository."""

    def test_get_by_applicant(self, mock_client):
        """Test get_by_applicant returns projects."""
        repo = ProjectRepository(mock_client)
        mock_client.fetch_all.return_value = [{"id": "123", "name": "test"}]

        result = repo.get_by_applicant("applicant-123")
        assert len(result) == 1
        assert result[0]["name"] == "test"


class TestProjectFactsRepository:
    """Tests for ProjectFactsRepository."""

    def test_get_by_project(self, mock_client):
        """Test get_by_project returns facts."""
        repo = ProjectFactsRepository(mock_client)
        mock_client.fetch_one.return_value = {
            "id": "123",
            "entity_type": "pvt-ltd",
        }

        result = repo.get_by_project("project-123")
        assert result["entity_type"] == "pvt-ltd"


class TestApprovalsRepository:
    """Tests for ApprovalsRepository."""

    def test_get_active(self, mock_client):
        """Test get_active returns active approvals."""
        repo = ApprovalsRepository(mock_client)
        mock_client.fetch_all.return_value = [
            {"id": "1", "name": "Approval 1", "active": True}
        ]

        result = repo.get_active()
        assert len(result) == 1
        assert result[0]["active"] is True


class TestObligationsRepository:
    """Tests for ObligationsRepository."""

    def test_get_all_active(self, mock_client):
        """Test get_all_active returns all obligations."""
        repo = ObligationsRepository(mock_client)
        mock_client.fetch_all.return_value = [{"id": "1", "canonical_id": "obl-1"}]

        result = repo.get_all_active()
        assert len(result) == 1

    def test_get_by_canonical_id(self, mock_client):
        """Test get_by_canonical_id returns obligation."""
        repo = ObligationsRepository(mock_client)
        mock_client.fetch_one.return_value = {"id": "1", "canonical_id": "obl-1"}

        result = repo.get_by_canonical_id("obl-1")
        assert result["canonical_id"] == "obl-1"


class TestSourcesRepository:
    """Tests for SourcesRepository."""

    def test_get_by_jurisdiction(self, mock_client):
        """Test get_by_jurisdiction returns sources."""
        repo = SourcesRepository(mock_client)
        mock_client.fetch_all.return_value = [{"id": "1", "jurisdiction": "IN-GJ"}]

        result = repo.get_by_jurisdiction("IN-GJ")
        assert len(result) == 1
        assert result[0]["jurisdiction"] == "IN-GJ"


class TestApplicationsRepository:
    """Tests for ApplicationsRepository."""

    def test_get_by_project(self, mock_client):
        """Test get_by_project returns applications."""
        repo = ApplicationsRepository(mock_client)
        mock_client.fetch_all.return_value = [{"id": "1", "project_id": "project-123"}]

        result = repo.get_by_project("project-123")
        assert len(result) == 1

    def test_create_with_reference(self, mock_client):
        """Test create_with_reference generates reference number."""
        repo = ApplicationsRepository(mock_client)
        mock_client.insert_one.return_value = {
            "id": "1",
            "reference_number": "APP-12345678",
        }

        result = repo.create_with_reference({"project_id": "123"})
        assert "reference_number" in result
