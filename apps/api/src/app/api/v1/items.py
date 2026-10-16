from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from app.api.deps import CurrentUser, ItemServiceDep
from app.api.schemas import ItemCreate, ItemRead, ItemUpdate, Problem
from rio_core.pagination import Page, PageParams

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={401: {"model": Problem}, 403: {"model": Problem}, 404: {"model": Problem}},
)
ItemId = Annotated[int, Path(ge=1, description="Item identifier")]


@router.get("", response_model=Page[ItemRead])
async def list_items(
    user: CurrentUser, svc: ItemServiceDep, page: Annotated[PageParams, Depends()]
) -> Page[ItemRead]:
    items, total = await svc.list(user, limit=page.limit, offset=page.offset)
    return Page(
        items=[ItemRead.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(body: ItemCreate, user: CurrentUser, svc: ItemServiceDep) -> ItemRead:
    return ItemRead.model_validate(
        await svc.create(user, title=body.title, description=body.description)
    )


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: ItemId, user: CurrentUser, svc: ItemServiceDep) -> ItemRead:
    return ItemRead.model_validate(await svc.get(user, item_id))


@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: ItemId, body: ItemUpdate, user: CurrentUser, svc: ItemServiceDep
) -> ItemRead:
    return ItemRead.model_validate(
        await svc.update(user, item_id, title=body.title, description=body.description)
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: ItemId, user: CurrentUser, svc: ItemServiceDep) -> Response:
    await svc.delete(user, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
