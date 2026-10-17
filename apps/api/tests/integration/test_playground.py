from fastapi.testclient import TestClient

from app.playground.dependencies_demo import CLEANUPS

P = "/api/v1/playground"


# ------------------------------------------------------------------------------------ parameters
def test_path_query_header_cookie(client: TestClient) -> None:
    assert client.get(f"{P}/params/path/7").json() == {"item_id": 7}
    assert client.get(f"{P}/params/path/0").status_code == 422
    assert client.get(f"{P}/params/enum/resnet").json()["kind"] == "residual"
    assert client.get(f"{P}/params/enum/nope").status_code == 422
    assert client.get(f"{P}/params/files/a/b/c.txt").json() == {"file_path": "a/b/c.txt"}
    r = client.get(f"{P}/params/query?q=hello&item-query=x&tag=a&tag=b&limit=5")
    assert r.json()["tag"] == ["a", "b"]
    assert r.json()["item-query"] == "x"
    assert client.get(f"{P}/params/query?q=!!").status_code == 422
    r = client.get(f"{P}/params/header", headers={"x-token": "t1"}, cookies={"session_id": "s"})
    assert r.json()["x_token"] == ["t1"]
    assert r.json()["session_id"] == "s"


def test_parameter_models(client: TestClient) -> None:
    assert client.get(f"{P}/params/query-model?limit=3&tags=a&tags=b").json()["tags"] == ["a", "b"]
    bad = client.get(f"{P}/params/query-model?bogus=1")
    assert bad.status_code == 422
    assert bad.headers["content-type"] == "application/problem+json"
    assert bad.json()["errors"][0]["loc"][0] == "query"
    assert client.get(f"{P}/params/header-model", headers={"x-tracking": "a"}).json()[
        "x_tracking"
    ] == ["a"]


# ----------------------------------------------------------------------------------------- bodies
def test_bodies(client: TestClient) -> None:
    cust = {
        "name": "Ada",
        "emails": ["a@b.co"],
        "tags": ["x", "x"],
        "address": {"street": "s", "city": "c", "country": "GB"},
    }
    assert client.post(f"{P}/bodies/customer", json=cust).json()["tags"] == ["x"]
    cust["address"]["country"] = "GBR"  # type: ignore[index]
    assert client.post(f"{P}/bodies/customer", json=cust).status_code == 422
    body = {"customer": {"name": "A"}, "rect": {"width": 2, "height": 3}, "importance": 5}
    assert client.post(f"{P}/bodies/multiple", json=body).json()["area"] == 6
    assert (
        client.post(f"{P}/bodies/embed", json={"rect": {"width": 1, "height": 2}}).json()["area"]
        == 2
    )
    assert client.post(f"{P}/bodies/pet", json={"pet_type": "dog"}).json() == {
        "kind": "dog",
        "class": "Dog",
    }
    assert client.post(f"{P}/bodies/pet", json={"pet_type": "fish"}).status_code == 422
    assert (
        client.post(f"{P}/bodies/weights?names=a", json={"1": 1.5, "2": 2.5}).json()["total"] == 4
    )


def test_response_model_hides_password_and_put_vs_patch(client: TestClient) -> None:
    r = client.post(f"{P}/bodies/accounts", json={"username": "u", "password": "password1"})
    assert r.status_code == 201
    assert "password" not in r.json()
    client.put(f"{P}/bodies/prefs", json={"theme": "dark", "page_size": 50, "beta": True})
    assert client.patch(f"{P}/bodies/prefs", json={"page_size": 5}).json() == {
        "theme": "dark",
        "page_size": 5,
        "beta": True,
    }
    assert client.put(f"{P}/bodies/prefs", json={"theme": "light"}).json()["page_size"] == 20
    assert client.get(f"{P}/bodies/encode").json()["tags"] == ["a"]


# --------------------------------------------------------------------------------------- responses
def test_responses(client: TestClient) -> None:
    assert client.post(f"{P}/responses/created").status_code == 201
    assert client.get(f"{P}/responses/accepted").status_code == 202
    assert client.get(f"{P}/responses/no-content").content == b""
    r = client.get(f"{P}/responses/headers-cookies")
    assert r.headers["x-demo"] == "hello"
    assert "demo=1" in r.headers["set-cookie"]
    assert client.get(f"{P}/responses/html").headers["content-type"].startswith("text/html")
    assert client.get(f"{P}/responses/xml").headers["content-type"] == "application/xml"
    assert (
        client.get(f"{P}/responses/redirect?to=/health/live", follow_redirects=False).status_code
        == 307
    )
    assert (
        client.get(f"{P}/responses/redirect?to=http://evil", follow_redirects=False).status_code
        == 422
    )
    assert client.get(f"{P}/responses/status/418").status_code == 418
    csv_resp = client.get(f"{P}/responses/csv?rows=3")
    assert csv_resp.text.splitlines()[-1] == "3,9"
    assert "attachment" in csv_resp.headers["content-disposition"]


