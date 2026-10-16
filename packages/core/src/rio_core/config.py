"""Typed, environment-driven settings (12-factor)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]
_INSECURE_DEFAULT = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_prefix="RIO_"
    )

    app_name: str = "root-of-it-all"
    environment: Environment = "development"
    debug: bool = False
    docs_enabled: bool = True

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False

    database_url: str = "sqlite+aiosqlite:///./dev.db"
    db_echo: bool = False
    auto_create_tables: bool = False  # dev/test convenience; prod uses Alembic

    secret_key: SecretStr = SecretStr(_INSECURE_DEFAULT)
    access_token_expire_minutes: int = Field(default=30, ge=1)

    cors_origins: list[str] = Field(default_factory=list)
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])

    first_superuser_email: str | None = None
    first_superuser_password: SecretStr | None = None

    max_upload_bytes: int = 5 * 1024 * 1024

    # Playground: dummy end-to-end APIs that exercise the FastAPI feature set. Never in production.
    playground_enabled: bool = True
    playground_api_key: SecretStr = SecretStr("demo-key")
    public_url: str | None = None  # advertised in OpenAPI `servers` (set behind a proxy)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _guard_production(self) -> Settings:
        if self.environment in {"staging", "production"}:
            if self.secret_key.get_secret_value() == _INSECURE_DEFAULT:
                raise ValueError("RIO_SECRET_KEY must be set outside development/test")
            if self.debug:
                raise ValueError("RIO_DEBUG must be false in staging/production")
        if self.environment == "production" and self.playground_enabled:
            raise ValueError("RIO_PLAYGROUND_ENABLED must be false in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
