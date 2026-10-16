from fastapi import APIRouter, Response, status

from app.api.deps import DbDep

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness probe")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe (checks the database)")
async def ready(db: DbDep, response: Response) -> dict[str, str]:
    try:
        await db.ping()
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}
