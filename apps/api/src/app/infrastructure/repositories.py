"""SQLAlchemy adapters for the domain ports."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Item, User
from app.infrastructure.models import ItemModel, UserModel
from rio_core.errors import NotFoundError


def _user(m: UserModel) -> User:
    return User(
        m.id, m.email, m.hashed_password, m.full_name, m.is_active, m.is_superuser, m.created_at
    )


def _item(m: ItemModel) -> Item:
    return Item(m.id, m.owner_id, m.title, m.description, m.created_at, m.updated_at)


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, user_id: int) -> User | None:
        m = await self._s.get(UserModel, user_id)
        return _user(m) if m else None

    async def get_by_email(self, email: str) -> User | None:
        m = await self._s.scalar(select(UserModel).where(UserModel.email == email))
        return _user(m) if m else None

    async def add(
        self, *, email: str, hashed_password: str, full_name: str | None, is_superuser: bool = False
    ) -> User:
        m = UserModel(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_superuser=is_superuser,
            is_active=True,
        )
        self._s.add(m)
        await self._s.flush()
        await self._s.refresh(m)
        return _user(m)

    async def list(self, *, limit: int, offset: int) -> tuple[list[User], int]:
        total = await self._s.scalar(select(func.count()).select_from(UserModel)) or 0
        rows = await self._s.scalars(
            select(UserModel).order_by(UserModel.id).limit(limit).offset(offset)
        )
        return [_user(m) for m in rows], total


class SqlItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, item_id: int) -> Item | None:
        m = await self._s.get(ItemModel, item_id)
        return _item(m) if m else None

    async def list_for_owner(
        self, owner_id: int, *, limit: int, offset: int
    ) -> tuple[list[Item], int]:
        where = ItemModel.owner_id == owner_id
        total = await self._s.scalar(select(func.count()).select_from(ItemModel).where(where)) or 0
        rows = await self._s.scalars(
            select(ItemModel).where(where).order_by(ItemModel.id).limit(limit).offset(offset)
        )
        return [_item(m) for m in rows], total

    async def add(self, *, owner_id: int, title: str, description: str | None) -> Item:
        m = ItemModel(owner_id=owner_id, title=title, description=description)
        self._s.add(m)
        await self._s.flush()
        await self._s.refresh(m)
        return _item(m)

    async def update(self, item_id: int, *, title: str | None, description: str | None) -> Item:
        m = await self._s.get(ItemModel, item_id)
        if m is None:
            raise NotFoundError("Item not found")
        if title is not None:
            m.title = title
        if description is not None:
            m.description = description
        await self._s.flush()
        await self._s.refresh(m)
        return _item(m)

    async def delete(self, item_id: int) -> None:
        m = await self._s.get(ItemModel, item_id)
        if m is not None:
            await self._s.delete(m)
            await self._s.flush()
