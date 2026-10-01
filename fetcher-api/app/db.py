"""Database access: one connection pool per gunicorn worker process."""

from typing import Any

from psycopg.conninfo import make_conninfo # pyright: ignore[reportMissingImports]
from psycopg.rows import dict_row # pyright: ignore[reportMissingImports]
from psycopg.types.json import Jsonb # pyright: ignore[reportMissingImports]
from psycopg_pool import ConnectionPool # pyright: ignore[reportMissingImports]

_pool = None


def init_pool(config):
    global _pool
    conninfo = make_conninfo(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    # The pool opens connections in the background, so the app can start
    # even if the database is briefly unavailable.
    _pool = ConnectionPool(
        conninfo,
        min_size=1,
        max_size=4,
        timeout=3,  # seconds to wait for a free connection
        kwargs={"row_factory": dict_row},
        open=True,
    )


def is_healthy() -> bool:
    try:
        with _pool.connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def insert_request(endpoint, params, status_code, duration_ms, response, error) -> Any:
    """Store one history row and return it, including the generated id and created_at."""
    # %s placeholders: psycopg sends values separately from the SQL, so no SQL injection.
    with _pool.connection() as conn:
        row = conn.execute(
            """
            INSERT INTO requests_history
                (endpoint, params, status_code, duration_ms, response, error)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, endpoint, params, status_code,
                      duration_ms, response, error
            """,
            (
                endpoint,
                Jsonb(params),
                status_code,
                duration_ms,
                Jsonb(response) if response is not None else None,
                error,
            ),
        ).fetchone()
    row["created_at"] = row["created_at"].isoformat()
    return row
