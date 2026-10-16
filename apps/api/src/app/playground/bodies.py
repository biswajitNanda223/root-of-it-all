"""Request bodies: nested/multiple/embedded bodies, unions, response models, PUT vs PATCH."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Query
from fastapi.encoders import jsonable_encoder

from app.playground.models import (
    AccountIn,
    AccountOut,
    Customer,
    Pet,
    Prefs,
    PrefsPatch,
    Rectangle,
)

router = APIRouter(prefix="/bodies", tags=["playground: bodies"])
_prefs = Prefs()


@router.post("/customer", response_model=Customer, summary="Nested models, lists, sets")
async def customer(body: Customer) -> Customer:
    return body


@router.post("/multiple", summary="Multiple body params + singular value in the body")
async def multiple(
    customer: Customer,
    rect: Rectangle,
    importance: Annotated[int, Body(gt=0)],
    note: Annotated[str | None, Body()] = None,
) -> dict[str, object]:
    return {"customer": customer.name, "area": rect.area, "importance": importance, "note": note}


@router.post("/embed", summary='`embed=True`: body becomes {"rect": {...}}')
async def embed(rect: Annotated[Rectangle, Body(embed=True)]) -> Rectangle:
    return rect


@router.post("/pet", summary="Discriminated union (`pet_type`)")
async def pet(body: Pet) -> dict[str, str]:
    return {"kind": body.pet_type, "class": type(body).__name__}


@router.post("/weights", summary="Bodies of plain `dict[int, float]` / `list[...]`")
async def weights(
    weights: dict[int, float], names: Annotated[list[str] | None, Query()] = None
) -> dict[str, float]:
    return {"total": sum(weights.values()), "n_names": float(len(names or []))}


@router.post(
    "/accounts",
    response_model=AccountOut,
    status_code=201,
    summary="Input model != output model (password never returned)",
)
async def create_account(account: AccountIn) -> AccountIn:
    # Returning the *input* model on purpose: `response_model` filters `password` out.
    return account


@router.get("/prefs", response_model=Prefs)
async def get_prefs() -> Prefs:
    return _prefs


@router.put("/prefs", response_model=Prefs, summary="PUT replaces the whole resource")
async def put_prefs(new: Prefs) -> Prefs:
    global _prefs
    _prefs = new
    return _prefs


@router.patch("/prefs", response_model=Prefs, summary="PATCH updates only the fields sent")
async def patch_prefs(patch: PrefsPatch) -> Prefs:
    global _prefs
    _prefs = _prefs.model_copy(update=patch.model_dump(exclude_unset=True))
    return _prefs


@router.get("/encode", summary="`jsonable_encoder` turns rich objects into JSON-safe data")
async def encode() -> object:
    from datetime import UTC, datetime
    from decimal import Decimal

    return jsonable_encoder(
        {"when": datetime(2025, 1, 1, tzinfo=UTC), "price": Decimal("9.99"), "tags": {"a"}}
    )
