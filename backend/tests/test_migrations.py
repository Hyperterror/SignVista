"""Migrations must produce exactly the schema the ORM models describe."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.database import Base, engine
from app.migrations import run_migrations


def test_migrations_match_models(client):
    run_migrations()  # idempotent; the app already ran it at startup
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"compare_type": True, "render_as_batch": True})
        diff = compare_metadata(ctx, Base.metadata)
    assert diff == [], f"Models changed without a migration: {diff}. Run: alembic revision --autogenerate"
