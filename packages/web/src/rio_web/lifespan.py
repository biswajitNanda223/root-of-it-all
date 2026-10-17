from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import MetaData

from rio_core.config import CoreSettings
from rio_db import Database

log = logging.getLogger(__name__)
Hook = Callable[[FastAPI, Database], Awaitable[None]]


def database_lifespan(
    *, metadata: MetaData, on_start: Hook | None = None, on_stop: Hook | None = None
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Lifespan factory: owns the engine, optionally creates *this service's* tables (dev/test), runs hooks.

    Each service has its own declarative `Base` (own metadata), so services never create each other's tables.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings: CoreSettings = app.state.settings
        db = Database(settings.database_url, echo=settings.db_echo)
        app.state.db = db
        if settings.auto_create_tables:
            async with db.engine.begin() as conn:
                await conn.run_sync(metadata.create_all)
        if on_start:
            await on_start(app, db)
        log.info("%s started env=%s", settings.app_name, settings.environment)
        try:
            yield
        finally:
            if on_stop:
                await on_stop(app, db)
            await db.dispose()
            log.info("%s stopped", settings.app_name)

    return lifespan
