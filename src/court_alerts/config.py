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
    """Connection string, overridable by env for Cloud Run."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_discord_webhook_url() -> str | None:
    """None when unset, so the app can fall back to console output."""
    return os.environ.get("DISCORD_WEBHOOK_URL") or None

def get_gemini_api_key() -> str | None:
    """None when unset, so triage degrades instead of crashing."""
    return os.environ.get("GEMINI_API_KEY") or None