from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool


class Database:
    """Owns the engine and hands out transactional sessions."""

    def __init__(self, url: str, *, echo: bool = False) -> None:
        kwargs: dict[str, object] = {}
        if url.endswith(":memory:") or url.endswith("sqlite+aiosqlite://"):
            kwargs.update(poolclass=StaticPool, connect_args={"check_same_thread": False})
        elif not url.startswith("sqlite"):
            kwargs.update(pool_pre_ping=True)
        self.engine: AsyncEngine = create_async_engine(url, echo=echo, **kwargs)
        self._factory = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Commit on success, roll back on error."""
        async with self._factory() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback()
                raise

    async def ping(self) -> bool:
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True

    async def dispose(self) -> None:
        await self.engine.dispose()
