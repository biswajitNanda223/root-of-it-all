import pytest
from pydantic import ValidationError

from rio_core.config import Settings


def test_defaults_are_development() -> None:
    assert Settings().environment == "development"


def test_production_requires_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production")


def test_production_ok_with_secret() -> None:
    s = Settings(environment="production", secret_key="x" * 32)  # type: ignore[arg-type]
    assert s.is_production
