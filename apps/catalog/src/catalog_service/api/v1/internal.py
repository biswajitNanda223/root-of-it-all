"""Service-to-service endpoints. Authenticated with `X-Service-Key`, hidden from end-user clients by convention."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from catalog_service.api.deps import StockDep
from catalog_service.api.schemas import PricedLineOut, ReservationOut, ReserveIn
from catalog_service.domain.entities import Reservation, StockLine
from rio_auth import require_service_key

router = APIRouter(
    prefix="/internal/stock",
    tags=["internal"],
    dependencies=[Depends(require_service_key)],
)


def _out(r: Reservation) -> ReservationOut:
    return ReservationOut(
        reservation_id=r.reservation_id,
        status=r.status,
        lines=[PricedLineOut(**vars_(ln)) for ln in r.lines],
    )


def vars_(ln: object) -> dict[str, object]:
    return {k: getattr(ln, k) for k in ("product_id", "sku", "name", "unit_price", "quantity")}


@router.post(
    "/reserve", response_model=ReservationOut, summary="Reserve stock (idempotent, all-or-nothing)"
)
async def reserve(body: ReserveIn, svc: StockDep) -> ReservationOut:
    lines = [StockLine(ln.product_id, ln.quantity) for ln in body.lines]
    return _out(await svc.reserve(body.reservation_id, lines))


@router.post(
    "/release/{reservation_id}",
    response_model=ReservationOut,
    summary="Release a reservation (idempotent)",
)
async def release(reservation_id: str, svc: StockDep) -> ReservationOut:
    return _out(await svc.release(reservation_id))
