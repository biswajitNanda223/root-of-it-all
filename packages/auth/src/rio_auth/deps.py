# NOTE: no `from __future__ import annotations` - FastAPI resolves these closure annotations at definition time.
import secrets
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from rio_auth.tokens import JwtTokens, Principal
from rio_core.config import CoreSettings
from rio_core.errors import UnauthorizedError


def principal_dependency(token_url: str) -> Callable[..., Awaitable[Principal]]:
    """Build a `current principal` dependency whose Swagger *Authorize* points at the identity service."""
    scheme = OAuth2PasswordBearer(tokenUrl=token_url, scheme_name="IdentityJWT")

    async def current_principal(
        request: Request, token: Annotated[str, Depends(scheme)]
    ) -> Principal:
        settings: CoreSettings = request.app.state.settings
        return JwtTokens(settings.secret_key.get_secret_value()).decode(token)

    return current_principal


_service_key = APIKeyHeader(name="X-Service-Key", scheme_name="ServiceKey", auto_error=False)


async def require_service_key(
    request: Request, key: Annotated[str | None, Depends(_service_key)]
) -> None:
    """Guard for `/internal/*`: service-to-service calls carry the shared key (constant-time compare)."""
    expected = request.app.state.settings.service_key.get_secret_value()
    if not key or not secrets.compare_digest(key, expected):
        raise UnauthorizedError("missing or invalid X-Service-Key")
