from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from rio_core.errors import UnauthorizedError


@dataclass(frozen=True, slots=True)
class Principal:
    """Who is calling. Built from a verified token, never from a database (services stay decoupled)."""

    subject: str
    is_superuser: bool = False
    scopes: tuple[str, ...] = ()


class JwtTokens:
    """HS256 tokens signed with the platform secret shared by every service."""

    _ALG = "HS256"

    def __init__(self, secret: str, expire_minutes: int = 30) -> None:
        self._secret = secret
        self._ttl = timedelta(minutes=expire_minutes)

    def issue(self, subject: str, claims: Mapping[str, Any] | None = None) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            **(claims or {}),
            "sub": subject,
            "iat": now,
            "exp": now + self._ttl,
        }
        return jwt.encode(payload, self._secret, self._ALG)

    def decode(self, token: str) -> Principal:
        try:
            data = jwt.decode(token, self._secret, algorithms=[self._ALG])
            return Principal(
                subject=str(data["sub"]),
                is_superuser=bool(data.get("adm", False)),
                scopes=tuple(data.get("scopes", ())),
            )
        except (jwt.PyJWTError, KeyError) as exc:
            raise UnauthorizedError("Invalid or expired token") from exc

    def verify(self, token: str) -> str:
        return self.decode(token).subject
