from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from orders_service.api.deps import OrderServiceDep, PrincipalDep
from orders_service.api.schemas import OrderIn, OrderOut
from orders_service.domain.entities import OrderStatus, WantedLine
from rio_core.pagination import Page

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
OrderId = Annotated[int, Path(ge=1)]


def _out(order: object) -> OrderOut:
    out = OrderOut.model_validate(order)
    return out


@router.post(
    "",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order (reserves stock in the catalog service)",
    responses={
        404: {"description": "Unknown product"},
        409: {"description": "Insufficient stock"},
        502: {"description": "Catalog service unavailable"},
    },
)
async def place_order(body: OrderIn, who: PrincipalDep, svc: OrderServiceDep) -> OrderOut:
    order = await svc.place(who, [WantedLine(ln.product_id, ln.quantity) for ln in body.lines])
    return _out(order)


@router.get("", response_model=Page[OrderOut], summary="My orders (admins see all)")
async def list_orders(
    who: PrincipalDep,
    svc: OrderServiceDep,
    status_: Annotated[OrderStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[OrderOut]:
    orders, total = await svc.list(who, status=status_, limit=limit, offset=offset)
    return Page(items=[_out(o) for o in orders], total=total, limit=limit, offset=offset)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: OrderId, who: PrincipalDep, svc: OrderServiceDep) -> OrderOut:
    return _out(await svc.get(who, order_id))


@router.post("/{order_id}/pay", response_model=OrderOut, summary="pending -> paid")
async def pay_order(order_id: OrderId, who: PrincipalDep, svc: OrderServiceDep) -> OrderOut:
    return _out(await svc.pay(who, order_id))


@router.post(
    "/{order_id}/cancel", response_model=OrderOut, summary="pending -> cancelled (releases stock)"
)
async def cancel_order(order_id: OrderId, who: PrincipalDep, svc: OrderServiceDep) -> OrderOut:
    return _out(await svc.cancel(who, order_id))
