"""Raising and handling errors."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from rio_core.errors import ConflictError, NotFoundError

router = APIRouter(prefix="/errors", tags=["playground: errors"])


class TeapotError(Exception):
    """Custom exception with its own handler (registered in playground.router.register)."""

    def __init__(self, brew: str) -> None:
        self.brew = brew


@router.get("/http/{code}", summary="HTTPException with custom headers")
async def http_error(code: int) -> None:
    raise HTTPException(
        status_code=code if 400 <= code < 600 else 400,
        detail=f"demo {code}",
        headers={"X-Error": "demo"},
    )


@router.get("/app/{kind}", summary="Domain errors (AppError) -> problem+json")
async def app_error(kind: str) -> None:
    if kind == "missing":
        raise NotFoundError("no such thing")
    if kind == "conflict":
        raise ConflictError("already exists")
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "unknown kind; try missing|conflict")


@router.get("/teapot", summary="Custom exception + handler (418)")
async def teapot() -> None:
    raise TeapotError("earl grey")


@router.get("/boom", summary="Unhandled exception -> sanitized 500")
async def boom() -> None:
    raise RuntimeError("never leaks to the client")
