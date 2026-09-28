"""Database client factory — local PostgreSQL via psycopg pool."""

from functools import lru_cache

from app.core.config import get_settings
from app.db.postgres import PostgresDB, create_pool


@lru_cache
def get_db() -> PostgresDB:
    """Get cached local PostgreSQL database handle."""
    settings = get_settings()
    return PostgresDB(create_pool(settings.database_url))
