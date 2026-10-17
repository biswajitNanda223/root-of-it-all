"""Pydantic models used across the playground (nested models, unions, examples, computed fields)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Color(StrEnum):
    red = "red"
    green = "green"
    blue = "blue"


class Address(BaseModel):
    street: str
    city: str
    country: Annotated[str, Field(min_length=2, max_length=2, description="ISO-3166 alpha-2")]


class Customer(BaseModel):
    """Nested model + list of nested models."""

    name: str = Field(examples=["Ada Lovelace"])
    emails: list[str] = Field(default_factory=list)
    address: Address | None = None
    tags: set[str] = Field(default_factory=set, description="A set de-duplicates automatically")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Ada Lovelace",
                    "emails": ["ada@example.com"],
                    "address": {"street": "1 Analytical Way", "city": "London", "country": "GB"},
                    "tags": ["vip", "vip", "beta"],
                }
            ]
        }
    )


class Cat(BaseModel):
    pet_type: Literal["cat"]
    lives: int = 9


class Dog(BaseModel):
    pet_type: Literal["dog"]
    good_boy: bool = True


Pet = Annotated[Cat | Dog, Field(discriminator="pet_type")]


class Rectangle(BaseModel):
    width: float = Field(gt=0)
    height: float = Field(gt=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def area(self) -> float:
        return self.width * self.height


class AccountIn(BaseModel):
    """Input has the secret; the response model (AccountOut) must never echo it."""

    username: str
    password: str = Field(min_length=8)
    nickname: str | None = None


class AccountOut(BaseModel):
    username: str
    nickname: str | None = None


class Prefs(BaseModel):
    """PATCH demo: only provided fields change (`exclude_unset`)."""

    theme: Literal["light", "dark"] = "light"
    page_size: int = Field(default=20, ge=1, le=100)
    beta: bool = False


class PrefsPatch(BaseModel):
    theme: Literal["light", "dark"] | None = None
    page_size: int | None = Field(default=None, ge=1, le=100)
    beta: bool | None = None


class QueryFilters(BaseModel):
    """Query-parameter model: validated as a group, extra params rejected."""

    model_config = ConfigDict(extra="forbid")
    q: str | None = Field(default=None, max_length=50)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


class CommonHeaders(BaseModel):
    """Header-parameter model. Real requests carry many headers, so extras are ignored (not forbidden)."""

    model_config = ConfigDict(extra="ignore")
    host: str | None = None
    user_agent: str | None = None
    x_tracking: list[str] = []


class ContactForm(BaseModel):
    """Form-data model."""

    model_config = ConfigDict(extra="forbid")
    name: str
    email: str
    message: str = Field(max_length=500)


# --------------------------------------------------------------------------------------- shop (E2E)
class ProductIn(BaseModel):
    sku: str = Field(pattern=r"^[A-Z0-9-]{3,20}$", examples=["MUG-001"])
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=["12.50"])
    stock: int = Field(default=0, ge=0)
    color: Color | None = None


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    color: Color | None = None


class Product(ProductIn):
    id: int
    created_at: datetime


class OrderLine(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=100)


class OrderIn(BaseModel):
    lines: list[OrderLine] = Field(min_length=1, max_length=50)
    callback_url: str | None = Field(
        default=None, description="If set, the (documented) payment callback is delivered here."
    )


class OrderStatus(StrEnum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class OrderEvent(BaseModel):
    at: datetime
    status: OrderStatus
    note: str


class Order(BaseModel):
    id: int
    status: OrderStatus
    lines: list[OrderLine]
    total: Decimal
    events: list[OrderEvent]
    created_at: datetime


class PaymentCallback(BaseModel):
    """Body we would POST to `callback_url` (documented via OpenAPI `callbacks`)."""

    order_id: int
    status: OrderStatus
    total: Decimal


class OrderPaidEvent(BaseModel):
    """Documented under OpenAPI `webhooks`."""

    order_id: int
    total: Decimal
    paid_at: datetime
