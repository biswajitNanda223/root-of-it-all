from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from orders_service.domain.entities import OrderStatus


class LineIn(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=100)


class OrderIn(BaseModel):
    lines: list[LineIn] = Field(min_length=1, max_length=50)

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"lines": [{"product_id": 1, "quantity": 2}]}]}
    )


class LineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: int
    sku: str
    name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: str
    status: OrderStatus
    total: Decimal
    lines: list[LineOut]
    created_at: datetime
    updated_at: datetime


class OutboxOut(BaseModel):
    id: int
    topic: str
    payload: dict[str, object]
    created_at: datetime
