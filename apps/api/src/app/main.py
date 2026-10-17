"""Application factory for the identity / demo API."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import v1
from app.lifespan import lifespan
from app.openapi import CONTACT, DESCRIPTION, TAGS
from app.playground import router as playground
from rio_core.config import Settings, get_settings
from rio_web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = create_service_app(
        settings,
        title=settings.app_name,
        description=DESCRIPTION,
        contact=CONTACT,
        tags=TAGS + (playground.TAGS if settings.playground_enabled else []),
        lifespan=lifespan,
        routers=[v1],
    )
    if settings.playground_enabled:
        playground.register(app)
    return app


def app_factory() -> FastAPI:  # for `uvicorn --factory`
    return create_app()
