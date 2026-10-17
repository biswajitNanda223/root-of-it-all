"""Relay-facing outbox API (a message relay polls this; real brokers would replace it)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from orders_service.api.deps import SessionDep
from orders_service.api.schemas import OutboxOut
from orders_service.infrastructure.repositories import SqlOutboxRepository
from rio_auth import require_service_key

router = APIRouter(
    prefix="/internal/outbox", tags=["internal"], dependencies=[Depends(require_service_key)]
)


@router.get("", response_model=list[OutboxOut], summary="Unpublished domain events")
async def pending(
    session: SessionDep, limit: Annotated[int, Query(ge=1, le=500)] = 100
) -> list[OutboxOut]:
    events = await SqlOutboxRepository(session).pending(limit)
    return [
        OutboxOut(id=e.id, topic=e.topic, payload=e.payload, created_at=e.created_at)
        for e in events
    ]


@router.post(
    "/{event_id}/ack", status_code=status.HTTP_204_NO_CONTENT, summary="Mark an event as published"
)
async def ack(event_id: int, session: SessionDep) -> Response:
    await SqlOutboxRepository(session).mark_published(event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
