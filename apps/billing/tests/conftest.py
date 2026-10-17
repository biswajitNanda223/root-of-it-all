from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from billing_service.config import ServiceSettings
from billing_service.main import create_app
from rio_auth import JwtTokens

SECRET = "t" * 32


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = ServiceSettings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'db.sqlite'}",
        auto_create_tables=True,
        secret_key=SECRET,  # type: ignore[arg-type]
    )
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {JwtTokens(SECRET).issue('42')}"}
