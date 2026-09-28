"""Direct PostgreSQL access layer (psycopg 3 + connection pool).

Replaces the Supabase PostgREST client for database access. All SQL is
parameterized — user-controlled values are never interpolated.
Rows are returned as JSON-compatible dicts matching the previous
PostgREST response shapes (UUID/datetime/Decimal normalized).
"""
from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import Any

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool


def _normalize(value: Any) -> Any:
    """Convert driver-native values to JSON-compatible ones."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, memoryview):
        return bytes(value)
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return value


def _normalize_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: _normalize(v) for k, v in row.items()}


def _adapt_param(value: Any) -> Any:
    """Wrap mappings for jsonb columns (psycopg needs Jsonb).

    Sequences are left alone so text[] columns keep working; callers
    wrap jsonb-bound lists explicitly with Jsonb at the repository or
    service layer where the schema is known.
    """
    if isinstance(value, Jsonb):
        return value
    if isinstance(value, dict):
        return Jsonb(value)
    return value


def _adapt_params(params: tuple) -> tuple:
    return tuple(_adapt_param(v) for v in params)


class PostgresDB:
    """Thin parameterized-SQL wrapper around a psycopg connection pool."""

    def __init__(self, pool: ConnectionPool):
        self._pool = pool

    def fetch_all(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Run a SELECT-type query, return all rows as dicts."""
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, _adapt_params(params))
                rows = cur.fetchall() or []
                return [_normalize_row(dict(r)) for r in rows]  # type: ignore[arg-type]

    def fetch_one(self, query: str, params: tuple = ()) -> dict[str, Any] | None:
        """Run a SELECT-type query, return the first row or None."""
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query, _adapt_params(params))
                row = cur.fetchone()
                return _normalize_row(dict(row)) if row else None  # type: ignore[arg-type]

    def execute(self, query: str, params: tuple = ()) -> int:
        """Run INSERT/UPDATE/DELETE without RETURNING. Returns rowcount."""
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, _adapt_params(params))
                return cur.rowcount or 0

    def insert_one(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """INSERT one row, return it via RETURNING *."""
        columns = list(data.keys())
        stmt = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values}) RETURNING *").format(
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(stmt, _adapt_params(tuple(data[c] for c in columns)))
                row = cur.fetchone()
                assert row is not None
                return _normalize_row(dict(row))  # type: ignore[arg-type, return-value]

    def insert_many(self, table: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """INSERT many rows with uniform keys, return them via RETURNING *."""
        if not rows:
            return []
        columns = list(rows[0].keys())
        stmt = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values}) RETURNING *").format(
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                out: list[dict[str, Any]] = []
                for r in rows:
                    cur.execute(stmt, _adapt_params(tuple(r[c] for c in columns)))
                    row = cur.fetchone()
                    assert row is not None
                    out.append(_normalize_row(dict(row)))  # type: ignore[arg-type]
                return out

    def upsert_one(
        self,
        table: str,
        data: dict[str, Any],
        conflict_columns: list[str],
    ) -> dict[str, Any]:
        """INSERT ... ON CONFLICT DO UPDATE, return the row via RETURNING *."""
        columns = list(data.keys())
        update_cols = [c for c in columns if c not in conflict_columns]
        stmt = sql.SQL(
            "INSERT INTO {table} ({fields}) VALUES ({values}) "
            "ON CONFLICT ({conflict}) DO UPDATE SET {updates} RETURNING *"
        ).format(
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(sql.Identifier(c) for c in columns),
            values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
            conflict=sql.SQL(", ").join(sql.Identifier(c) for c in conflict_columns),
            updates=sql.SQL(", ").join(
                sql.SQL("{f} = EXCLUDED.{f}").format(f=sql.Identifier(c))
                for c in update_cols
            ),
        )
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(stmt, _adapt_params(tuple(data[c] for c in columns)))
                row = cur.fetchone()
                assert row is not None
                return _normalize_row(dict(row))  # type: ignore[arg-type, return-value]

    def update_where(
        self, table: str, data: dict[str, Any], where: str, params: tuple
    ) -> list[dict[str, Any]]:
        """UPDATE ... WHERE <where> RETURNING *. `where` is static SQL."""
        set_clause = sql.SQL(", ").join(
            sql.SQL("{f} = %s").format(f=sql.Identifier(c)) for c in data
        )
        stmt = sql.SQL("UPDATE {table} SET {sets} WHERE {cond} RETURNING *").format(
            table=sql.Identifier(table),
            sets=set_clause,
            cond=sql.SQL(where),
        )
        return self.fetch_all(stmt.as_string(), _adapt_params(tuple(data.values()) + tuple(params)))

    def delete_where(self, table: str, where: str, params: tuple) -> int:
        """DELETE ... WHERE <where>. `where` is static SQL."""
        stmt = sql.SQL("DELETE FROM {table} WHERE {cond}").format(
            table=sql.Identifier(table),
            cond=sql.SQL(where),
        )
        return self.execute(stmt.as_string(), params)

    def count(self, table: str, where: str = "", params: tuple = ()) -> int:
        """SELECT COUNT(*) with optional static WHERE clause."""
        stmt = f"SELECT COUNT(*) AS n FROM {table}"
        if where:
            stmt += f" WHERE {where}"
        row = self.fetch_one(stmt, params)
        return int(row["n"]) if row else 0


def create_pool(database_url: str, **kwargs: Any) -> ConnectionPool:
    """Create a psycopg connection pool for the given DATABASE_URL."""
    options = {"min_size": 1, "max_size": 10, "open": True}
    options.update(kwargs)
    return ConnectionPool(database_url, **options)
