"""Server-Sent Events and WebSockets."""

import asyncio
from collections.abc import AsyncIterator

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["realtime"])


async def _ticks(count: int, interval: float) -> AsyncIterator[str]:
    for i in range(count):
        yield f"event: tick\ndata: {i}\n\n"
        await asyncio.sleep(interval)


@router.get("/stream/ticks", response_class=StreamingResponse, summary="SSE demo")
async def stream_ticks(
    count: int = Query(default=5, ge=1, le=100), interval: float = Query(default=0.1, ge=0, le=5)
) -> StreamingResponse:
    return StreamingResponse(_ticks(count, interval), media_type="text/event-stream")


@router.websocket("/ws/echo")
async def ws_echo(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            await ws.send_text(await ws.receive_text())
    except WebSocketDisconnect:
        return
