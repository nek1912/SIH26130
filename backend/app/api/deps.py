"""FastAPI dependencies for dependency injection (local PostgreSQL)."""

from functools import lru_cache

from fastapi import Depends

from app.db.client import get_db
from app.db.postgres import PostgresDB
from app.repositories.applications import ApplicationsRepository
from app.repositories.approvals import ApprovalsRepository
from app.repositories.consistency import ConsistencyRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.handoffs import HandoffsRepository
from app.repositories.obligations import ObligationsRepository
from app.repositories.project_facts import ProjectFactsRepository
from app.repositories.projects import ProjectRepository
from app.repositories.sources import SourcesRepository
from app.repositories.workflow_events import WorkflowEventsRepository
from app.seed import pack as pack_module


@lru_cache
def get_db_client() -> PostgresDB:
    """Get database client dependency (local PostgreSQL pool handle)."""
    return get_db()


def get_active_jurisdiction() -> str:
    """Resolve the regulatory jurisdiction for a request.

    Production behavior: always the pack module's DEFAULT_JURISDICTION
    (IN-GJ). The module-attribute lookup keeps the single cutover
    point authoritative. No client-controlled selector exists.
    """
    return pack_module.DEFAULT_JURISDICTION


def get_project_repository(
    client: PostgresDB = Depends(get_db_client),
) -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository(client)


def get_project_facts_repository(
    client: PostgresDB = Depends(get_db_client),
) -> ProjectFactsRepository:
    """Get project facts repository dependency."""
    return ProjectFactsRepository(client)


def get_approvals_repository(
    client: PostgresDB = Depends(get_db_client),
) -> ApprovalsRepository:
    """Get approvals repository dependency."""
    return ApprovalsRepository(client)


def get_obligations_repository(
    client: PostgresDB = Depends(get_db_client),
) -> ObligationsRepository:
    """Get obligations repository dependency."""
    return ObligationsRepository(client)


def get_sources_repository(
    client: PostgresDB = Depends(get_db_client),
) -> SourcesRepository:
    """Get sources repository dependency."""
    return SourcesRepository(client)


def get_applications_repository(
    client: PostgresDB = Depends(get_db_client),
) -> ApplicationsRepository:
    """Get applications repository dependency."""
    return ApplicationsRepository(client)


def get_documents_repository(
    client: PostgresDB = Depends(get_db_client),
) -> DocumentsRepository:
    """Get documents repository dependency."""
    return DocumentsRepository(client)


def get_handoffs_repository(
    client: PostgresDB = Depends(get_db_client),
) -> HandoffsRepository:
    """Get handoffs repository dependency."""
    return HandoffsRepository(client)


def get_workflow_events_repository(
    client: PostgresDB = Depends(get_db_client),
) -> WorkflowEventsRepository:
    """Get workflow events repository dependency."""
    return WorkflowEventsRepository(client)


def get_consistency_repository(
    client: PostgresDB = Depends(get_db_client),
) -> ConsistencyRepository:
    """Get consistency repository dependency."""
    return ConsistencyRepository(client)
