"""Composition root: the one place that knows which adapter backs which port."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from billing_service.infrastructure.repositories import SqlInvoiceRepository
from billing_service.services.invoices import InvoiceService
from rio_auth import Principal, principal_dependency
from rio_core.errors import ForbiddenError
from rio_web import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
current_principal = principal_dependency(
    os.environ.get("IDENTITY_TOKEN_URL", "http://localhost:8000/api/v1/auth/token")
)
PrincipalDep = Annotated[Principal, Depends(current_principal)]


async def require_admin(who: PrincipalDep) -> Principal:
    if not who.is_superuser:
        raise ForbiddenError("Administrator token required")
    return who


AdminDep = Annotated[Principal, Depends(require_admin)]


def get_invoice_service(session: SessionDep) -> InvoiceService:
    return InvoiceService(SqlInvoiceRepository(session))


InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]
