from __future__ import annotations

from fastapi import FastAPI

from billing_service.api.v1 import invoices
from billing_service.config import ServiceSettings, get_settings
from billing_service.infrastructure.models import Base
from rio_web import create_service_app, database_lifespan

DESCRIPTION = """
**Billing service** - one invoice per order, with a small state machine (`issued -> paid | void`).

* Admins issue and void invoices; customers see and pay only their own (identity tokens, verified statelessly).
* References orders by id only: no cross-database foreign keys, no imports from the orders service.
"""


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    return create_service_app(
        settings or get_settings(),
        title="Billing service",
        description=DESCRIPTION,
        tags=[{"name": "invoices", "description": "Issue, read, pay and void invoices."}],
        lifespan=database_lifespan(metadata=Base.metadata),
        routers=[invoices.router],
    )


def app_factory() -> FastAPI:
    return create_app()
