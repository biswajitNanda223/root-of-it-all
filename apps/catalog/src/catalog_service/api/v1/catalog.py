from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query, Response, status

from catalog_service.api.deps import AdminDep, CatalogDep
from catalog_service.api.schemas import (
    CategoryIn,
    CategoryOut,
    ProductIn,
    ProductOut,
    ProductPatch,
    ProductQuery,
)
from rio_core.pagination import Page

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])
ProductId = Annotated[int, Path(ge=1)]


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(svc: CatalogDep) -> list[CategoryOut]:
    return [CategoryOut.model_validate(c) for c in await svc.list_categories()]


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(body: CategoryIn, _: AdminDep, svc: CatalogDep) -> CategoryOut:
    return CategoryOut.model_validate(await svc.create_category(body.name))


@router.get("/products", response_model=Page[ProductOut], summary="Search products (public)")
async def search_products(q: Annotated[ProductQuery, Query()], svc: CatalogDep) -> Page[ProductOut]:
    items, total = await svc.search(q)
    return Page(
        items=[ProductOut.model_validate(p) for p in items],
        total=total,
        limit=q.limit,
        offset=q.offset,
    )


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: ProductId, svc: CatalogDep) -> ProductOut:
    return ProductOut.model_validate(await svc.get_product(product_id))


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(body: ProductIn, _: AdminDep, svc: CatalogDep) -> ProductOut:
    return ProductOut.model_validate(await svc.create_product(**body.model_dump()))


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: ProductId, body: ProductPatch, _: AdminDep, svc: CatalogDep
) -> ProductOut:
    return ProductOut.model_validate(
        await svc.update_product(product_id, **body.model_dump(exclude_unset=True))
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: ProductId, _: AdminDep, svc: CatalogDep) -> Response:
    await svc.delete_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
