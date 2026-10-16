from __future__ import annotations

from app.domain.entities import Item, User
from app.domain.ports import ItemRepository
from rio_core.errors import ForbiddenError, NotFoundError


class ItemService:
    def __init__(self, items: ItemRepository) -> None:
        self._items = items

    async def _owned(self, actor: User, item_id: int) -> Item:
        item = await self._items.get(item_id)
        if item is None:
            raise NotFoundError("Item not found")
        if item.owner_id != actor.id and not actor.is_superuser:
            raise ForbiddenError("Not your item")
        return item

    async def list(self, actor: User, *, limit: int, offset: int) -> tuple[list[Item], int]:
        return await self._items.list_for_owner(actor.id, limit=limit, offset=offset)

    async def create(self, actor: User, *, title: str, description: str | None) -> Item:
        return await self._items.add(owner_id=actor.id, title=title, description=description)

    async def get(self, actor: User, item_id: int) -> Item:
        return await self._owned(actor, item_id)

    async def update(
        self, actor: User, item_id: int, *, title: str | None, description: str | None
    ) -> Item:
        await self._owned(actor, item_id)
        return await self._items.update(item_id, title=title, description=description)

    async def delete(self, actor: User, item_id: int) -> None:
        await self._owned(actor, item_id)
        await self._items.delete(item_id)
