"""HTTP adapter for the catalog service (implements `CatalogGateway`)."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

import httpx

from orders_service.domain.entities import OrderLine, WantedLine
from rio_core.errors import ConflictError, NotFoundError, UpstreamError


class HttpCatalogGateway:
    def __init__(self, client: httpx.AsyncClient, service_key: str) -> None:
        self._client = client
        self._headers = {"X-Service-Key": service_key}

    async def _post(self, path: str, json: Mapping[str, Any] | None = None) -> httpx.Response:
        try:
            resp = await self._client.post(path, json=json, headers=self._headers)
        except httpx.HTTPError as exc:
            raise UpstreamError(f"catalog unreachable: {type(exc).__name__}") from exc
        if resp.status_code == 404:
            raise NotFoundError(resp.json().get("detail", "not found"))
        if resp.status_code == 409:
            raise ConflictError(resp.json().get("detail", "conflict"))
        if resp.status_code >= 400:
            raise UpstreamError(f"catalog answered {resp.status_code}")
        return resp

    async def reserve(self, reservation_id: str, lines: list[WantedLine]) -> list[OrderLine]:
        body = {
            "reservation_id": reservation_id,
            "lines": [{"product_id": ln.product_id, "quantity": ln.quantity} for ln in lines],
        }
        data = (await self._post("/internal/stock/reserve", body)).json()
        return [
            OrderLine(x["product_id"], x["sku"], x["name"], Decimal(x["unit_price"]), x["quantity"])
            for x in data["lines"]
        ]

    async def release(self, reservation_id: str) -> None:
        await self._post(f"/internal/stock/release/{reservation_id}")


class UuidGenerator:
    def new(self) -> str:
        return uuid.uuid4().hex
