from fastapi.testclient import TestClient

from catalog_service.infrastructure.models import Base

C = "/api/v1/catalog"
SERVICE = {"X-Service-Key": "svc-key"}


def _product(client: TestClient, admin: dict[str, str], **kw: object) -> dict[str, object]:
    body = {"sku": "MUG-1", "name": "Mug", "price": "12.50", "stock": 5, **kw}
    r = client.post(f"{C}/products", json=body, headers=admin)
    assert r.status_code == 201, r.text
    return r.json()  # type: ignore[no-any-return]


def test_own_metadata_only_has_catalog_tables() -> None:
    assert set(Base.metadata.tables) == {"categories", "products", "reservations"}


def test_writes_need_admin_reads_are_public(client: TestClient, admin, user) -> None:  # type: ignore[no-untyped-def]
    body = {"sku": "A-1", "name": "A", "price": "1.00"}
    assert client.post(f"{C}/products", json=body).status_code == 401
    assert client.post(f"{C}/products", json=body, headers=user).status_code == 403
    assert client.post(f"{C}/products", json=body, headers=admin).status_code == 201
    assert client.get(f"{C}/products").json()["total"] == 1


def test_crud_search_and_categories(client: TestClient, admin) -> None:  # type: ignore[no-untyped-def]
    cat = client.post(f"{C}/categories", json={"name": "Kitchen Ware"}, headers=admin).json()
    assert cat["slug"] == "kitchen-ware"
    assert (
        client.post(f"{C}/categories", json={"name": "kitchen ware"}, headers=admin).status_code
        == 409
    )
    mug = _product(client, admin, category_id=cat["id"])
    _product(client, admin, sku="PEN-1", name="Pen", price="1.20", stock=0)
    assert _product(client, admin, sku="BAD-1", category_id=None)  # created
    assert (
        client.post(
            f"{C}/products",
            json={"sku": "X-1", "name": "x", "price": "1", "category_id": 99},
            headers=admin,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"{C}/products", json={"sku": "MUG-1", "name": "dup", "price": "1"}, headers=admin
        ).status_code
        == 409
    )
    assert client.get(f"{C}/products?q=pen").json()["total"] == 1
    assert (
        client.get(f"{C}/products?in_stock=true&sort=-price").json()["items"][0]["sku"] == "MUG-1"
    )
    assert client.get(f"{C}/products?category_id={cat['id']}").json()["total"] == 1
    assert client.get(f"{C}/products?min_price=2&max_price=20").json()["total"] == 2
    assert client.get(f"{C}/products?bogus=1").status_code == 422
    patched = client.patch(
        f"{C}/products/{mug['id']}", json={"price": "9.99"}, headers=admin
    ).json()
    assert patched["price"] == "9.99"
    assert client.delete(f"{C}/products/{mug['id']}", headers=admin).status_code == 204
    assert client.get(f"{C}/products/{mug['id']}").status_code == 404


def test_internal_requires_service_key(client: TestClient) -> None:
    body = {"reservation_id": "r1", "lines": [{"product_id": 1, "quantity": 1}]}
    assert client.post("/internal/stock/reserve", json=body).status_code == 401
    assert (
        client.post(
            "/internal/stock/reserve", json=body, headers={"X-Service-Key": "x"}
        ).status_code
        == 401
    )


def test_reserve_release_is_idempotent_and_atomic(client: TestClient, admin) -> None:  # type: ignore[no-untyped-def]
    mug = _product(client, admin)  # stock 5
    pen = _product(client, admin, sku="PEN-1", name="Pen", price="1.00", stock=1)
    body = {"reservation_id": "o-1", "lines": [{"product_id": mug["id"], "quantity": 2}]}
    first = client.post("/internal/stock/reserve", json=body, headers=SERVICE).json()
    assert first["lines"][0]["unit_price"] == "12.50"
    assert (
        client.post("/internal/stock/reserve", json=body, headers=SERVICE).json() == first
    )  # replay
    assert client.get(f"{C}/products/{mug['id']}").json()["stock"] == 3  # decremented once

    # all-or-nothing: second line is short -> first line must not be taken either
    bad = {
        "reservation_id": "o-2",
        "lines": [
            {"product_id": mug["id"], "quantity": 1},
            {"product_id": pen["id"], "quantity": 5},
        ],
    }
    assert client.post("/internal/stock/reserve", json=bad, headers=SERVICE).status_code == 409
    assert client.get(f"{C}/products/{mug['id']}").json()["stock"] == 3
    missing = {"reservation_id": "o-3", "lines": [{"product_id": 999, "quantity": 1}]}
    assert client.post("/internal/stock/reserve", json=missing, headers=SERVICE).status_code == 404

    rel = client.post("/internal/stock/release/o-1", headers=SERVICE).json()
    assert rel["status"] == "released"
    assert (
        client.post("/internal/stock/release/o-1", headers=SERVICE).status_code == 200
    )  # idempotent
    assert client.get(f"{C}/products/{mug['id']}").json()["stock"] == 5  # restored once
    assert client.post("/internal/stock/release/nope", headers=SERVICE).status_code == 404


def test_openapi_and_probes(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "Catalog service"
    assert "ServiceKey" in spec["components"]["securitySchemes"]
    assert client.get("/health/ready").json() == {"status": "ok"}
