"""Shared FastAPI plumbing for every service in the monorepo."""

from rio_web.app import create_service_app
from rio_web.deps import get_db, get_session
from rio_web.errors import register_exception_handlers
from rio_web.health import health_router
from rio_web.lifespan import database_lifespan
from rio_web.openapi import operation_id

__all__ = [
    "create_service_app",
    "database_lifespan",
    "get_db",
    "get_session",
    "health_router",
    "operation_id",
    "register_exception_handlers",
]
