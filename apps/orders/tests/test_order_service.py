"""Unit tests: the saga and state machine against in-memory fakes (no HTTP, no DB)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from orders_service.domain.entities import Order, OrderLine, OrderStatus, WantedLine
from orders_service.services.orders import OrderService
from rio_auth import Principal
from rio_core.errors import ConflictError, ForbiddenError, NotFoundError


class FakeCatalog:
    def __init__(self) -> None:
        self.reserved: list[str] = []
        self.released: list[str] = []

    async def reserve(self, reservation_id: str, lines: list[WantedLine]) -> list[OrderLine]:
        self.reserved.append(reservation_id)
        return [
            OrderLine(ln.product_id, f"SKU-{ln.product_id}", "n", Decimal("2.50"), ln.quantity)
            for ln in lines
        ]

    async def release(self, reservation_id: str) -> None:
        self.released.append(reservation_id)


class FakeOrders:
    def __init__(self, fail: bool = False) -> None:
        self.rows: dict[int, Order] = {}
        self.fail = fail

    async def add(self, *, customer_id: str, reservation_id: str, lines: list[OrderLine]) -> Order:
        if self.fail:
            raise RuntimeError("db down")
        now = datetime.now(UTC)
        order = Order(
            len(self.rows) + 1,
            customer_id,
            OrderStatus.pending,
            reservation_id,
            sum((ln.subtotal for ln in lines), Decimal(0)),
            lines,
            now,
            now,
        )
        self.rows[order.id] = order
        return order

    async def get(self, order_id: int) -> Order | None:
        return self.rows.get(order_id)

    async def list(self, *, customer_id, status, limit, offset):  # type: ignore[no-untyped-def]
        rows = [o for o in self.rows.values() if customer_id in (None, o.customer_id)]
        return rows, len(rows)

    async def set_status(self, order_id: int, status: OrderStatus) -> Order:
        o = self.rows[order_id]
        self.rows[order_id] = Order(
            o.id,
            o.customer_id,
            status,
            o.reservation_id,
            o.total,
            o.lines,
            o.created_at,
            o.updated_at,
        )
        return self.rows[order_id]


class FakeOutbox:
    def __init__(self) -> None:
        self.topics: list[str] = []

    async def add(self, topic: str, payload: dict[str, object]) -> None:
        self.topics.append(topic)


class FixedIds:
    def new(self) -> str:
        return "fixed"


ALICE, BOB, ADMIN = Principal("alice"), Principal("bob"), Principal("root", is_superuser=True)


def make(fail: bool = False) -> tuple[OrderService, FakeCatalog, FakeOutbox]:
    catalog, outbox = FakeCatalog(), FakeOutbox()
    return OrderService(FakeOrders(fail), outbox, catalog, FixedIds()), catalog, outbox  # type: ignore[arg-type]


async def test_place_reserves_prices_and_emits_event() -> None:
    svc, catalog, outbox = make()
    order = await svc.place(ALICE, [WantedLine(1, 2)])
    assert order.total == Decimal("5.00")
    assert catalog.reserved == ["order-fixed"]
    assert outbox.topics == ["order.created"]


async def test_local_failure_compensates_the_reservation() -> None:
    svc, catalog, _ = make(fail=True)
    with pytest.raises(RuntimeError):
        await svc.place(ALICE, [WantedLine(1, 1)])
    assert catalog.released == ["order-fixed"]


async def test_state_machine_and_ownership() -> None:
    svc, catalog, outbox = make()
    order = await svc.place(ALICE, [WantedLine(1, 1)])
    with pytest.raises(ForbiddenError):
        await svc.get(BOB, order.id)
    assert (await svc.get(ADMIN, order.id)).id == order.id
    with pytest.raises(NotFoundError):
        await svc.get(ALICE, 99)
    assert (await svc.pay(ALICE, order.id)).status is OrderStatus.paid
    with pytest.raises(ConflictError):
        await svc.cancel(ALICE, order.id)
    with pytest.raises(ConflictError):
        await svc.pay(ALICE, order.id)
    assert catalog.released == []
    second = await svc.place(ALICE, [WantedLine(2, 1)])
    await svc.cancel(ALICE, second.id)
    assert catalog.released == ["order-fixed"]
    assert outbox.topics == ["order.created", "order.paid", "order.created", "order.cancelled"]


async def test_list_scopes_to_owner_unless_admin() -> None:
    svc, _, _ = make()
    await svc.place(ALICE, [WantedLine(1, 1)])
    await svc.place(BOB, [WantedLine(1, 1)])
    assert (await svc.list(ALICE, status=None, limit=10, offset=0))[1] == 1
    assert (await svc.list(ADMIN, status=None, limit=10, offset=0))[1] == 2
