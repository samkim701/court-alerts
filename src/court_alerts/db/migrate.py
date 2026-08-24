from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from court_alerts.config import get_database_url

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


def build_alembic_config(database_url: str | None = None) -> Config:
    """Alembic config with the URL injected instead of hard-coded."""
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url or get_database_url())
    return config


def upgrade_to_head(database_url: str | None = None) -> None:
    """Bring a database up to the latest migration."""
    command.upgrade(build_alembic_config(database_url), "head")
