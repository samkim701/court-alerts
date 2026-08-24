from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://court_alerts:local_dev_only@localhost:5433/court_alerts"
)

CLUB_NAME = "Life Time Centreville"

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def get_database_url() -> str:
    """Connection string, resolved in three steps.

    An explicit DATABASE_URL always wins. On Cloud Run the password
    arrives separately as a secret, so the URL is assembled from parts
    when a Cloud SQL socket path is present. Otherwise fall back to the
    local docker compose database.
    """
    direct_url = os.environ.get("DATABASE_URL")
    if direct_url:
        return direct_url

    socket_path = os.environ.get("CLOUD_SQL_SOCKET")
    if socket_path:
        user = os.environ.get("DB_USER", "court_alerts")
        password = os.environ.get("DB_PASSWORD", "")
        name = os.environ.get("DB_NAME", "court_alerts")
        return f"postgresql+psycopg://{user}:{password}@/{name}" f"?host={socket_path}"

    return DEFAULT_DATABASE_URL


def get_discord_webhook_url() -> str | None:
    """None when unset, so the app can fall back to console output."""
    return os.environ.get("DISCORD_WEBHOOK_URL") or None


def get_gemini_api_key() -> str | None:
    """None when unset, so triage degrades instead of crashing."""
    return os.environ.get("GEMINI_API_KEY") or None
