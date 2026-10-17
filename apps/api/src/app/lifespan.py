from __future__ import annotations

import logging

from fastapi import FastAPI

from app.infrastructure.models import Base
from app.infrastructure.repositories import SqlUserRepository
from app.services.auth import AuthService
from rio_auth import Argon2Hasher, JwtTokens
from rio_core.config import Settings
from rio_db import Database
from rio_web import database_lifespan

log = logging.getLogger(__name__)


async def _seed_superuser(app: FastAPI, db: Database) -> None:
    settings: Settings = app.state.settings
    if not (settings.first_superuser_email and settings.first_superuser_password):
        return
    async with db.session() as session:
        users = SqlUserRepository(session)
        auth = AuthService(
            users,
            Argon2Hasher(),
            JwtTokens(settings.secret_key.get_secret_value(), settings.access_token_expire_minutes),
        )
        if await users.get_by_email(settings.first_superuser_email.lower()) is None:
            await auth.register(
                email=settings.first_superuser_email,
                password=settings.first_superuser_password.get_secret_value(),
                full_name="Admin",
                is_superuser=True,
            )
            log.info("seeded first superuser")


lifespan = database_lifespan(metadata=Base.metadata, on_start=_seed_superuser)
