from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Category:
    id: int
    name: str
    slug: str


@dataclass(frozen=True, slots=True)
class Product:
    id: int
    sku: str
    name: str
    description: str | None
    price: Decimal
    stock: int
    category_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class StockLine:
    product_id: int
    quantity: int


@dataclass(frozen=True, slots=True)
class PricedLine:
    product_id: int
    sku: str
    name: str
    unit_price: Decimal
    quantity: int


@dataclass(frozen=True, slots=True)
class Reservation:
    reservation_id: str
    status: str  # reserved | released
    lines: list[PricedLine]
