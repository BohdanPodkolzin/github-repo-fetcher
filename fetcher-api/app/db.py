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
    return _serialize(row)


def list_requests(page, per_page, status=None, status_is_null=False, req_type=None) -> Any:
    """Return (items, total) for one page of history, newest first, without the big response column."""
    # Only fixed SQL text is assembled here; every user value travels as a %s parameter.
    conditions = []
    values = []
    if status_is_null:
        conditions.append("status_code IS NULL")
    elif status is not None:
        conditions.append("status_code = %s")
        values.append(status)
    if req_type is not None:
        conditions.append("endpoint = %s")
        values.append(req_type)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with _pool.connection() as conn:
        total = conn.execute(
            f"SELECT count(*) AS total FROM requests_history {where}", values
        ).fetchone()["total"]
        rows = conn.execute(
            f"""
            SELECT id, created_at, endpoint, params, status_code, duration_ms, error
            FROM requests_history
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT %s OFFSET %s
            """,
            values + [per_page, (page - 1) * per_page],
        ).fetchall()
    return [_serialize(row) for row in rows], total


def get_request(request_id) -> Any:
    """Return one full history row (including response), or None if the id does not exist."""
    with _pool.connection() as conn:
        row = conn.execute(
            """
            SELECT id, created_at, endpoint, params, status_code,
                   duration_ms, response, error
            FROM requests_history
            WHERE id = %s
            """,
            (request_id,),
        ).fetchone()
    return _serialize(row) if row else None


def _serialize(row):
    # ISO 8601 text (e.g. 2026-10-01T18:43:51+00:00) is what JavaScript's Date parses directly.
    row["created_at"] = row["created_at"].isoformat()
    return row
