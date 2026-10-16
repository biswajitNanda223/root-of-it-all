from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, SuperUser
from app.api.schemas import UserRead
from app.infrastructure.repositories import SqlUserRepository
from rio_core.pagination import Page, PageParams

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.get("", response_model=Page[UserRead], summary="List users (superuser only)")
async def list_users(
    _: SuperUser, session: SessionDep, page: Annotated[PageParams, Depends()]
) -> Page[UserRead]:
    users, total = await SqlUserRepository(session).list(limit=page.limit, offset=page.offset)
    return Page(
        items=[UserRead.model_validate(u) for u in users],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )
