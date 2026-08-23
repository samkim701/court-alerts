from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from court_alerts.config import get_database_url
from court_alerts.db.tables import Base

engine = create_engine(get_database_url(), future=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def create_all() -> None:
    """Create any missing tables.

    A stand-in for Alembic while the schema is still moving.
    """
    Base.metadata.create_all(engine)