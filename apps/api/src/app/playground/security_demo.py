"""Security schemes beyond the main JWT flow: API key, HTTP Basic, OAuth2 scopes."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Security
from fastapi.security import (
    APIKeyHeader,
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from pydantic import BaseModel

from app.api.deps import SettingsDep
from rio_core.errors import ForbiddenError, UnauthorizedError

router = APIRouter(prefix="/security", tags=["playground: security"])

api_key_header = APIKeyHeader(name="X-API-Key", scheme_name="PlaygroundApiKey", auto_error=False)
basic = HTTPBasic(scheme_name="PlaygroundBasic", auto_error=False)
SCOPES = {"items:read": "Read items", "items:write": "Write items", "admin": "Everything"}
scoped = OAuth2PasswordBearer(
    tokenUrl="/api/v1/playground/security/token", scopes=SCOPES, scheme_name="PlaygroundScopes"
)
_AUD = "playground"


async def api_key(
    key: Annotated[str | None, Security(api_key_header)], settings: SettingsDep
) -> str:
    if not key or not secrets.compare_digest(key, settings.playground_api_key.get_secret_value()):
        raise UnauthorizedError("bad or missing X-API-Key")
    return key


@router.get("/api-key", summary="API key in a header (`demo-key`)")
async def by_api_key(_: Annotated[str, Depends(api_key)]) -> dict[str, str]:
    return {"auth": "api-key"}


@router.get("/basic", summary="HTTP Basic (`demo` / `demo`) with constant-time compare")
async def by_basic(creds: Annotated[HTTPBasicCredentials | None, Depends(basic)]) -> dict[str, str]:
    ok = (
        creds is not None
        and secrets.compare_digest(creds.username, "demo")
        and secrets.compare_digest(creds.password, "demo")
    )
    if not ok:
        raise UnauthorizedError("bad basic credentials")
    return {"auth": "basic", "user": "demo"}


class ScopedToken(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    scope: str


@router.post(
    "/token", response_model=ScopedToken, summary="Issue a token carrying the *requested* scopes"
)
async def issue_token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], settings: SettingsDep
) -> ScopedToken:
    if not (form.username == "demo" and form.password == "demo"):  # noqa: S105
        raise UnauthorizedError("use demo / demo")
    granted = [s for s in form.scopes if s in SCOPES]
    now = datetime.now(UTC)
    token = jwt.encode(
        {"sub": "demo", "scopes": granted, "aud": _AUD, "exp": now + timedelta(minutes=15)},
        settings.secret_key.get_secret_value(),
        "HS256",
    )
    return ScopedToken(access_token=token, scope=" ".join(granted))


async def scoped_user(
    needed: SecurityScopes, token: Annotated[str, Depends(scoped)], settings: SettingsDep
) -> str:
    try:
        claims = jwt.decode(
            token, settings.secret_key.get_secret_value(), algorithms=["HS256"], audience=_AUD
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("invalid token") from exc
    have = set(claims.get("scopes", []))
    if "admin" not in have and not set(needed.scopes) <= have:
        raise ForbiddenError(f"missing scope(s): {sorted(set(needed.scopes) - have)}")
    return str(claims["sub"])


@router.get("/scoped/read", summary="Needs scope `items:read`")
async def scoped_read(
    user: Annotated[str, Security(scoped_user, scopes=["items:read"])],
) -> dict[str, str]:
    return {"user": user, "can": "read"}


@router.post("/scoped/write", summary="Needs scope `items:write`")
async def scoped_write(
    user: Annotated[str, Security(scoped_user, scopes=["items:write"])],
) -> dict[str, str]:
    return {"user": user, "can": "write"}
