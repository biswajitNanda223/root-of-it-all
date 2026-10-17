from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from billing_service.domain.entities import Invoice, InvoiceStatus
from billing_service.infrastructure.models import InvoiceModel
from rio_core.errors import NotFoundError


def _inv(m: InvoiceModel) -> Invoice:
    return Invoice(
        m.id,
        m.order_id,
        m.customer_id,
        m.amount,
        InvoiceStatus(m.status),
        m.created_at,
        m.updated_at,
    )


class SqlInvoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, *, order_id: int, customer_id: str, amount: Decimal) -> Invoice:
        m = InvoiceModel(
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            status=InvoiceStatus.issued.value,
        )
        self._s.add(m)
        await self._s.flush()
        await self._s.refresh(m)
        return _inv(m)

    async def get(self, invoice_id: int) -> Invoice | None:
        m = await self._s.get(InvoiceModel, invoice_id)
        return _inv(m) if m else None

    async def get_by_order(self, order_id: int) -> Invoice | None:
        m = await self._s.scalar(select(InvoiceModel).where(InvoiceModel.order_id == order_id))
        return _inv(m) if m else None

    async def list(
        self, *, customer_id: str | None, limit: int, offset: int
    ) -> tuple[list[Invoice], int]:
        where = [InvoiceModel.customer_id == customer_id] if customer_id is not None else []
        total = (
            await self._s.scalar(select(func.count()).select_from(InvoiceModel).where(*where)) or 0
        )
        rows = await self._s.scalars(
            select(InvoiceModel)
            .where(*where)
            .order_by(InvoiceModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_inv(m) for m in rows], total

    async def set_status(self, invoice_id: int, status: InvoiceStatus) -> Invoice:
        m = await self._s.get(InvoiceModel, invoice_id)
        if m is None:
            raise NotFoundError("Invoice not found")
        m.status = status.value
        await self._s.flush()
        await self._s.refresh(m)
        return _inv(m)
