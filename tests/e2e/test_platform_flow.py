"""End-to-end across THREE services in one event loop: identity (api) -> catalog -> orders.

No sockets: each service is a real ASGI app with its own database; orders talks to catalog through the real
`HttpCatalogGateway` over an in-process ASGI transport (the DI seam `catalog_transport`).
"""

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.main import create_app as create_identity
from catalog_service.config import CatalogSettings
from catalog_service.main import create_app as create_catalog
from orders_service.config import OrdersSettings
from orders_service.main import create_app as create_orders
from rio_core.config import Settings

SECRET, SVC = "e" * 32, "e2e-service-key"
KEY = {"X-Service-Key": SVC}


@dataclass
class Platform:
    identity: httpx.AsyncClient
    catalog: httpx.AsyncClient
    orders: httpx.AsyncClient
    catalog_app: FastAPI


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://svc")


@pytest.fixture
async def platform(tmp_path: Path) -> AsyncIterator[Platform]:
    common = {
        "environment": "test",
        "auto_create_tables": True,
        "secret_key": SECRET,
        "service_key": SVC,
    }
    db = lambda name: f"sqlite+aiosqlite:///{tmp_path / name}.db"  # noqa: E731
    identity = create_identity(
        Settings(
            **common,
            database_url=db("identity"),
            playground_enabled=False,
            first_superuser_email="root@example.com",
            first_superuser_password="root-password",
        )
    )  # type: ignore[arg-type]
    catalog = create_catalog(CatalogSettings(**common, database_url=db("catalog")))  # type: ignore[arg-type]
    async with AsyncExitStack() as stack:
        for app in (identity, catalog):
            await stack.enter_async_context(app.router.lifespan_context(app))
        orders = create_orders(
            OrdersSettings(**common, database_url=db("orders")),  # type: ignore[arg-type]
            catalog_transport=httpx.ASGITransport(app=catalog),
        )
        await stack.enter_async_context(orders.router.lifespan_context(orders))
        clients = [_client(identity), _client(catalog), _client(orders)]
        for c in clients:
            stack.push_async_callback(c.aclose)
        yield Platform(clients[0], clients[1], clients[2], catalog)


async def _login(p: Platform, email: str, password: str) -> dict[str, str]:
    r = await p.identity.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _customer(p: Platform, email: str) -> dict[str, str]:
    r = await p.identity.post(
        "/api/v1/auth/register", json={"email": email, "password": "password123"}
    )
    assert r.status_code == 201
    return await _login(p, email, "password123")


async def _stock(p: Platform, pid: int) -> int:
    return (await p.catalog.get(f"/api/v1/catalog/products/{pid}")).json()["stock"]  # type: ignore[no-any-return]


