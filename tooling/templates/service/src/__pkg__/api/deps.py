"""Composition root: wire adapters into use-cases here (and override them in tests)."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from __pkg__.infrastructure.repositories import SqlNoteRepository
from rio_auth import Principal, principal_dependency
from rio_web import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
current_principal = principal_dependency(
    os.environ.get("IDENTITY_TOKEN_URL", "http://localhost:8000/api/v1/auth/token")
)
PrincipalDep = Annotated[Principal, Depends(current_principal)]


def get_notes(session: SessionDep) -> SqlNoteRepository:
    return SqlNoteRepository(session)


NotesDep = Annotated[SqlNoteRepository, Depends(get_notes)]
