from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from rio_core.errors import AppError
from rio_core.logging import request_id_var

log = logging.getLogger(__name__)


def _problem(status: int, code: str, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        {
            "type": f"urn:problem:{code}",
            "title": title,
            "status": status,
            "detail": detail,
            "request_id": request_id_var.get(),
        },
        status_code=status,
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        resp = _problem(exc.status_code, exc.code, type(exc).__name__, exc.detail)
        if exc.status_code == 401:
            resp.headers["WWW-Authenticate"] = "Bearer"
        return resp

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", exc_info=exc)
        return _problem(500, "internal_error", "InternalServerError", "Unexpected error")
