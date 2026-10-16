"""Application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import root, v1
from app.errors import register_exception_handlers
from app.lifespan import lifespan
from app.middleware import RequestContextMiddleware
from rio_core.config import Settings, get_settings
from rio_core.logging import configure_logging

TAGS = [
    {"name": "health", "description": "Liveness and readiness probes."},
    {"name": "auth", "description": "Registration and OAuth2 password-flow tokens."},
    {"name": "users", "description": "User profile and administration."},
    {"name": "items", "description": "Owner-scoped CRUD with pagination."},
    {"name": "files", "description": "Streaming, size-capped uploads."},
    {"name": "realtime", "description": "SSE and WebSocket examples."},
]


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, json_output=settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="Production-grade FastAPI service.",
        openapi_tags=TAGS,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings

    # Order: last added runs first (outermost).
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
    app.include_router(root)
    app.include_router(v1)
    return app


def app_factory() -> FastAPI:  # for `uvicorn --factory`
    return create_app()
