"""Composition root for the orders service. Swap any adapter here (or override it in tests)."""

from __future__ import annotations

import os
from typing import Annotated

import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from orders_service.config import OrdersSettings
from orders_service.domain.ports import CatalogGateway, IdGenerator
from orders_service.infrastructure.catalog_client import HttpCatalogGateway, UuidGenerator
from orders_service.infrastructure.repositories import SqlOrderRepository, SqlOutboxRepository
from orders_service.services.orders import OrderService
from rio_auth import Principal, principal_dependency
from rio_web import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_TOKEN_URL = os.environ.get("IDENTITY_TOKEN_URL", "http://localhost:8000/api/v1/auth/token")
current_principal = principal_dependency(_TOKEN_URL)
PrincipalDep = Annotated[Principal, Depends(current_principal)]


def get_settings_dep(request: Request) -> OrdersSettings:
    settings: OrdersSettings = request.app.state.settings
    return settings


SettingsDep = Annotated[OrdersSettings, Depends(get_settings_dep)]


def get_catalog_gateway(request: Request, settings: SettingsDep) -> CatalogGateway:
    http: httpx.AsyncClient = request.app.state.catalog_http
    return HttpCatalogGateway(http, settings.service_key.get_secret_value())


def get_ids() -> IdGenerator:
    return UuidGenerator()


def get_order_service(
    session: SessionDep,
    catalog: Annotated[CatalogGateway, Depends(get_catalog_gateway)],
    ids: Annotated[IdGenerator, Depends(get_ids)],
) -> OrderService:
    return OrderService(SqlOrderRepository(session), SqlOutboxRepository(session), catalog, ids)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
