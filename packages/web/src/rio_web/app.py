"""One factory builds every service the same way: same middleware, errors, probes, docs, ids."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import Lifespan

from rio_core.config import CoreSettings
from rio_core.logging import configure_logging
from rio_web.errors import register_exception_handlers
from rio_web.health import health_router
from rio_web.middleware import RequestContextMiddleware
from rio_web.openapi import operation_id

SWAGGER_UI: dict[str, Any] = {
    "persistAuthorization": True,
    "displayRequestDuration": True,
    "filter": True,
    "tryItOutEnabled": True,
    "docExpansion": "list",
    "defaultModelsExpandDepth": 0,
}


def create_service_app(
    settings: CoreSettings,
    *,
    title: str,
    description: str,
    lifespan: Lifespan[FastAPI],
    routers: Sequence[APIRouter] = (),
    tags: list[dict[str, Any]] | None = None,
    version: str = "0.1.0",
    contact: dict[str, str] | None = None,
) -> FastAPI:
    configure_logging(settings.log_level, json_output=settings.log_json)
    docs = settings.docs_enabled
    app = FastAPI(
        title=title,
        version=version,
        description=description,
        contact=contact,
        openapi_tags=(tags or [])
        + [{"name": "health", "description": "Liveness and readiness probes."}],
        generate_unique_id_function=operation_id,
        servers=[{"url": settings.public_url}] if settings.public_url else None,
        swagger_ui_parameters=SWAGGER_UI,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings

    # Last added = outermost.
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    if settings.allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(health_router())
    for router in routers:
        app.include_router(router)
    return app
