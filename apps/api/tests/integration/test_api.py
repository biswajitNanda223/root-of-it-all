from fastapi.testclient import TestClient

from tests.conftest import login, register_and_login


def test_health(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ok"}


def test_request_context_headers(client: TestClient) -> None:
    r = client.get("/health/live", headers={"X-Request-ID": "abc"})
    assert r.headers["x-request-id"] == "abc"
    assert r.headers["x-content-type-options"] == "nosniff"


def test_auth_flow_and_problem_json(client: TestClient) -> None:
    h = register_and_login(client)
    assert client.get("/api/v1/users/me", headers=h).json()["email"] == "a@example.com"
    dup = client.post(
        "/api/v1/auth/register", json={"email": "a@example.com", "password": "password123"}
    )
    assert dup.status_code == 409
    assert dup.headers["content-type"] == "application/problem+json"
    assert client.get("/api/v1/users/me").status_code == 401


def test_items_crud_and_ownership(client: TestClient) -> None:
    alice, bob = (
        register_and_login(client, "alice@example.com"),
        register_and_login(client, "bob@example.com"),
    )
    created = client.post("/api/v1/items", json={"title": "t"}, headers=alice)
    assert created.status_code == 201
    iid = created.json()["id"]
    assert client.get(f"/api/v1/items/{iid}", headers=bob).status_code == 403
    assert (
        client.patch(f"/api/v1/items/{iid}", json={"title": "u"}, headers=alice).json()["title"]
        == "u"
    )
    page = client.get("/api/v1/items?limit=1", headers=alice).json()
    assert page["total"] == 1
    assert len(page["items"]) == 1
    assert client.delete(f"/api/v1/items/{iid}", headers=alice).status_code == 204
    assert client.get(f"/api/v1/items/{iid}", headers=alice).status_code == 404
    assert client.get("/api/v1/items/0", headers=alice).status_code == 422


def test_superuser_listing(client: TestClient) -> None:
    user = register_and_login(client)
    assert client.get("/api/v1/users", headers=user).status_code == 403
    admin = login(client, "admin@example.com", "adminpassword")
    assert client.get("/api/v1/users", headers=admin).json()["total"] == 2


def test_upload_limit(client: TestClient) -> None:
    h = register_and_login(client)
    ok = client.post("/api/v1/files", files={"file": ("a.txt", b"hello")}, headers=h)
    assert ok.json()["size"] == 5
    big = client.post("/api/v1/files", files={"file": ("b.bin", b"x" * 2000)}, headers=h)
    assert big.status_code == 413


def test_sse_and_websocket(client: TestClient) -> None:
    with client.stream("GET", "/api/v1/stream/ticks?count=3&interval=0") as r:
        r.read()
        assert r.text.count("event: tick") == 3
    with client.websocket_connect("/api/v1/ws/echo") as ws:
        ws.send_text("hi")
        assert ws.receive_text() == "hi"


def test_openapi_available(client: TestClient) -> None:
    assert "/api/v1/items" in client.get("/openapi.json").json()["paths"]
