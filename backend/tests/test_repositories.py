"""Tests for repository layer with mocked Supabase client."""

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
    """Create a mock Supabase client."""
    client = MagicMock()
    client.table.return_value = MagicMock()
    return client


class TestBaseRepository:
    """Tests for BaseRepository."""

    def test_get_by_id(self, mock_client):
        """Test get_by_id returns record."""
        repo = BaseRepository(mock_client, "test_table")
        mock_result = MagicMock()
        mock_result.data = [{"id": "123", "name": "test"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_id("123")
        assert result == {"id": "123", "name": "test"}

    def test_get_by_id_not_found(self, mock_client):
        """Test get_by_id returns None when not found."""
        repo = BaseRepository(mock_client, "test_table")
        mock_result = MagicMock()
        mock_result.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_id("123")
        assert result is None

    def test_get_all(self, mock_client):
        """Test get_all returns list of records."""
        repo = BaseRepository(mock_client, "test_table")
        mock_result = MagicMock()
        mock_result.data = [{"id": "1"}, {"id": "2"}]
        exec_mock = mock_client.table.return_value.select.return_value.range.return_value.execute
        exec_mock.return_value = mock_result

        result = repo.get_all()
        assert len(result) == 2

    def test_create(self, mock_client):
        """Test create returns created record."""
        repo = BaseRepository(mock_client, "test_table")
        mock_result = MagicMock()
        mock_result.data = [{"id": "123", "name": "test"}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        result = repo.create({"name": "test"})
        assert result == {"id": "123", "name": "test"}


class TestProjectRepository:
    """Tests for ProjectRepository."""

    def test_get_by_applicant(self, mock_client):
        """Test get_by_applicant returns projects."""
        repo = ProjectRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "123", "name": "test"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_applicant("applicant-123")
        assert len(result) == 1
        assert result[0]["name"] == "test"


class TestProjectFactsRepository:
    """Tests for ProjectFactsRepository."""

    def test_get_by_project(self, mock_client):
        """Test get_by_project returns facts."""
        repo = ProjectFactsRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "123", "entity_type": "pvt-ltd"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_project("project-123")
        assert result["entity_type"] == "pvt-ltd"


class TestApprovalsRepository:
    """Tests for ApprovalsRepository."""

    def test_get_active(self, mock_client):
        """Test get_active returns active approvals."""
        repo = ApprovalsRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "1", "name": "Approval 1", "active": True}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_active()
        assert len(result) == 1
        assert result[0]["active"] is True


class TestObligationsRepository:
    """Tests for ObligationsRepository."""

    def test_get_all_active(self, mock_client):
        """Test get_all_active returns all obligations."""
        repo = ObligationsRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "1", "canonical_id": "obl-1"}]
        mock_client.table.return_value.select.return_value.execute.return_value = mock_result

        result = repo.get_all_active()
        assert len(result) == 1

    def test_get_by_canonical_id(self, mock_client):
        """Test get_by_canonical_id returns obligation."""
        repo = ObligationsRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "1", "canonical_id": "obl-1"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_canonical_id("obl-1")
        assert result["canonical_id"] == "obl-1"


class TestSourcesRepository:
    """Tests for SourcesRepository."""

    def test_get_by_jurisdiction(self, mock_client):
        """Test get_by_jurisdiction returns sources."""
        repo = SourcesRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "1", "jurisdiction": "IN-GJ"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_jurisdiction("IN-GJ")
        assert len(result) == 1
        assert result[0]["jurisdiction"] == "IN-GJ"


class TestApplicationsRepository:
    """Tests for ApplicationsRepository."""

    def test_get_by_project(self, mock_client):
        """Test get_by_project returns applications."""
        repo = ApplicationsRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "1", "project_id": "project-123"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_result
        )

        result = repo.get_by_project("project-123")
        assert len(result) == 1

    def test_create_with_reference(self, mock_client):
        """Test create_with_reference generates reference number."""
        repo = ApplicationsRepository(mock_client)
        mock_result = MagicMock()
        mock_result.data = [{"id": "1", "reference_number": "APP-12345678"}]
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        result = repo.create_with_reference({"project_id": "123"})
        assert "reference_number" in result