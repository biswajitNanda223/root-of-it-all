from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field

from rio_core.config import CoreSettings


class OrdersSettings(CoreSettings):
    app_name: str = "orders-service"
    database_url: str = Field(
        default="sqlite+aiosqlite:///./orders.db",
        validation_alias=AliasChoices("ORDERS_DATABASE_URL"),
    )
    catalog_url: str = Field(
        default="http://localhost:8001", validation_alias=AliasChoices("CATALOG_URL")
    )
    catalog_timeout_seconds: float = Field(default=3.0, gt=0)


@lru_cache
def get_settings() -> OrdersSettings:
    return OrdersSettings()
