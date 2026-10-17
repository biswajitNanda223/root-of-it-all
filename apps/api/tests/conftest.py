from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from rio_core.config import Settings


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        auto_create_tables=True,
        secret_key="t" * 32,  # type: ignore[arg-type]
        first_superuser_email="admin@example.com",
        first_superuser_password="adminpassword",  # type: ignore[arg-type]
        max_upload_bytes=1024,
    )
    with TestClient(create_app(settings)) as c:
        yield c


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/token", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _register_and_login(client: TestClient, email: str = "a@example.com") -> dict[str, str]:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    return _login(client, email, "password123")


@pytest.fixture
def login() -> Callable[[TestClient, str, str], dict[str, str]]:
    return _login


@pytest.fixture
def register_and_login() -> Callable[..., dict[str, str]]:
    return _register_and_login
