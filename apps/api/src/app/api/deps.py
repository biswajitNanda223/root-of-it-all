"""Dependency-injection wiring: the composition root for request scope."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User
from app.infrastructure.repositories import SqlItemRepository, SqlUserRepository
from app.infrastructure.security import Argon2Hasher, JwtTokens
from app.services.auth import AuthService
from app.services.items import ItemService
from rio_core.config import Settings
from rio_core.errors import ForbiddenError
from rio_db import Database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_settings_dep(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_db(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


DbDep = Annotated[Database, Depends(get_db)]


async def get_session(db: DbDep) -> AsyncIterator[AsyncSession]:
    """One transaction per request (unit of work)."""
    async with db.session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service(session: SessionDep, settings: SettingsDep) -> AuthService:
    return AuthService(
        SqlUserRepository(session),
        Argon2Hasher(),
        JwtTokens(settings.secret_key.get_secret_value(), settings.access_token_expire_minutes),
    )


def get_item_service(session: SessionDep) -> ItemService:
    return ItemService(SqlItemRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], auth: AuthServiceDep
) -> User:
    return await auth.authenticate(token)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_superuser(user: CurrentUser) -> User:
    if not user.is_superuser:
        raise ForbiddenError("Superuser required")
    return user


SuperUser = Annotated[User, Depends(require_superuser)]
