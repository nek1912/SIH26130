"""FastAPI dependencies for dependency injection."""

from functools import lru_cache

from fastapi import Depends
from supabase import Client

from app.db.client import get_supabase
from app.repositories.applications import ApplicationsRepository
from app.repositories.approvals import ApprovalsRepository
from app.repositories.obligations import ObligationsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.sources import SourcesRepository


@lru_cache
def get_db_client() -> Client:
    """Get Supabase client dependency."""
    return get_supabase()


def get_project_repository(
    client: Client = Depends(get_db_client),
) -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository(client)


def get_project_facts_repository(
    client: Client = Depends(get_db_client),
) -> ProjectFactsRepository:
    """Get project facts repository dependency."""
    return ProjectFactsRepository(client)


def get_approvals_repository(
    client: Client = Depends(get_db_client),
) -> ApprovalsRepository:
    """Get approvals repository dependency."""
    return ApprovalsRepository(client)


def get_obligations_repository(
    client: Client = Depends(get_db_client),
) -> ObligationsRepository:
    """Get obligations repository dependency."""
    return ObligationsRepository(client)


def get_sources_repository(
    client: Client = Depends(get_db_client),
) -> SourcesRepository:
    """Get sources repository dependency."""
    return SourcesRepository(client)


def get_applications_repository(
    client: Client = Depends(get_db_client),
) -> ApplicationsRepository:
    """Get applications repository dependency."""
    return ApplicationsRepository(client)