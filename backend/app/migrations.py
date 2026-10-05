"""
Lightweight schema migration.

`Base.metadata.create_all` creates missing tables but never alters existing
ones. This adds any columns that exist on the models but are missing from
the live database (additive changes only), so older databases keep working
after model upgrades.
"""

import logging

from sqlalchemy import inspect, text

from app.database import Base, engine
from app import models  # noqa: F401  # registers all tables on Base.metadata

logger = logging.getLogger(__name__)


def _column_ddl(column, dialect) -> str:
    col_type = column.type.compile(dialect=dialect)
    ddl = f'"{column.name}" {col_type}'
    if column.server_default is not None:
        default = column.server_default.arg
        default = default.text if hasattr(default, "text") else str(default)
        ddl += f" DEFAULT {default}" if default.lstrip("-").isdigit() else f" DEFAULT '{default}'"
        if not column.nullable:
            ddl += " NOT NULL"
    return ddl


def ensure_schema() -> None:
    """Create missing tables and add missing columns."""
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                ddl = _column_ddl(column, engine.dialect)
                logger.info(f"🛠️  Migrating: adding column {table.name}.{column.name}")
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'))
