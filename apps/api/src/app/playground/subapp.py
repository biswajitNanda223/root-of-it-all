"""A mounted sub-application: independent OpenAPI schema and docs at /subapi/docs."""

from __future__ import annotations

from fastapi import FastAPI


def create_sub_app() -> FastAPI:
    sub = FastAPI(
        title="Mounted sub-application", version="1.0.0", description="Own docs, own OpenAPI."
    )

    @sub.get("/ping", summary="Ping the sub-app")
    async def ping() -> dict[str, str]:
        return {"pong": "sub-app"}

    return sub
