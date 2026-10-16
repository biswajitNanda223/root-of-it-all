from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.models import UserModel  # noqa: F401  (register mappers)
from app.infrastructure.repositories import SqlUserRepository
from app.infrastructure.security import Argon2Hasher, JwtTokens
from app.services.auth import AuthService
from rio_core.config import Settings
from rio_db import Base, Database

log = logging.getLogger(__name__)


async def _seed_superuser(db: Database, settings: Settings) -> None:
    if not (settings.first_superuser_email and settings.first_superuser_password):
        return
    async with db.session() as session:
        auth = AuthService(
            SqlUserRepository(session),
            Argon2Hasher(),
            JwtTokens(settings.secret_key.get_secret_value(), settings.access_token_expire_minutes),
        )
        users = SqlUserRepository(session)
        if await users.get_by_email(settings.first_superuser_email.lower()) is None:
            await auth.register(
                email=settings.first_superuser_email,
                password=settings.first_superuser_password.get_secret_value(),
                full_name="Admin",
                is_superuser=True,
            )
            log.info("seeded first superuser")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    db = Database(settings.database_url, echo=settings.db_echo)
    app.state.db = db
    if settings.auto_create_tables:
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await _seed_superuser(db, settings)
    log.info("started env=%s", settings.environment)
    try:
        yield
    finally:
        await db.dispose()
        log.info("stopped")
