import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from court_alerts.config import get_database_url
from court_alerts.db.migrate import upgrade_to_head

TEST_DB_NAME = "court_alerts_test"


def build_test_database_url() -> str:
    """A second database on the same server, so app data and test data
    can never contaminate each other."""
    admin_url = get_database_url()
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        ).scalar()
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))

    admin_engine.dispose()

    base_url = admin_url.rsplit("/", 1)[0]
    return f"{base_url}/{TEST_DB_NAME}"


TEST_DATABASE_URL = build_test_database_url()
test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Build the test schema through the real migrations, so a broken
    migration fails the suite instead of production."""
    upgrade_to_head(TEST_DATABASE_URL)


@pytest.fixture
def session():
    """Each test runs in a transaction that is rolled back afterwards."""
    connection = test_engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)

    yield db

    db.close()
    transaction.rollback()
    connection.close()
