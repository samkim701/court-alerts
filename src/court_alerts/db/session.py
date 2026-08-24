from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from court_alerts.config import get_database_url

engine = create_engine(get_database_url(), future=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
