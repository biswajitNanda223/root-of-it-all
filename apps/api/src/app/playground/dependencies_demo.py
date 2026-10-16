"""Dependency injection patterns: classes, sub-dependencies, yield, parametrised, router-level."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request

from rio_core.errors import ForbiddenError

CLEANUPS: list[str] = []  # observable by tests


async def require_demo_header(x_demo: Annotated[str | None, Header()] = None) -> None:
    """Router-level dependency: runs for every route in this router and shows up in Swagger."""
    if x_demo != "on":
        raise ForbiddenError("send header X-Demo: on")


router = APIRouter(
    prefix="/deps", tags=["playground: dependencies"], dependencies=[Depends(require_demo_header)]
)


class Pagination:
    """Class dependency; the instance is built from query params."""

    def __init__(self, page: int = 1, size: int = 10) -> None:
        self.page, self.size = max(page, 1), min(max(size, 1), 50)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class MaxSize:
    """Parametrised dependency: callable instance."""

    def __init__(self, maximum: int) -> None:
        self.maximum = maximum

    def __call__(self, size: int = 1) -> int:
        if size > self.maximum:
            raise ForbiddenError(f"size must be <= {self.maximum}")
        return size


def query_dep(q: str = "") -> str:
    return q.strip()


def sub_dep(q: Annotated[str, Depends(query_dep)], suffix: str = "!") -> str:
    """Sub-dependency: depends on another dependency."""
    return f"{q}{suffix}" if q else ""


async def resource(request: Request) -> AsyncIterator[dict[str, str]]:
    """`yield` dependency: code after yield is cleanup, runs after the response is sent."""
    res = {"id": "res-1", "path": request.url.path}
    try:
        yield res
    finally:
        CLEANUPS.append(res["id"])


@router.get("/class", summary="Class dependency")
async def class_dep(p: Annotated[Pagination, Depends()]) -> dict[str, int]:
    return {"page": p.page, "size": p.size, "offset": p.offset}


@router.get("/sub", summary="Sub-dependencies (cached per request)")
async def sub(
    value: Annotated[str, Depends(sub_dep)], again: Annotated[str, Depends(sub_dep)]
) -> dict[str, str]:
    return {"value": value, "same": str(value == again)}


@router.get("/param", summary="Parametrised dependency")
async def param(size: Annotated[int, Depends(MaxSize(5))]) -> dict[str, int]:
    return {"size": size}


@router.get("/yield", summary="Dependency with `yield` (setup/teardown)")
async def with_yield(res: Annotated[dict[str, str], Depends(resource)]) -> dict[str, str]:
    return res


@router.get("/cleanups", summary="What the yield-dependency cleaned up so far")
async def cleanups() -> list[str]:
    return CLEANUPS
