from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from rio_db import TimestampMixin, new_metadata


class Base(DeclarativeBase):
    """This service's own metadata: isolated from every other service."""

    metadata = new_metadata()


class NoteModel(TimestampMixin, Base):
    """Example aggregate - replace with your domain."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200))
