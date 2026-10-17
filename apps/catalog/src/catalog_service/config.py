from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from rio_core.config import CoreSettings


class CatalogSettings(CoreSettings):
    app_name: str = "catalog-service"
    # Own database, own env var - several services can share a host/env without clobbering each other.
    database_url: str = Field(
        default="sqlite+aiosqlite:///./catalog.db",
        validation_alias=AliasChoices("CATALOG_DATABASE_URL"),
    )


@lru_cache
def get_settings() -> CatalogSettings:
    return CatalogSettings()
