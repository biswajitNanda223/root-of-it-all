from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from rio_db import TimestampMixin, new_metadata


class Base(DeclarativeBase):
    """Orders' own metadata: isolated from every other service."""

    metadata = new_metadata()


class OrderModel(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    reservation_id: Mapped[str] = mapped_column(String(100), unique=True)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    lines: Mapped[list[OrderLineModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="OrderLineModel.id"
    )


class OrderLineModel(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(Integer)
    sku: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(200))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer)


class OutboxModel(Base):
    """Transactional outbox: written in the same transaction as the state change, relayed later."""

    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
