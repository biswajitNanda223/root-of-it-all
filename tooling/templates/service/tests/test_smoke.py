from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    assert client.get("/health/ready").json() == {"status": "ok"}


def test_notes_need_a_token_and_are_private(client: TestClient, auth: dict[str, str]) -> None:
    assert client.post("/api/v1/notes", json={"title": "x"}).status_code == 401
    assert client.post("/api/v1/notes", json={"title": "x"}, headers=auth).status_code == 201
    assert [n["title"] for n in client.get("/api/v1/notes", headers=auth).json()] == ["x"]
