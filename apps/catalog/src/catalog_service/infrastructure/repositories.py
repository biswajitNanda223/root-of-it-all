from __future__ import annotations

from decimal import Decimal
from typing import Any, ClassVar

from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.domain.entities import (
    Category,
    PricedLine,
    Product,
    Reservation,
    StockLine,
)
from catalog_service.domain.ports import ProductFilter
from catalog_service.infrastructure.models import CategoryModel, ProductModel, ReservationModel
from rio_core.errors import NotFoundError


def _cat(m: CategoryModel) -> Category:
    return Category(m.id, m.name, m.slug)


def _prod(m: ProductModel) -> Product:
    return Product(
        m.id,
        m.sku,
        m.name,
        m.description,
        m.price,
        m.stock,
        m.category_id,
        m.is_active,
        m.created_at,
        m.updated_at,
    )


class SqlCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, *, name: str, slug: str) -> Category:
        m = CategoryModel(name=name, slug=slug)
        self._s.add(m)
        await self._s.flush()
        return _cat(m)

    async def list(self) -> list[Category]:
        return [
            _cat(m)
            for m in await self._s.scalars(select(CategoryModel).order_by(CategoryModel.name))
        ]

    async def get_by_slug(self, slug: str) -> Category | None:
        m = await self._s.scalar(select(CategoryModel).where(CategoryModel.slug == slug))
        return _cat(m) if m else None

    async def get(self, category_id: int) -> Category | None:
        m = await self._s.get(CategoryModel, category_id)
        return _cat(m) if m else None


class SqlProductRepository:
    _SORTS: ClassVar[dict[str, Any]] = {
        "id": ProductModel.id,
        "price": ProductModel.price,
        "name": ProductModel.name,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, **fields: object) -> Product:
        m = ProductModel(**fields)
        self._s.add(m)
        await self._s.flush()
        await self._s.refresh(m)
        return _prod(m)

    async def get(self, product_id: int) -> Product | None:
        m = await self._s.get(ProductModel, product_id)
        return _prod(m) if m else None

    async def get_by_sku(self, sku: str) -> Product | None:
        m = await self._s.scalar(select(ProductModel).where(ProductModel.sku == sku))
        return _prod(m) if m else None

    async def search(self, f: ProductFilter) -> tuple[list[Product], int]:
        where: list[ColumnElement[bool]] = [ProductModel.is_active.is_(True)]
        if f.q:
            like = f"%{f.q.lower()}%"
            where.append(
                func.lower(ProductModel.name).like(like) | func.lower(ProductModel.sku).like(like)
            )
        if f.category_id is not None:
            where.append(ProductModel.category_id == f.category_id)
        if f.min_price is not None:
            where.append(ProductModel.price >= f.min_price)
        if f.max_price is not None:
            where.append(ProductModel.price <= f.max_price)
        if f.in_stock is not None:
            where.append(ProductModel.stock > 0 if f.in_stock else ProductModel.stock == 0)
        col = self._SORTS[f.sort.lstrip("-")]
        order = col.desc() if f.sort.startswith("-") else col.asc()
        total = (
            await self._s.scalar(select(func.count()).select_from(ProductModel).where(*where)) or 0
        )
        rows = await self._s.scalars(
            select(ProductModel)
            .where(*where)
            .order_by(order, ProductModel.id)
            .limit(f.limit)
            .offset(f.offset)
        )
        return [_prod(m) for m in rows], total

    async def update(self, product_id: int, **fields: object) -> Product:
        m = await self._s.get(ProductModel, product_id)
        if m is None:
            raise NotFoundError("Product not found")
        for k, v in fields.items():
            setattr(m, k, v)
        await self._s.flush()
        await self._s.refresh(m)
        return _prod(m)

    async def delete(self, product_id: int) -> None:
        m = await self._s.get(ProductModel, product_id)
        if m is not None:
            await self._s.delete(m)
            await self._s.flush()

    async def take_stock(self, line: StockLine) -> bool:
        # Single conditional UPDATE: atomic even under concurrent reservations (no read-modify-write race).
        result = await self._s.execute(
            update(ProductModel)
            .where(
                ProductModel.id == line.product_id,
                ProductModel.stock >= line.quantity,
                ProductModel.is_active.is_(True),
            )
            .values(stock=ProductModel.stock - line.quantity)
        )
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def return_stock(self, line: StockLine) -> None:
        await self._s.execute(
            update(ProductModel)
            .where(ProductModel.id == line.product_id)
            .values(stock=ProductModel.stock + line.quantity)
        )


class SqlReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, reservation_id: str) -> Reservation | None:
        m = await self._s.get(ReservationModel, reservation_id)
        if m is None:
            return None
        lines = [
            PricedLine(
                int(x["product_id"]),
                str(x["sku"]),
                str(x["name"]),
                Decimal(str(x["unit_price"])),
                int(x["quantity"]),
            )
            for x in m.lines
        ]
        return Reservation(m.reservation_id, m.status, lines)

    async def save(self, r: Reservation) -> None:
        payload: list[dict[str, object]] = [
            {
                "product_id": ln.product_id,
                "sku": ln.sku,
                "name": ln.name,
                "unit_price": str(ln.unit_price),
                "quantity": ln.quantity,
            }
            for ln in r.lines
        ]
        m = await self._s.get(ReservationModel, r.reservation_id)
        if m is None:
            self._s.add(
                ReservationModel(reservation_id=r.reservation_id, status=r.status, lines=payload)
            )
        else:
            m.status = r.status
            m.lines = payload
        await self._s.flush()
