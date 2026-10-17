"""Playground wiring: one `register(app)` call mounts everything (and nothing else knows about it)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.playground import advanced, bodies, forms, params, responses, security_demo, shop
from app.playground import dependencies_demo as deps_demo
from app.playground import errors_demo as errors_demo
from app.playground.errors_demo import TeapotError
from app.playground.models import OrderPaidEvent
from app.playground.subapp import create_sub_app

TAGS = [
    {
        "name": "playground: parameters",
        "description": "Path, query, header, cookie params and parameter models.",
    },
    {
        "name": "playground: bodies",
        "description": "Nested/multiple/embedded bodies, unions, PUT vs PATCH.",
    },
    {
        "name": "playground: responses",
        "description": "Status codes, headers, cookies, media types, streaming.",
    },
    {"name": "playground: forms & files", "description": "Form data and uploads."},
    {"name": "playground: errors", "description": "HTTPException, domain errors, custom handlers."},
    {
        "name": "playground: dependencies",
        "description": "Class/sub/yield/parametrised dependencies.",
    },
    {"name": "playground: security", "description": "API key, HTTP Basic, OAuth2 scopes."},
    {
        "name": "playground: advanced",
        "description": "Request object, route classes, WebSocket rooms, templates.",
    },
    {
        "name": "playground: shop (end-to-end)",
        "description": "Products -> orders -> pay/cancel -> events. Documents callbacks & webhooks.",
    },
]

router = APIRouter(prefix="/api/v1/playground")
for module in (
    params,
    bodies,
    responses,
    forms,
    errors_demo,
    deps_demo,
    security_demo,
    advanced,
    shop,
):
    router.include_router(module.router)


def register(app: FastAPI) -> None:
    app.state.shop = shop.ShopStore()
    app.include_router(router)

    @app.exception_handler(TeapotError)
    async def _teapot(_: Request, exc: TeapotError) -> JSONResponse:
        return JSONResponse(status_code=418, content={"detail": f"I'm a teapot brewing {exc.brew}"})

    # OpenAPI `webhooks`: requests *we* send to subscribers (documentation only).
    @app.webhooks.post("order-paid", summary="Order paid")
    def order_paid(body: OrderPaidEvent) -> None:  # pragma: no cover - documentation only
        """Sent to every subscriber when an order moves to `paid`."""

    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).resolve().parent.parent / "static"),
        name="static",
    )
    app.mount("/subapi", create_sub_app())