# ------------------------------------------------------------------------------------- forms/files
def test_forms_and_files(client: TestClient) -> None:
    assert (
        client.post(f"{P}/forms/login", data={"username": "u", "password": "pw"}).json()[
            "password_length"
        ]
        == "2"
    )
    assert (
        client.post(
            f"{P}/forms/contact", data={"name": "n", "email": "e", "message": "m"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"{P}/forms/contact", data={"name": "n", "email": "e", "message": "m", "x": "1"}
        ).status_code
        == 422
    )
    up = client.post(
        f"{P}/forms/upload", files={"file": ("a.txt", b"a")}, data={"description": "d"}
    ).json()
    assert up["fnv1a64"] == 0xAF63DC4C8601EC8C
    assert up["description"] == "d"
    assert client.post(f"{P}/forms/bytes", files={"file": ("b", b"")}).json()["size"] == 0
    multi = client.post(f"{P}/forms/multi", files=[("files", ("1", b"1")), ("files", ("2", b"2"))])
    assert multi.json()["filenames"] == ["1", "2"]


# ----------------------------------------------------------------------------------------- errors
def test_errors(client: TestClient) -> None:
    r = client.get(f"{P}/errors/http/403")
    assert r.status_code == 403
    assert r.headers["x-error"] == "demo"
    assert r.json()["type"] == "urn:problem:http_error"
    assert client.get(f"{P}/errors/app/missing").status_code == 404
    assert client.get(f"{P}/errors/app/conflict").status_code == 409
    assert client.get(f"{P}/errors/teapot").status_code == 418
    assert client.get("/nope").json()["status"] == 404


def test_unhandled_error_is_sanitised(client: TestClient) -> None:
    with TestClient(client.app, raise_server_exceptions=False) as c:
        r = c.get(f"{P}/errors/boom")
    assert r.status_code == 500
    assert "never leaks" not in r.text


# ------------------------------------------------------------------------------------ dependencies
def test_dependencies(client: TestClient) -> None:
    on = {"X-Demo": "on"}
    assert client.get(f"{P}/deps/class").status_code == 403  # router-level dependency
    assert client.get(f"{P}/deps/class?page=3&size=500", headers=on).json() == {
        "page": 3,
        "size": 50,
        "offset": 100,
    }
    assert client.get(f"{P}/deps/sub?q=%20hi", headers=on).json() == {
        "value": "hi!",
        "same": "True",
    }
    assert client.get(f"{P}/deps/param?size=5", headers=on).json() == {"size": 5}
    assert client.get(f"{P}/deps/param?size=6", headers=on).status_code == 403
    CLEANUPS.clear()
    assert client.get(f"{P}/deps/yield", headers=on).json()["id"] == "res-1"
    assert CLEANUPS == ["res-1"]


# ------------------------------------------------------------------------------------- security
def test_api_key_and_basic(client: TestClient) -> None:
    assert client.get(f"{P}/security/api-key").status_code == 401
    assert client.get(f"{P}/security/api-key", headers={"X-API-Key": "demo-key"}).status_code == 200
    assert client.get(f"{P}/security/basic", auth=("demo", "demo")).json()["user"] == "demo"
    assert client.get(f"{P}/security/basic", auth=("demo", "bad")).status_code == 401


def test_oauth2_scopes(client: TestClient) -> None:
    def token(scope: str) -> dict[str, str]:
        r = client.post(
            f"{P}/security/token", data={"username": "demo", "password": "demo", "scope": scope}
        )
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    reader = token("items:read")
    assert client.get(f"{P}/security/scoped/read", headers=reader).status_code == 200
    assert client.post(f"{P}/security/scoped/write", headers=reader).status_code == 403
    assert client.post(f"{P}/security/scoped/write", headers=token("admin")).status_code == 200
    assert client.get(f"{P}/security/scoped/read").status_code == 401
    assert (
        client.post(f"{P}/security/token", data={"username": "x", "password": "y"}).status_code
        == 401
    )


# ---------------------------------------------------------------------------------------- advanced
def test_advanced(client: TestClient) -> None:
    info = client.get(f"{P}/advanced/request-info", headers={"X-Request-ID": "rid-1"})
    assert info.json()["request_id"] == "rid-1"
    assert "x-route-time-ms" in info.headers
    assert client.get(f"{P}/advanced/hidden").status_code == 200
    assert f"{P}/advanced/hidden" not in client.get("/openapi.json").json()["paths"]
    assert (
        client.get("/openapi.json").json()["paths"][f"{P}/advanced/deprecated"]["get"]["deprecated"]
        is True
    )
    assert client.post(f"{P}/advanced/background?message=hi").status_code == 202
    assert "hi" in client.get(f"{P}/advanced/background").json()
    assert "Hello, Bob!" in client.get(f"{P}/advanced/page?name=Bob").text
    assert client.get("/static/demo.css").status_code == 200
    assert client.get("/subapi/ping").json() == {"pong": "sub-app"}
    assert client.get("/subapi/openapi.json").json()["info"]["title"] == "Mounted sub-application"


def test_websocket_room(client: TestClient) -> None:
    with (
        client.websocket_connect(f"{P}/advanced/ws/chat/r1?name=ann") as a,
        client.websocket_connect(f"{P}/advanced/ws/chat/r1?name=bob") as b,
    ):
        assert a.receive_text() == "* ann joined r1"
        assert a.receive_text() == "* bob joined r1"
        assert b.receive_text() == "* bob joined r1"
        a.send_text("hello")
        assert b.receive_text() == "ann: hello"


# ------------------------------------------------------------------------- shop (end-to-end flow)
def test_shop_end_to_end(client: TestClient) -> None:
    shop = f"{P}/shop"
    client.post(f"{shop}/_reset")
    mug = client.post(
        f"{shop}/products", json={"sku": "MUG-1", "name": "Mug", "price": "12.50", "stock": 5}
    ).json()
    pen = client.post(
        f"{shop}/products", json={"sku": "PEN-1", "name": "Pen", "price": "1.20", "stock": 1}
    ).json()
    assert (
        client.post(
            f"{shop}/products", json={"sku": "MUG-1", "name": "dup", "price": "1"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"{shop}/products", json={"sku": "bad sku", "name": "x", "price": "1"}
        ).status_code
        == 422
    )

    listing = client.get(f"{shop}/products?sort=-price&in_stock=true&min_price=1").json()
    assert [p["sku"] for p in listing["items"]] == ["MUG-1", "PEN-1"]
    assert client.get(f"{shop}/products?q=pen").json()["total"] == 1
    assert client.patch(f"{shop}/products/{pen['id']}", json={"stock": 3}).json()["stock"] == 3

    order_body = {
        "lines": [
            {"product_id": mug["id"], "quantity": 2},
            {"product_id": pen["id"], "quantity": 1},
        ]
    }
    created = client.post(f"{shop}/orders", json=order_body, headers={"Idempotency-Key": "k1"})
    assert created.status_code == 201
    order = created.json()
    assert order["total"] == "26.20"
    replay = client.post(f"{shop}/orders", json=order_body, headers={"Idempotency-Key": "k1"})
    assert replay.status_code == 200
    assert replay.headers["idempotent-replayed"] == "true"
    assert replay.json()["id"] == order["id"]
    assert (
        client.get(f"{shop}/products/{mug['id']}").json()["stock"] == 3
    )  # reserved once, not twice

    too_many = {"lines": [{"product_id": mug["id"], "quantity": 99}]}
    assert client.post(f"{shop}/orders", json=too_many).status_code == 409
    assert (
        client.post(
            f"{shop}/orders", json={"lines": [{"product_id": 999, "quantity": 1}]}
        ).status_code
        == 404
    )

    paid = client.post(f"{shop}/orders/{order['id']}/pay").json()
    assert paid["status"] == "paid"
    assert client.post(f"{shop}/orders/{order['id']}/pay").status_code == 409
    assert client.post(f"{shop}/orders/{order['id']}/cancel").status_code == 409

    second = client.post(
        f"{shop}/orders", json={"lines": [{"product_id": mug["id"], "quantity": 1}]}
    ).json()
    assert client.post(f"{shop}/orders/{second['id']}/cancel").json()["status"] == "cancelled"
    assert client.get(f"{shop}/products/{mug['id']}").json()["stock"] == 3  # restocked

    assert client.get(f"{shop}/orders?status=paid").json()["total"] == 1
    events = client.get(f"{shop}/orders/{order['id']}/events").text
    assert "event: pending" in events
    assert "event: paid" in events
    assert client.get(f"{shop}/orders/export.csv").text.splitlines()[0] == "id,status,total,lines"
    assert client.delete(f"{shop}/products/{pen['id']}").status_code == 204
    assert client.get(f"{shop}/products/{pen['id']}").status_code == 404


# ---------------------------------------------------------------------------------------- OpenAPI
def test_openapi_documents_everything(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    assert "order-paid" in spec["webhooks"]
    create = spec["paths"][f"{P}/shop/orders"]["post"]
    assert create["callbacks"]
    assert create["operationId"] == "playground_shop_end_to_end-create_order"
    schemes = spec["components"]["securitySchemes"]
    assert {
        "PlaygroundApiKey",
        "PlaygroundBasic",
        "PlaygroundScopes",
        "OAuth2PasswordBearer",
    } <= set(schemes)
    assert spec["info"]["contact"]["name"] == "Platform team"
    ids = [op["operationId"] for path in spec["paths"].values() for op in path.values()]
    assert len(ids) == len(set(ids))
    tags = {t["name"] for t in spec["tags"]}
    assert "playground: parameters" in tags
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_playground_can_be_disabled(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.main import create_app
    from rio_core.config import Settings

    s = Settings(
        environment="test",
        playground_enabled=False,
        database_url=f"sqlite+aiosqlite:///{tmp_path}/x.db",
        auto_create_tables=True,
    )
    with TestClient(create_app(s)) as c:
        assert c.get(f"{P}/params/path/1").status_code == 404
        assert not any("playground" in p for p in c.get("/openapi.json").json()["paths"])
