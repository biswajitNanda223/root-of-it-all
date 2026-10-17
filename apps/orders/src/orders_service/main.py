from __future__ import annotations

import httpx
from fastapi import FastAPI

from orders_service.api.v1 import orders, outbox
from orders_service.config import OrdersSettings, get_settings
from orders_service.infrastructure.models import Base
from rio_db import Database
from rio_web import create_service_app, database_lifespan

DESCRIPTION = """
**Orders service** - places orders against the **catalog** service.

Flow: `POST /api/v1/orders` -> reserve stock remotely (idempotent, all-or-nothing) -> persist order **and** an outbox
event in one transaction. If persisting fails, the reservation is released (compensation). Cancelling releases stock.

* Needs a bearer token from the identity service (`apps/api`); customers see only their own orders.
* `/internal/outbox` exposes unpublished events for a relay (transactional outbox pattern).
"""
TAGS = [
    {"name": "orders", "description": "Place, pay, cancel and read orders."},
    {"name": "internal", "description": "Outbox relay endpoints (service key)."},
]


def create_app(
    settings: OrdersSettings | None = None,
    *,
    catalog_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """`catalog_transport` is the DI seam for tests/e2e: point the gateway at an in-process catalog app."""
    settings = settings or get_settings()

    async def start(app: FastAPI, _: Database) -> None:
        app.state.catalog_http = httpx.AsyncClient(
            base_url=settings.catalog_url,
            timeout=settings.catalog_timeout_seconds,
            transport=catalog_transport,
        )

    async def stop(app: FastAPI, _: Database) -> None:
        await app.state.catalog_http.aclose()

    return create_service_app(
        settings,
        title="Orders service",
        description=DESCRIPTION,
        tags=TAGS,
        lifespan=database_lifespan(metadata=Base.metadata, on_start=start, on_stop=stop),
        routers=[orders.router, outbox.router],
    )


def app_factory() -> FastAPI:
    return create_app()
