from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from catalog_service.config import CatalogSettings
from catalog_service.main import create_app
from rio_auth import JwtTokens

SECRET = "t" * 32


@pytest.fixture
def settings(tmp_path: Path) -> CatalogSettings:
    return CatalogSettings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'catalog.db'}",
        auto_create_tables=True,
        secret_key=SECRET,  # type: ignore[arg-type]
        service_key="svc-key",  # type: ignore[arg-type]
    )


@pytest.fixture
def client(settings: CatalogSettings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def admin() -> dict[str, str]:
    return {"Authorization": f"Bearer {JwtTokens(SECRET).issue('1', {'adm': True})}"}


@pytest.fixture
def user() -> dict[str, str]:
    return {"Authorization": f"Bearer {JwtTokens(SECRET).issue('2')}"}
