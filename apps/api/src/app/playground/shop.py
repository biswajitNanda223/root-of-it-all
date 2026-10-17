"""Dummy *end-to-end* domain: products -> orders -> payment -> events.

An in-memory store keeps the demo dependency-free. It shows: filtering/sorting/pagination via a query model,
PUT/PATCH/DELETE, validation, idempotency keys, a state machine, background tasks, SSE, CSV export,
OpenAPI `callbacks` and `webhooks`.
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.schemas import Problem
from app.playground.models import (
    Order,
    OrderEvent,
    OrderIn,
    OrderLine,
    OrderPaidEvent,
    OrderStatus,
    PaymentCallback,
    Product,
    ProductIn,
    ProductPatch,
)
from rio_core.errors import ConflictError, NotFoundError
from rio_core.pagination import Page

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


class ShopStore:
    """Not persisted. One asyncio lock keeps multi-step updates (stock reservation) atomic."""

    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.reset()

    def reset(self) -> None:
        self.products: dict[int, Product] = {}
        self.orders: dict[int, Order] = {}
        self.idempotency: dict[str, int] = {}
        self._pid = self._oid = 0

    def next_pid(self) -> int:
        self._pid += 1
        return self._pid

    def next_oid(self) -> int:
        self._oid += 1
        return self._oid


def get_shop(request: Request) -> ShopStore:
    store: ShopStore = request.app.state.shop
    return store


Shop = Annotated[ShopStore, Depends(get_shop)]

router = APIRouter(prefix="/shop", tags=["playground: shop (end-to-end)"])

# ----------------------------------------------------------------------------------------- products


class ProductFilters(BaseModel):
    q: str | None = Field(default=None, description="Substring of name or sku")
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    in_stock: bool | None = None
    sort: Literal["price", "-price", "name", "-name", "id"] = "id"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


@router.post(
    "/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": Problem}},
)
async def create_product(body: ProductIn, shop: Shop) -> Product:
    async with shop.lock:
        if any(p.sku == body.sku for p in shop.products.values()):
            raise ConflictError(f"sku {body.sku} exists")
        product = Product(id=shop.next_pid(), created_at=_now(), **body.model_dump())
        shop.products[product.id] = product
        return product


@router.get("/products", response_model=Page[Product], summary="Filter, sort and paginate")
async def list_products(f: Annotated[ProductFilters, Query()], shop: Shop) -> Page[Product]:
    items = list(shop.products.values())
    if f.q:
        needle = f.q.lower()
        items = [p for p in items if needle in p.name.lower() or needle in p.sku.lower()]
    if f.min_price is not None:
        items = [p for p in items if p.price >= f.min_price]
    if f.max_price is not None:
        items = [p for p in items if p.price <= f.max_price]
    if f.in_stock is not None:
        items = [p for p in items if (p.stock > 0) is f.in_stock]
    key = f.sort.lstrip("-")
    items.sort(key=lambda p: getattr(p, key), reverse=f.sort.startswith("-"))
    return Page(
        items=items[f.offset : f.offset + f.limit], total=len(items), limit=f.limit, offset=f.offset
    )


def _product(shop: ShopStore, product_id: int) -> Product:
    try:
        return shop.products[product_id]
    except KeyError:
        raise NotFoundError(f"product {product_id} not found") from None


@router.get("/products/{product_id}", response_model=Product, responses={404: {"model": Problem}})
async def get_product(product_id: int, shop: Shop) -> Product:
    return _product(shop, product_id)


@router.put("/products/{product_id}", response_model=Product, summary="Replace")
async def replace_product(product_id: int, body: ProductIn, shop: Shop) -> Product:
    async with shop.lock:
        old = _product(shop, product_id)
        shop.products[product_id] = Product(
            id=old.id, created_at=old.created_at, **body.model_dump()
        )
        return shop.products[product_id]


@router.patch("/products/{product_id}", response_model=Product, summary="Partial update")
async def patch_product(product_id: int, body: ProductPatch, shop: Shop) -> Product:
    async with shop.lock:
        old = _product(shop, product_id)
        shop.products[product_id] = old.model_copy(update=body.model_dump(exclude_unset=True))
        return shop.products[product_id]


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, shop: Shop) -> Response:
    async with shop.lock:
        _product(shop, product_id)
        del shop.products[product_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------------------------------ orders
callback_router = APIRouter()


@callback_router.post(
    "{$request.body.callback_url}", response_model=None, summary="Payment status callback"
)
def payment_callback(body: PaymentCallback) -> None:
    """We POST this to the caller's `callback_url` when the order is paid. (Documentation only: the demo never
    makes outbound requests, which avoids SSRF in a public sandbox.)"""


def _event(order: Order, new: OrderStatus, note: str) -> None:
    order.status = new
    order.events.append(OrderEvent(at=_now(), status=new, note=note))


def _order(shop: ShopStore, order_id: int) -> Order:
    try:
        return shop.orders[order_id]
    except KeyError:
        raise NotFoundError(f"order {order_id} not found") from None


@router.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    callbacks=callback_router.routes,
    summary="Create an order (reserves stock; supports `Idempotency-Key`)",
    responses={
        404: {"model": Problem},
        409: {"model": Problem, "description": "Insufficient stock"},
    },
)
async def create_order(
    body: OrderIn,
    shop: Shop,
    response: Response,
    idempotency_key: Annotated[str | None, Header(max_length=100)] = None,
) -> Order:
    async with shop.lock:
        if idempotency_key and idempotency_key in shop.idempotency:
            response.headers["Idempotent-Replayed"] = "true"
            response.status_code = status.HTTP_200_OK
            return shop.orders[shop.idempotency[idempotency_key]]
        wanted: dict[int, int] = {}
        for line in body.lines:
            wanted[line.product_id] = wanted.get(line.product_id, 0) + line.quantity
        total = Decimal(0)
        for pid, qty in wanted.items():  # validate everything first -> all-or-nothing
            product = _product(shop, pid)
            if product.stock < qty:
                raise ConflictError(f"only {product.stock} of '{product.name}' in stock")
            total += product.price * qty
        for pid, qty in wanted.items():
            shop.products[pid] = shop.products[pid].model_copy(
                update={"stock": shop.products[pid].stock - qty}
            )
        order = Order(
            id=shop.next_oid(),
            status=OrderStatus.pending,
            lines=[OrderLine(product_id=p, quantity=q) for p, q in wanted.items()],
            total=total,
            events=[],
            created_at=_now(),
        )
        _event(order, OrderStatus.pending, "order created")
        shop.orders[order.id] = order
        if idempotency_key:
            shop.idempotency[idempotency_key] = order.id
        return order


@router.get("/orders", response_model=Page[Order])
async def list_orders(
    shop: Shop,
    status_: Annotated[OrderStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[Order]:
    orders = [o for o in shop.orders.values() if status_ is None or o.status is status_]
    return Page(
        items=orders[offset : offset + limit], total=len(orders), limit=limit, offset=offset
    )


@router.get(
    "/orders/export.csv", response_class=StreamingResponse, summary="CSV export of all orders"
)
async def export_orders(shop: Shop) -> StreamingResponse:
    async def gen() -> AsyncIterator[str]:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "status", "total", "lines"])
        for o in list(shop.orders.values()):
            w.writerow([o.id, o.status.value, o.total, len(o.lines)])
        yield buf.getvalue()

    return StreamingResponse(gen(), media_type="text/csv")


@router.get("/orders/{order_id}", response_model=Order, responses={404: {"model": Problem}})
async def get_order(order_id: int, shop: Shop) -> Order:
    return _order(shop, order_id)


def _emit_paid(order_id: int, total: Decimal) -> None:
    """Background task: fan out the documented `order-paid` webhook (here: just a log line)."""
    event = OrderPaidEvent(order_id=order_id, total=total, paid_at=_now())
    log.info("webhook order-paid %s", event.model_dump_json())


@router.post(
    "/orders/{order_id}/pay",
    response_model=Order,
    summary="pending -> paid (emits webhook)",
    responses={409: {"model": Problem}},
)
async def pay_order(order_id: int, shop: Shop, background: BackgroundTasks) -> Order:
    async with shop.lock:
        order = _order(shop, order_id)
        if order.status is not OrderStatus.pending:
            raise ConflictError(f"cannot pay an order that is {order.status.value}")
        _event(order, OrderStatus.paid, "payment captured")
    background.add_task(_emit_paid, order.id, order.total)
    return order


@router.post(
    "/orders/{order_id}/cancel",
    response_model=Order,
    summary="pending -> cancelled (restocks)",
    responses={409: {"model": Problem}},
)
async def cancel_order(order_id: int, shop: Shop) -> Order:
    async with shop.lock:
        order = _order(shop, order_id)
        if order.status is not OrderStatus.pending:
            raise ConflictError(f"cannot cancel an order that is {order.status.value}")
        for line in order.lines:
            if line.product_id in shop.products:
                p = shop.products[line.product_id]
                shop.products[p.id] = p.model_copy(update={"stock": p.stock + line.quantity})
        _event(order, OrderStatus.cancelled, "cancelled by customer")
        return order


@router.get(
    "/orders/{order_id}/events", response_class=StreamingResponse, summary="Order timeline as SSE"
)
async def order_events(order_id: int, shop: Shop) -> StreamingResponse:
    order = _order(shop, order_id)

    async def gen() -> AsyncIterator[str]:
        for ev in list(order.events):
            yield f"event: {ev.status.value}\ndata: {ev.model_dump_json()}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/_reset", status_code=status.HTTP_204_NO_CONTENT, summary="Wipe the in-memory shop")
async def reset(shop: Shop) -> Response:
    shop.reset()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
