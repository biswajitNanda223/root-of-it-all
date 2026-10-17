from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from rio_core.config import CoreSettings


class ServiceSettings(CoreSettings):
    app_name: str = "billing-service"
    database_url: str = Field(
        default="sqlite+aiosqlite:///./billing.db",
        validation_alias=AliasChoices("BILLING_DATABASE_URL"),
    )


@lru_cache
def get_settings() -> ServiceSettings:
    return ServiceSettings()
