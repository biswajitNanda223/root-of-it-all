from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from orders_service.domain.entities import Order, OrderLine, OrderStatus, OutboxEvent
from orders_service.infrastructure.models import OrderLineModel, OrderModel, OutboxModel
from rio_core.errors import NotFoundError


def _order(m: OrderModel) -> Order:
    return Order(
        m.id,
        m.customer_id,
        OrderStatus(m.status),
        m.reservation_id,
        m.total,
        [OrderLine(ln.product_id, ln.sku, ln.name, ln.unit_price, ln.quantity) for ln in m.lines],
        m.created_at,
        m.updated_at,
    )


class SqlOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, *, customer_id: str, reservation_id: str, lines: list[OrderLine]) -> Order:
        total = sum((ln.subtotal for ln in lines), Decimal(0))
        m = OrderModel(
            customer_id=customer_id,
            status=OrderStatus.pending.value,
            reservation_id=reservation_id,
            total=total,
            lines=[
                OrderLineModel(
                    product_id=ln.product_id,
                    sku=ln.sku,
                    name=ln.name,
                    unit_price=ln.unit_price,
                    quantity=ln.quantity,
                )
                for ln in lines
            ],
        )
        self._s.add(m)
        await self._s.flush()
        await self._s.refresh(m)
        return _order(m)

    async def get(self, order_id: int) -> Order | None:
        m = await self._s.get(OrderModel, order_id)
        return _order(m) if m else None

    async def list(
        self, *, customer_id: str | None, status: OrderStatus | None, limit: int, offset: int
    ) -> tuple[list[Order], int]:
        where = []
        if customer_id is not None:
            where.append(OrderModel.customer_id == customer_id)
        if status is not None:
            where.append(OrderModel.status == status.value)
        total = (
            await self._s.scalar(select(func.count()).select_from(OrderModel).where(*where)) or 0
        )
        rows = await self._s.scalars(
            select(OrderModel)
            .where(*where)
            .order_by(OrderModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_order(m) for m in rows], total

    async def set_status(self, order_id: int, status: OrderStatus) -> Order:
        m = await self._s.get(OrderModel, order_id)
        if m is None:
            raise NotFoundError("Order not found")
        m.status = status.value
        await self._s.flush()
        await self._s.refresh(m)
        return _order(m)


class SqlOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, topic: str, payload: dict[str, object]) -> None:
        self._s.add(OutboxModel(topic=topic, payload=payload, created_at=datetime.now(UTC)))
        await self._s.flush()

    async def pending(self, limit: int) -> list[OutboxEvent]:
        rows = await self._s.scalars(
            select(OutboxModel)
            .where(OutboxModel.published_at.is_(None))
            .order_by(OutboxModel.id)
            .limit(limit)
        )
        return [OutboxEvent(m.id, m.topic, m.payload, m.created_at, m.published_at) for m in rows]

    async def mark_published(self, event_id: int) -> None:
        m = await self._s.get(OutboxModel, event_id)
        if m is None:
            raise NotFoundError("Outbox event not found")
        m.published_at = datetime.now(UTC)
        await self._s.flush()
