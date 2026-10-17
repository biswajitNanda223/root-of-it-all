from __future__ import annotations

from fastapi import FastAPI

from catalog_service.api.v1 import catalog, internal
from catalog_service.config import CatalogSettings, get_settings
from catalog_service.infrastructure.models import Base
from rio_web import create_service_app, database_lifespan

DESCRIPTION = """
**Catalog service** - categories, products and stock.

* Reads are public; writes need an **administrator token** minted by the identity service (`apps/api`).
* `/internal/stock/*` is for other services (header `X-Service-Key`): idempotent, all-or-nothing reservations.
* Owns its database (`CATALOG_DATABASE_URL`) and Alembic history.
"""
TAGS = [
    {"name": "catalog", "description": "Browse and manage products and categories."},
    {"name": "internal", "description": "Service-to-service stock reservation protocol."},
]


def create_app(settings: CatalogSettings | None = None) -> FastAPI:
    return create_service_app(
        settings or get_settings(),
        title="Catalog service",
        description=DESCRIPTION,
        tags=TAGS,
        lifespan=database_lifespan(metadata=Base.metadata),
        routers=[catalog.router, internal.router],
    )


def app_factory() -> FastAPI:
    return create_app()
