"""Database access: one connection pool per gunicorn worker process."""

from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

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


def is_healthy():
    try:
        with _pool.connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
