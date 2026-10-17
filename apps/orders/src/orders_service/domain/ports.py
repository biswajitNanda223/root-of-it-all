"""Ports. `CatalogGateway` is the anti-corruption boundary to another service."""

from __future__ import annotations

from typing import Protocol

from orders_service.domain.entities import Order, OrderLine, OrderStatus, OutboxEvent, WantedLine


class CatalogGateway(Protocol):
    async def reserve(self, reservation_id: str, lines: list[WantedLine]) -> list[OrderLine]:
        """Reserve stock and return priced lines. Raises ConflictError/NotFoundError/UpstreamError."""
        ...

    async def release(self, reservation_id: str) -> None: ...


class OrderRepository(Protocol):
    async def add(
        self, *, customer_id: str, reservation_id: str, lines: list[OrderLine]
    ) -> Order: ...
    async def get(self, order_id: int) -> Order | None: ...
    async def list(
        self, *, customer_id: str | None, status: OrderStatus | None, limit: int, offset: int
    ) -> tuple[list[Order], int]: ...
    async def set_status(self, order_id: int, status: OrderStatus) -> Order: ...


class OutboxRepository(Protocol):
    async def add(self, topic: str, payload: dict[str, object]) -> None: ...
    async def pending(self, limit: int) -> list[OutboxEvent]: ...
    async def mark_published(self, event_id: int) -> None: ...


class IdGenerator(Protocol):
    def new(self) -> str: ...
