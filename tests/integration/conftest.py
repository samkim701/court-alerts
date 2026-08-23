import pytest
from sqlalchemy.orm import Session

from court_alerts.db.session import create_all, engine


@pytest.fixture(scope="session", autouse=True)
def _tables():
    create_all()


@pytest.fixture
def session():
    """Each test runs in a transaction that is rolled back afterwards."""
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)

    yield db

    db.close()
    transaction.rollback()
    connection.close()