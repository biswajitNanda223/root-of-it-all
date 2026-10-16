"""Framework-free domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class User:
    id: int
    email: str
    hashed_password: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Item:
    id: int
    owner_id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
