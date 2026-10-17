"""Use cases. Pure orchestration over ports - no FastAPI, no SQLAlchemy."""

from __future__ import annotations

import re

from catalog_service.domain.entities import (
    Category,
    PricedLine,
    Product,
    Reservation,
    StockLine,
)
from catalog_service.domain.ports import (
    CategoryRepository,
    ProductFilter,
    ProductRepository,
    ReservationRepository,
)
from rio_core.errors import ConflictError, NotFoundError


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class CatalogService:
    def __init__(self, categories: CategoryRepository, products: ProductRepository) -> None:
        self._categories = categories
        self._products = products

    async def create_category(self, name: str) -> Category:
        slug = slugify(name)
        if await self._categories.get_by_slug(slug):
            raise ConflictError(f"category '{slug}' exists")
        return await self._categories.add(name=name, slug=slug)

    async def list_categories(self) -> list[Category]:
        return await self._categories.list()

    async def create_product(self, **fields: object) -> Product:
        if await self._products.get_by_sku(str(fields["sku"])):
            raise ConflictError(f"sku {fields['sku']} exists")
        await self._check_category(fields.get("category_id"))
        return await self._products.add(**fields)

    async def _check_category(self, category_id: object) -> None:
        if category_id is not None and not await self._categories.get(int(category_id)):  # type: ignore[call-overload]
            raise NotFoundError(f"category {category_id} not found")

    async def get_product(self, product_id: int) -> Product:
        product = await self._products.get(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    async def search(self, f: ProductFilter) -> tuple[list[Product], int]:
        return await self._products.search(f)

    async def update_product(self, product_id: int, **fields: object) -> Product:
        await self.get_product(product_id)
        await self._check_category(fields.get("category_id"))
        return await self._products.update(product_id, **fields)

    async def delete_product(self, product_id: int) -> None:
        await self.get_product(product_id)
        await self._products.delete(product_id)


class StockService:
    """Reservation protocol used by the orders service (idempotent per `reservation_id`)."""

    def __init__(self, products: ProductRepository, reservations: ReservationRepository) -> None:
        self._products = products
        self._reservations = reservations

    async def reserve(self, reservation_id: str, lines: list[StockLine]) -> Reservation:
        existing = await self._reservations.get(reservation_id)
        if existing is not None:
            return existing  # replay-safe
        merged: dict[int, int] = {}
        for ln in lines:
            merged[ln.product_id] = merged.get(ln.product_id, 0) + ln.quantity
        priced: list[PricedLine] = []
        for pid, qty in merged.items():
            product = await self._products.get(pid)
            if product is None or not product.is_active:
                raise NotFoundError(f"product {pid} not found")
            if not await self._products.take_stock(StockLine(pid, qty)):
                raise ConflictError(f"insufficient stock for '{product.name}' (sku {product.sku})")
            priced.append(PricedLine(pid, product.sku, product.name, product.price, qty))
        reservation = Reservation(reservation_id, "reserved", priced)
        await self._reservations.save(reservation)
        return reservation

    async def release(self, reservation_id: str) -> Reservation:
        reservation = await self._reservations.get(reservation_id)
        if reservation is None:
            raise NotFoundError("reservation not found")
        if reservation.status == "released":
            return reservation  # idempotent
        for ln in reservation.lines:
            await self._products.return_stock(StockLine(ln.product_id, ln.quantity))
        released = Reservation(reservation_id, "released", reservation.lines)
        await self._reservations.save(released)
        return released