async def test_full_purchase_lifecycle(platform: Platform) -> None:
    p = platform
    admin = await _login(p, "root@example.com", "root-password")
    alice, bob = await _customer(p, "alice@example.com"), await _customer(p, "bob@example.com")

    # catalog: admin-only writes, public reads
    prod = (
        await p.catalog.post(
            "/api/v1/catalog/products",
            headers=admin,
            json={"sku": "MUG-1", "name": "Mug", "price": "12.50", "stock": 3},
        )
    ).json()
    assert (
        await p.catalog.post(
            "/api/v1/catalog/products",
            headers=alice,
            json={"sku": "X-1", "name": "x", "price": "1"},
        )
    ).status_code == 403
    pid = prod["id"]

    # 1) order -> stock reserved, price comes from the catalog (not from the client)
    placed = await p.orders.post(
        "/api/v1/orders", headers=alice, json={"lines": [{"product_id": pid, "quantity": 2}]}
    )
    assert placed.status_code == 201, placed.text
    order = placed.json()
    assert order["total"] == "25.00"
    assert order["lines"][0]["unit_price"] == "12.50"
    assert await _stock(p, pid) == 1

    # 2) not enough stock left -> 409, nothing changes
    short = await p.orders.post(
        "/api/v1/orders", headers=bob, json={"lines": [{"product_id": pid, "quantity": 2}]}
    )
    assert short.status_code == 409
    assert await _stock(p, pid) == 1
    unknown = await p.orders.post(
        "/api/v1/orders", headers=bob, json={"lines": [{"product_id": 999, "quantity": 1}]}
    )
    assert unknown.status_code == 404

    # 3) isolation between customers; admins see everything
    assert (await p.orders.get(f"/api/v1/orders/{order['id']}", headers=bob)).status_code == 403
    assert (await p.orders.get(f"/api/v1/orders/{order['id']}", headers=admin)).status_code == 200
    assert (await p.orders.get("/api/v1/orders", headers=bob)).json()["total"] == 0
    assert (await p.orders.get("/api/v1/orders?status=pending", headers=alice)).json()["total"] == 1
    assert (await p.orders.get("/api/v1/orders")).status_code == 401

    # 4) cancel -> stock released upstream exactly once
    cancelled = await p.orders.post(f"/api/v1/orders/{order['id']}/cancel", headers=alice)
    assert cancelled.json()["status"] == "cancelled"
    assert await _stock(p, pid) == 3

    # 5) pay path + invalid transitions
    second = (
        await p.orders.post(
            "/api/v1/orders", headers=alice, json={"lines": [{"product_id": pid, "quantity": 1}]}
        )
    ).json()
    assert (await p.orders.post(f"/api/v1/orders/{second['id']}/pay", headers=alice)).json()[
        "status"
    ] == "paid"
    assert (
        await p.orders.post(f"/api/v1/orders/{second['id']}/cancel", headers=alice)
    ).status_code == 409
    assert await _stock(p, pid) == 2

    # 6) transactional outbox captured every state change, guarded by the service key
    assert (await p.orders.get("/internal/outbox")).status_code == 401
    events = (await p.orders.get("/internal/outbox", headers=KEY)).json()
    assert [e["topic"] for e in events] == [
        "order.created",
        "order.cancelled",
        "order.created",
        "order.paid",
    ]
    assert (
        await p.orders.post(f"/internal/outbox/{events[0]['id']}/ack", headers=KEY)
    ).status_code == 204
    assert len((await p.orders.get("/internal/outbox", headers=KEY)).json()) == 3


async def test_orders_degrade_gracefully_when_catalog_is_down(tmp_path: Path) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("catalog is down", request=request)

    settings = OrdersSettings(
        environment="test",
        auto_create_tables=True,
        secret_key=SECRET,  # type: ignore[arg-type]
        service_key=SVC,
        database_url=f"sqlite+aiosqlite:///{tmp_path}/o.db",
    )  # type: ignore[arg-type]
    app = create_orders(settings, catalog_transport=httpx.MockTransport(refuse))
    from rio_auth import JwtTokens

    token = {"Authorization": f"Bearer {JwtTokens(SECRET).issue('7')}"}
    async with app.router.lifespan_context(app), _client(app) as c:
        r = await c.post(
            "/api/v1/orders", headers=token, json={"lines": [{"product_id": 1, "quantity": 1}]}
        )
        assert r.status_code == 502
        assert r.json()["type"] == "urn:problem:upstream_error"
        assert (
            await c.get("/health/ready")
        ).status_code == 200  # we are up even though the dependency is not


async def test_each_service_only_creates_its_own_tables(platform: Platform) -> None:
    from app.infrastructure.models import Base as IdentityBase
    from catalog_service.infrastructure.models import Base as CatalogBase
    from orders_service.infrastructure.models import Base as OrdersBase

    tables = [set(b.metadata.tables) for b in (IdentityBase, CatalogBase, OrdersBase)]
    assert tables[0].isdisjoint(tables[1])
    assert tables[1].isdisjoint(tables[2])
    assert tables[0].isdisjoint(tables[2])
