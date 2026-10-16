"""Response customisation: status codes, headers, cookies, media types, redirects, streaming."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    StreamingResponse,
)

from app.api.schemas import Problem

router = APIRouter(prefix="/responses", tags=["playground: responses"])


@router.post("/created", status_code=status.HTTP_201_CREATED, summary="Custom status code")
async def created() -> dict[str, str]:
    return {"created": "yes"}


@router.get("/accepted", status_code=status.HTTP_202_ACCEPTED, summary="202 Accepted")
async def accepted() -> dict[str, str]:
    return {"queued": "yes"}


@router.get(
    "/no-content",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="204: no body",
)
async def no_content() -> None:
    return None


@router.get("/headers-cookies", summary="Set headers + cookies via the injected `Response`")
async def headers_cookies(response: Response) -> dict[str, str]:
    response.headers["X-Demo"] = "hello"
    response.set_cookie("demo", "1", httponly=True, samesite="lax", max_age=60)
    response.status_code = status.HTTP_200_OK
    return {"ok": "true"}


@router.get("/json", summary="Return a `JSONResponse` directly (bypasses response_model)")
async def json_direct() -> JSONResponse:
    return JSONResponse({"direct": True}, headers={"X-Direct": "1"})


@router.get("/html", response_class=HTMLResponse, summary="HTML")
async def html() -> str:
    return "<h1>Hello from FastAPI</h1>"


@router.get("/text", response_class=PlainTextResponse, summary="Plain text")
async def text() -> str:
    return "plain text"


@router.get(
    "/xml",
    summary="Custom media type documented in OpenAPI",
    responses={
        200: {"content": {"application/xml": {"example": "<ok>true</ok>"}}, "description": "XML"}
    },
    response_class=Response,
)
async def xml() -> Response:
    return Response("<ok>true</ok>", media_type="application/xml")


@router.get("/redirect", response_class=RedirectResponse, status_code=307, summary="Redirect")
async def redirect(to: Annotated[str, Query(pattern=r"^/")] = "/docs") -> RedirectResponse:
    return RedirectResponse(to)


@router.get(
    "/status/{code}",
    summary="Document several responses",
    responses={
        200: {"description": "Healthy"},
        404: {"model": Problem, "description": "Not found"},
        418: {"model": Problem, "description": "I'm a teapot"},
    },
)
async def status_code(code: int) -> JSONResponse:
    return JSONResponse({"code": code}, status_code=code if code in {200, 404, 418} else 200)


def _csv_rows(n: int) -> Iterator[str]:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "square"])
    yield buf.getvalue()
    for i in range(1, n + 1):
        buf.seek(0)
        buf.truncate()
        writer.writerow([i, i * i])
        yield buf.getvalue()


@router.get("/csv", summary="Streaming CSV download", response_class=StreamingResponse)
async def csv_stream(rows: Annotated[int, Query(ge=1, le=10_000)] = 5) -> StreamingResponse:
    return StreamingResponse(
        _csv_rows(rows),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="squares.csv"'},
    )
