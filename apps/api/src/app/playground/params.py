"""Path / query / header / cookie parameters, validation, and parameter models."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Cookie, Header, Path, Query

from app.playground.models import CommonHeaders, QueryFilters

router = APIRouter(prefix="/params", tags=["playground: parameters"])


class ModelName(StrEnum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@router.get("/path/{item_id}", summary="Validated path parameter")
async def path_param(
    item_id: Annotated[int, Path(title="Item id", ge=1, le=1_000_000, examples=[42])],
) -> dict[str, int]:
    return {"item_id": item_id}


@router.get("/enum/{model_name}", summary="Enum path parameter (renders as a dropdown in Swagger)")
async def enum_param(model_name: ModelName) -> dict[str, str]:
    return {
        "model": model_name.value,
        "kind": "cnn" if model_name is not ModelName.resnet else "residual",
    }


@router.get("/files/{file_path:path}", summary="Path convertor: the value may contain slashes")
async def file_path(file_path: str) -> dict[str, str]:
    return {"file_path": file_path}


@router.get("/query", summary="Query parameters: defaults, constraints, aliases, lists")
async def query_params(
    q: Annotated[
        str | None,
        Query(min_length=3, max_length=50, pattern=r"^[\w ]+$", description="Search text"),
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    item_query: Annotated[
        str | None, Query(alias="item-query", description="Alias with a dash")
    ] = None,
    tag: Annotated[list[str] | None, Query(description="Repeat: ?tag=a&tag=b")] = None,
    old: Annotated[str | None, Query(deprecated=True, description="Deprecated, ignored")] = None,
    hidden: Annotated[str | None, Query(include_in_schema=False)] = None,
) -> dict[str, object]:
    return {
        "q": q,
        "skip": skip,
        "limit": limit,
        "item-query": item_query,
        "tag": tag or [],
        "old": old,
        "hidden": hidden,
    }


@router.get("/query-model", summary="Query parameter *model* (extra params -> 422)")
async def query_model(filters: Annotated[QueryFilters, Query()]) -> QueryFilters:
    return filters


@router.get("/header", summary="Header + cookie parameters")
async def header_cookie(
    user_agent: Annotated[str | None, Header()] = None,  # underscores -> User-Agent
    x_token: Annotated[list[str] | None, Header()] = None,  # repeated header -> list
    session_id: Annotated[str | None, Cookie()] = None,
) -> dict[str, object]:
    return {"user_agent": user_agent, "x_token": x_token or [], "session_id": session_id}


@router.get("/header-model", summary="Header parameter *model*")
async def header_model(headers: Annotated[CommonHeaders, Header()]) -> CommonHeaders:
    return headers
