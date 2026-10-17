from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field

from billing_service.api.deps import AdminDep, InvoiceServiceDep, PrincipalDep
from billing_service.domain.entities import InvoiceStatus
from rio_core.pagination import Page

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])
InvoiceId = Annotated[int, Path(ge=1)]


class InvoiceIn(BaseModel):
    order_id: int = Field(ge=1, examples=[1])
    customer_id: str = Field(
        min_length=1, max_length=64, description="`sub` of the customer's token", examples=["2"]
    )
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2, examples=["25.00"])


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    customer_id: str
    amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime


@router.post(
    "",
    response_model=InvoiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Issue an invoice for an order (admin; one per order)",
)
async def issue_invoice(body: InvoiceIn, _: AdminDep, svc: InvoiceServiceDep) -> InvoiceOut:
    return InvoiceOut.model_validate(
        await svc.issue(order_id=body.order_id, customer_id=body.customer_id, amount=body.amount)
    )


@router.get("", response_model=Page[InvoiceOut], summary="My invoices (admins see all)")
async def list_invoices(
    who: PrincipalDep,
    svc: InvoiceServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[InvoiceOut]:
    items, total = await svc.list(who, limit=limit, offset=offset)
    return Page(
        items=[InvoiceOut.model_validate(i) for i in items], total=total, limit=limit, offset=offset
    )


@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: InvoiceId, who: PrincipalDep, svc: InvoiceServiceDep
) -> InvoiceOut:
    return InvoiceOut.model_validate(await svc.get(who, invoice_id))


@router.post("/{invoice_id}/pay", response_model=InvoiceOut, summary="issued -> paid")
async def pay_invoice(
    invoice_id: InvoiceId, who: PrincipalDep, svc: InvoiceServiceDep
) -> InvoiceOut:
    return InvoiceOut.model_validate(await svc.pay(who, invoice_id))


@router.post("/{invoice_id}/void", response_model=InvoiceOut, summary="issued -> void (admin)")
async def void_invoice(
    invoice_id: InvoiceId, who: PrincipalDep, svc: InvoiceServiceDep
) -> InvoiceOut:
    return InvoiceOut.model_validate(await svc.void(who, invoice_id))
