"""Async Alembic environment for the billing service (own URL, own version table)."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from billing_service.config import get_settings
from billing_service.infrastructure.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata
URL = get_settings().database_url
VERSION_TABLE = "alembic_version_billing"


def _configure(connection: Connection | None = None) -> None:
    context.configure(
        connection=connection,
        url=URL,
        target_metadata=target_metadata,
        version_table=VERSION_TABLE,
        compare_type=True,
        render_as_batch=URL.startswith("sqlite"),
        literal_binds=connection is None,
    )


def run_offline() -> None:
    _configure()
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    _configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    engine = create_async_engine(URL)
    async with engine.connect() as conn:
        await conn.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    run_offline()
else:
    asyncio.run(run_online())
