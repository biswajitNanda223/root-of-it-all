"""HTTP DTOs, kept separate from domain entities."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"email": "ada@example.com", "password": "correct-horse", "full_name": "Ada"}
            ]
        }
    )
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
    """RFC 7807-style error body (`application/problem+json`)."""

    type: str = Field(examples=["urn:problem:not_found"])
    title: str = Field(examples=["NotFoundError"])
    status: int = Field(examples=[404])
    detail: str = Field(examples=["Item not found"])
    request_id: str | None = Field(default=None, examples=["9f1c2b7e0f3a4c5d"])
    errors: list[dict[str, object]] | None = Field(
        default=None, description="Field-level details; present on 422 only."
    )


class FileInfo(BaseModel):
    filename: str | None
    content_type: str | None
    size: int
    sha256: str
    fnv1a64: int = Field(description="64-bit FNV-1a (rio-native C extension, lld-linked)")
