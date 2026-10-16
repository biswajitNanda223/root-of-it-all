"""HTTP DTOs, kept separate from domain entities."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserRead(ORMModel):
    id: int
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class ItemRead(ORMModel):
    id: int
    owner_id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class Problem(BaseModel):
    """RFC 7807-style error body."""

    type: str
    title: str
    status: int
    detail: str
    request_id: str | None = None


class FileInfo(BaseModel):
    filename: str | None
    content_type: str | None
    size: int
    sha256: str
