"""Request-scoped dependencies shared by all services (the DI backbone)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from rio_db import Database


def get_db(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One transaction per request (unit of work): commit on success, roll back on any error."""
    async with get_db(request).session() as session:
        yield session
