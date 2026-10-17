from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Kitchen"])


class CategoryOut(ORM):
    id: int
    name: str
    slug: str


class ProductIn(BaseModel):
    sku: str = Field(pattern=r"^[A-Z0-9-]{3,40}$", examples=["MUG-001"])
    name: str = Field(min_length=1, max_length=200, examples=["Enamel mug"])
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2, examples=["12.50"])
    stock: int = Field(default=0, ge=0)
    category_id: int | None = Field(default=None, ge=1)


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    category_id: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class ProductOut(ORM):
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


class ProductQuery(BaseModel):
    """Query-parameter model (also satisfies the `ProductFilter` port)."""

    model_config = ConfigDict(extra="forbid")
    q: str | None = Field(default=None, max_length=100)
    category_id: int | None = Field(default=None, ge=1)
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    in_stock: bool | None = None
    sort: Literal["id", "price", "-price", "name", "-name"] = "id"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class LineIn(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=1000)


class ReserveIn(BaseModel):
    reservation_id: str = Field(
        min_length=1, max_length=100, description="Caller-chosen idempotency key"
    )
    lines: list[LineIn] = Field(min_length=1, max_length=100)


class PricedLineOut(BaseModel):
    product_id: int
    sku: str
    name: str
    unit_price: Decimal
    quantity: int


class ReservationOut(BaseModel):
    reservation_id: str
    status: Literal["reserved", "released"]
    lines: list[PricedLineOut]
