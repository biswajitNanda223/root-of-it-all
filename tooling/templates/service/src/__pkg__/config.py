from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from rio_core.config import CoreSettings


class ServiceSettings(CoreSettings):
    app_name: str = "__name__-service"
    database_url: str = Field(
        default="sqlite+aiosqlite:///./__name__.db",
        validation_alias=AliasChoices("__ENV___DATABASE_URL"),
    )


@lru_cache
def get_settings() -> ServiceSettings:
    return ServiceSettings()
