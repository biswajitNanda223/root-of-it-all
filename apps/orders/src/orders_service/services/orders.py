"""Order use cases, including the reservation saga and compensation."""

from __future__ import annotations

import logging

from orders_service.domain.entities import Order, OrderStatus, WantedLine
from orders_service.domain.ports import (
    CatalogGateway,
    IdGenerator,
    OrderRepository,
    OutboxRepository,
)
from rio_auth import Principal
from rio_core.errors import ConflictError, ForbiddenError, NotFoundError

log = logging.getLogger(__name__)

# state machine: who may go where
_TRANSITIONS = {
    OrderStatus.pending: {OrderStatus.paid, OrderStatus.cancelled},
    OrderStatus.paid: set(),
    OrderStatus.cancelled: set(),
}


class OrderService:
    def __init__(
        self,
        orders: OrderRepository,
        outbox: OutboxRepository,
        catalog: CatalogGateway,
        ids: IdGenerator,
    ) -> None:
        self._orders = orders
        self._outbox = outbox
        self._catalog = catalog
        self._ids = ids

    async def place(self, who: Principal, wanted: list[WantedLine]) -> Order:
        reservation_id = f"order-{self._ids.new()}"
        lines = await self._catalog.reserve(reservation_id, wanted)  # 1) remote side effect
        try:
            order = await self._orders.add(
                customer_id=who.subject, reservation_id=reservation_id, lines=lines
            )
            await self._outbox.add(
                "order.created", {"order_id": order.id, "total": str(order.total)}
            )
        except Exception:
            # 2) local failure -> compensate the remote side effect, then surface the original error
            await self._release_quietly(reservation_id)
            raise
        return order

    async def _release_quietly(self, reservation_id: str) -> None:
        try:
            await self._catalog.release(reservation_id)
        except Exception:
            log.exception("compensation failed for %s - needs reconciliation", reservation_id)

    async def _visible(self, who: Principal, order_id: int) -> Order:
        order = await self._orders.get(order_id)
        if order is None:
            raise NotFoundError("Order not found")
        if order.customer_id != who.subject and not who.is_superuser:
            raise ForbiddenError("Not your order")
        return order

    async def get(self, who: Principal, order_id: int) -> Order:
        return await self._visible(who, order_id)

    async def list(
        self, who: Principal, *, status: OrderStatus | None, limit: int, offset: int
    ) -> tuple[list[Order], int]:
        owner = None if who.is_superuser else who.subject
        return await self._orders.list(customer_id=owner, status=status, limit=limit, offset=offset)

    async def _move(self, who: Principal, order_id: int, target: OrderStatus) -> Order:
        order = await self._visible(who, order_id)
        if target not in _TRANSITIONS[order.status]:
            raise ConflictError(f"cannot move an order from {order.status.value} to {target.value}")
        updated = await self._orders.set_status(order_id, target)
        await self._outbox.add(
            f"order.{target.value}", {"order_id": order_id, "total": str(order.total)}
        )
        return updated

    async def pay(self, who: Principal, order_id: int) -> Order:
        return await self._move(who, order_id, OrderStatus.paid)

    async def cancel(self, who: Principal, order_id: int) -> Order:
        order = await self._move(who, order_id, OrderStatus.cancelled)
        await self._catalog.release(
            order.reservation_id
        )  # give the stock back (idempotent upstream)
        return order
