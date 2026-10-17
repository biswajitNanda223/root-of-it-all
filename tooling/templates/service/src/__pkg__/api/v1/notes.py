from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from __pkg__.api.deps import NotesDep, PrincipalDep

router = APIRouter(prefix="/api/v1/notes", tags=["notes"])


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(body: NoteIn, who: PrincipalDep, notes: NotesDep) -> NoteOut:
    return NoteOut.model_validate(await notes.add(who.subject, body.title))


@router.get("", response_model=list[NoteOut])
async def list_notes(who: PrincipalDep, notes: NotesDep) -> list[NoteOut]:
    return [NoteOut.model_validate(n) for n in await notes.list_for(who.subject)]
