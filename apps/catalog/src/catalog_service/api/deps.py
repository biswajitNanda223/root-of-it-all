"""Composition root for the catalog service (request scope)."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.config import CatalogSettings
from catalog_service.infrastructure.repositories import (
    SqlCategoryRepository,
    SqlProductRepository,
    SqlReservationRepository,
)
from catalog_service.services.catalog import CatalogService, StockService
from rio_auth import Principal, principal_dependency
from rio_core.errors import ForbiddenError
from rio_web import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Swagger's *Authorize* talks to the identity service, which mints the tokens we verify.
_TOKEN_URL = os.environ.get("IDENTITY_TOKEN_URL", "http://localhost:8000/api/v1/auth/token")
current_principal = principal_dependency(_TOKEN_URL)
PrincipalDep = Annotated[Principal, Depends(current_principal)]


def get_settings_dep(request: Request) -> CatalogSettings:
    settings: CatalogSettings = request.app.state.settings
    return settings


async def require_admin(principal: PrincipalDep) -> Principal:
    if not principal.is_superuser:
        raise ForbiddenError("Administrator token required")
    return principal


AdminDep = Annotated[Principal, Depends(require_admin)]


def get_catalog_service(session: SessionDep) -> CatalogService:
    return CatalogService(SqlCategoryRepository(session), SqlProductRepository(session))


def get_stock_service(session: SessionDep) -> StockService:
    return StockService(SqlProductRepository(session), SqlReservationRepository(session))


CatalogDep = Annotated[CatalogService, Depends(get_catalog_service)]
StockDep = Annotated[StockService, Depends(get_stock_service)]
