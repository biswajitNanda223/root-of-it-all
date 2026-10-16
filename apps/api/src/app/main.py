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
from app.openapi import CONTACT, DESCRIPTION, SWAGGER_UI, TAGS, TERMS, operation_id
from app.playground import router as playground
from rio_core.config import Settings, get_settings
from rio_core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, json_output=settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="Production-grade FastAPI service.",
        openapi_tags=TAGS + (playground.TAGS if settings.playground_enabled else []),
        generate_unique_id_function=operation_id,
        servers=[{"url": settings.public_url}] if settings.public_url else None,
        description=DESCRIPTION,
        contact=CONTACT,
        terms_of_service=TERMS,
        swagger_ui_parameters=SWAGGER_UI,
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
    if settings.playground_enabled:
        playground.register(app)
    return app


def app_factory() -> FastAPI:  # for `uvicorn --factory`
    return create_app()
