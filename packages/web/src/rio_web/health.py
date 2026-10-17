from __future__ import annotations

from fastapi import APIRouter, Request, Response, status

from rio_web.deps import get_db


def health_router() -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live", summary="Liveness probe")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/ready", summary="Readiness probe (checks the database)")
    async def ready(request: Request, response: Response) -> dict[str, str]:
        try:
            await get_db(request).ping()
        except Exception:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "unavailable"}
        return {"status": "ok"}

    return router
