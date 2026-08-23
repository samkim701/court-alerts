from __future__ import annotations

import os

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://court_alerts:local_dev_only@localhost:5433/court_alerts"
)


def get_database_url() -> str:
    """Connection string, overridable by env for Cloud Run."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)