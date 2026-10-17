from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from rio_db import TimestampMixin, new_metadata


class Base(DeclarativeBase):
    """Billing's own metadata: isolated from every other service."""

    metadata = new_metadata()


class InvoiceModel(TimestampMixin, Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(20), index=True)
