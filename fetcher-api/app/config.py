"""All configuration comes from environment variables (nothing is hard-coded)."""

import os


def _required(name):
    value = os.environ.get(name)
    if not value:
        # Fail at startup with a clear message instead of a confusing error later.
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    def __init__(self):
        self.db_name = _required("POSTGRES_DB")
        self.db_user = _required("POSTGRES_USER")
        self.db_password = _required("POSTGRES_PASSWORD")
        # "db" is the compose service name; override these when moving to RDS.
        self.db_host = os.environ.get("DB_HOST", "db")
        self.db_port = int(os.environ.get("DB_PORT", "5432"))
        # Optional: without a token GitHub allows only 60 requests/hour.
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
