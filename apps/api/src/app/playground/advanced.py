"""Advanced features: Request object, custom route class, deprecation, hidden routes, background tasks,
WebSocket rooms, templates."""

from __future__ import annotations

import time
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from fastapi.templating import Jinja2Templates

TEMPLATES = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


class TimedRoute(APIRoute):
    """Custom `APIRoute`: wraps every handler of the router that uses it."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            start = time.perf_counter()
            response = await original(request)
            response.headers["X-Route-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.3f}"
            return response

        return handler


router = APIRouter(prefix="/advanced", tags=["playground: advanced"], route_class=TimedRoute)
BACKGROUND_LOG: list[str] = []


@router.get("/request-info", summary="Use the raw `Request`, `app.state` and `request.state`")
async def request_info(request: Request) -> dict[str, object]:
    return {
        "method": request.method,
        "path": request.url.path,
        "client": request.client.host if request.client else None,
        "request_id": request.state.request_id,
        "environment": request.app.state.settings.environment,
        "accept": request.headers.get("accept"),
    }


@router.get("/deprecated", deprecated=True, summary="Marked deprecated in OpenAPI")
async def deprecated() -> dict[str, str]:
    return {"use": "/advanced/request-info"}


@router.get("/hidden", include_in_schema=False)
async def hidden() -> dict[str, str]:
    return {"hidden": "not in /docs"}


@router.get("/named", operation_id="playground_custom_operation_id", summary="Explicit operationId")
async def named() -> dict[str, str]:
    return {"operationId": "playground_custom_operation_id"}


def _record(message: str) -> None:
    BACKGROUND_LOG.append(message)


@router.post(
    "/background", status_code=status.HTTP_202_ACCEPTED, summary="Run work after the response"
)
async def background(message: str, tasks: BackgroundTasks) -> dict[str, str]:
    tasks.add_task(_record, message)
    return {"accepted": message}


@router.get("/background", summary="Messages processed by background tasks")
async def background_log() -> list[str]:
    return BACKGROUND_LOG


@router.get("/page", response_class=HTMLResponse, summary="Jinja2 template")
async def page(request: Request, name: str = "world") -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "hello.html", {"name": name})


class RoomManager:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = {}

    async def join(self, room: str, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms.setdefault(room, set()).add(ws)

    def leave(self, room: str, ws: WebSocket) -> None:
        self.rooms.get(room, set()).discard(ws)

    async def broadcast(self, room: str, message: str) -> None:
        for peer in list(self.rooms.get(room, ())):
            await peer.send_text(message)


manager = RoomManager()


async def ws_user(
    ws: WebSocket, name: Annotated[str, Query(min_length=1, max_length=20)] = "anon"
) -> str:
    """Dependencies work on WebSockets too."""
    return name


@router.websocket("/ws/chat/{room}")
async def chat(ws: WebSocket, room: str, name: Annotated[str, Depends(ws_user)]) -> None:
    await manager.join(room, ws)
    await manager.broadcast(room, f"* {name} joined {room}")
    try:
        while True:
            await manager.broadcast(room, f"{name}: {await ws.receive_text()}")
    except WebSocketDisconnect:
        manager.leave(room, ws)
        await manager.broadcast(room, f"* {name} left")
