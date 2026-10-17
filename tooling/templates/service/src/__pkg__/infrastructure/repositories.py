from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from __pkg__.infrastructure.models import NoteModel


class SqlNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, owner_id: str, title: str) -> NoteModel:
        m = NoteModel(owner_id=owner_id, title=title)
        self._s.add(m)
        await self._s.flush()
        await self._s.refresh(m)
        return m

    async def list_for(self, owner_id: str) -> list[NoteModel]:
        rows = await self._s.scalars(select(NoteModel).where(NoteModel.owner_id == owner_id).order_by(NoteModel.id))
        return list(rows)
