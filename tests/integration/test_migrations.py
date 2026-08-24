from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from court_alerts.db.tables import Base


def test_models_and_migrations_agree(session):
    """Fails when a model changed but no migration was generated."""
    context = MigrationContext.configure(session.connection())
    differences = compare_metadata(context, Base.metadata)

    assert differences == []
