"""
Database migrations (Alembic).

At startup `run_migrations()` brings the database to the latest revision:

- New database           -> `alembic upgrade head` creates everything.
- Pre-Alembic database   -> created by older versions with `create_all`.
  Missing columns/indexes are added (additive only), the database is stamped
  at the baseline revision, then upgraded normally.
- Alembic-managed DB     -> `alembic upgrade head`.

Create a new migration after changing models:
    cd backend && alembic revision --autogenerate -m "describe the change"
"""

import logging
import os

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app import models  # noqa: F401  # registers all tables on Base.metadata
from app.database import Base, engine

logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_REVISION = "0001"


def _alembic_config() -> Config:
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    cfg.attributes["configure_logger"] = False  # keep the app's logging setup
    return cfg


def _column_ddl(column, dialect) -> str:
    ddl = f'"{column.name}" {column.type.compile(dialect=dialect)}'
    if column.server_default is not None:
        default = column.server_default.arg
        default = default.text if hasattr(default, "text") else str(default)
        ddl += f" DEFAULT {default}" if default.lstrip("-").isdigit() else f" DEFAULT '{default}'"
        if not column.nullable:
            ddl += " NOT NULL"
    return ddl


def _adopt_legacy_schema() -> None:
    """Bring a create_all-era database up to the baseline shape (additive only)."""
    Base.metadata.create_all(bind=engine)  # missing tables
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing_cols:
                    logger.info(f"🛠️  Adding column {table.name}.{column.name}")
                    conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {_column_ddl(column, engine.dialect)}'))
            existing_idx = {i["name"] for i in inspector.get_indexes(table.name)}
            for index in table.indexes:
                if index.name not in existing_idx:
                    logger.info(f"🛠️  Adding index {index.name}")
                    index.create(conn)


def run_migrations() -> None:
    cfg = _alembic_config()
    tables = set(inspect(engine).get_table_names())
    if "alembic_version" not in tables and "users" in tables:
        logger.info("📦 Adopting pre-Alembic database schema")
        _adopt_legacy_schema()
        command.stamp(cfg, BASELINE_REVISION)
    command.upgrade(cfg, "head")


# Backward-compatible name used by older code paths
ensure_schema = run_migrations
