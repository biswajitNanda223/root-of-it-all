from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class OrderStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


@dataclass(frozen=True, slots=True)
class OrderLine:
    product_id: int
    sku: str
    name: str
    unit_price: Decimal
    quantity: int

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True, slots=True)
class Order:
    id: int
    customer_id: str
    status: OrderStatus
    reservation_id: str
    total: Decimal
    lines: list[OrderLine]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    id: int
    topic: str
    payload: dict[str, object]
    created_at: datetime
    published_at: datetime | None = field(default=None)


@dataclass(frozen=True, slots=True)
class WantedLine:
    product_id: int
    quantity: int
