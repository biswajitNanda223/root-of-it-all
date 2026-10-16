import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep
from app.api.schemas import Problem, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger(__name__)


def _send_welcome(email: str) -> None:
    """Stand-in for an email provider; runs after the response is sent."""
    log.info("welcome email queued for %s", email)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": Problem}},
)
async def register(body: UserCreate, auth: AuthServiceDep, background: BackgroundTasks) -> UserRead:
    user = await auth.register(email=body.email, password=body.password, full_name=body.full_name)
    background.add_task(_send_welcome, user.email)
    return UserRead.model_validate(user)


@router.post("/token", response_model=Token, responses={401: {"model": Problem}})
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], auth: AuthServiceDep
) -> Token:
    """OAuth2 password flow; `username` is the email."""
    return Token(access_token=await auth.login(email=form.username, password=form.password))
