"""Use cases: pure rules over the repository port (no FastAPI, no SQLAlchemy)."""

from __future__ import annotations

from decimal import Decimal

from billing_service.domain.entities import Invoice, InvoiceStatus
from billing_service.domain.ports import InvoiceRepository
from rio_auth import Principal
from rio_core.errors import ConflictError, ForbiddenError, NotFoundError

_ALLOWED = {
    InvoiceStatus.issued: {InvoiceStatus.paid, InvoiceStatus.void},
    InvoiceStatus.paid: set(),
    InvoiceStatus.void: set(),
}


class InvoiceService:
    def __init__(self, invoices: InvoiceRepository) -> None:
        self._invoices = invoices

    async def issue(self, *, order_id: int, customer_id: str, amount: Decimal) -> Invoice:
        if await self._invoices.get_by_order(order_id):  # one invoice per order
            raise ConflictError(f"order {order_id} already has an invoice")
        return await self._invoices.add(order_id=order_id, customer_id=customer_id, amount=amount)

    async def _visible(self, who: Principal, invoice_id: int) -> Invoice:
        invoice = await self._invoices.get(invoice_id)
        if invoice is None:
            raise NotFoundError("Invoice not found")
        if invoice.customer_id != who.subject and not who.is_superuser:
            raise ForbiddenError("Not your invoice")
        return invoice

    async def get(self, who: Principal, invoice_id: int) -> Invoice:
        return await self._visible(who, invoice_id)

    async def list(self, who: Principal, *, limit: int, offset: int) -> tuple[list[Invoice], int]:
        owner = None if who.is_superuser else who.subject
        return await self._invoices.list(customer_id=owner, limit=limit, offset=offset)

    async def _move(self, who: Principal, invoice_id: int, target: InvoiceStatus) -> Invoice:
        invoice = await self._visible(who, invoice_id)
        if target not in _ALLOWED[invoice.status]:
            raise ConflictError(
                f"cannot move an invoice from {invoice.status.value} to {target.value}"
            )
        return await self._invoices.set_status(invoice_id, target)

    async def pay(self, who: Principal, invoice_id: int) -> Invoice:
        return await self._move(who, invoice_id, InvoiceStatus.paid)

    async def void(self, who: Principal, invoice_id: int) -> Invoice:
        if not who.is_superuser:
            raise ForbiddenError("Only administrators can void invoices")
        return await self._move(who, invoice_id, InvoiceStatus.void)
