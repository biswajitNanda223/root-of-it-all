from fastapi import APIRouter
from fastapi.testclient import TestClient

from rio_core.config import CoreSettings
from rio_core.errors import NotFoundError
from rio_db import new_metadata
from rio_web import create_service_app, database_lifespan


def test_factory_wires_everything(tmp_path) -> None:  # type: ignore[no-untyped-def]
    router = APIRouter(tags=["demo"])

    @router.get("/boom")
    async def boom() -> None:
        raise NotFoundError("nope")

    s = CoreSettings(environment="test", database_url=f"sqlite+aiosqlite:///{tmp_path}/w.db")
    app = create_service_app(
        s,
        title="t",
        description="d",
        lifespan=database_lifespan(metadata=new_metadata()),
        routers=[router],
    )
    with TestClient(app) as c:
        assert c.get("/health/ready").json() == {"status": "ok"}
        r = c.get("/boom", headers={"x-request-id": "r1"})
        assert r.status_code == 404
        assert r.headers["content-type"] == "application/problem+json"
        assert r.headers["x-request-id"] == "r1"
        assert c.get("/openapi.json").json()["paths"]["/boom"]["get"]["operationId"] == "demo-boom"
