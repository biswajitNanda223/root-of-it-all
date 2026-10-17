import pytest
from pydantic import ValidationError

from rio_core.config import Settings


def test_defaults_are_development() -> None:
    assert Settings().environment == "development"


def test_production_requires_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production")


def test_production_ok_with_secret() -> None:
    s = Settings(
        environment="production",
        secret_key="x" * 32,
        service_key="y" * 16,
        playground_enabled=False,
    )  # type: ignore[arg-type]
    assert s.is_production


def test_production_forbids_playground() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", secret_key="x" * 32, service_key="y" * 16)  # type: ignore[arg-type]


def test_staging_requires_service_key() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="staging", secret_key="x" * 32)  # type: ignore[arg-type]
