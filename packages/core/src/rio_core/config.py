"""Typed, environment-driven settings (12-factor).

`CoreSettings` holds what every service shares; each app extends it with its own fields (and, for the database URL,
its own env var so several services can run side by side: `CATALOG_DATABASE_URL`, `ORDERS_DATABASE_URL`, ...).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]
_INSECURE_DEFAULT = "change-me-in-production"
_INSECURE_SERVICE_KEY = "dev-service-key"


class CoreSettings(BaseSettings):
    # Real configuration arrives via process env (injected by `dotenvx run`, see docs/secrets.md);
    # `.env.local` is read directly so IDE-launched processes work too.
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="RIO_",
        populate_by_name=True,
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

    # Shared by ALL services: tokens minted by the identity service must verify everywhere.
    secret_key: SecretStr = SecretStr(_INSECURE_DEFAULT)
    access_token_expire_minutes: int = Field(default=30, ge=1)
    # Service-to-service credential for /internal/* endpoints.
    service_key: SecretStr = SecretStr(_INSECURE_SERVICE_KEY)

    cors_origins: list[str] = Field(default_factory=list)
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])
    public_url: str | None = None  # advertised in OpenAPI `servers` (set behind a proxy)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _guard_production(self) -> CoreSettings:
        if self.environment in {"staging", "production"}:
            if self.secret_key.get_secret_value() == _INSECURE_DEFAULT:
                raise ValueError("RIO_SECRET_KEY must be set outside development/test")
            if self.service_key.get_secret_value() == _INSECURE_SERVICE_KEY:
                raise ValueError("RIO_SERVICE_KEY must be set outside development/test")
            if self.debug:
                raise ValueError("RIO_DEBUG must be false in staging/production")
        return self


class Settings(CoreSettings):
    """Settings of the identity/demo API (`apps/api`)."""

    first_superuser_email: str | None = None
    first_superuser_password: SecretStr | None = None

    max_upload_bytes: int = 5 * 1024 * 1024

    # Playground: dummy end-to-end APIs that exercise the FastAPI feature set. Never in production.
    playground_enabled: bool = True
    playground_api_key: SecretStr = SecretStr("demo-key")

    @model_validator(mode="after")
    def _guard_playground(self) -> Settings:
        if self.environment == "production" and self.playground_enabled:
            raise ValueError("RIO_PLAYGROUND_ENABLED must be false in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
