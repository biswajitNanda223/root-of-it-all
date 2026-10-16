from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from rio_core.errors import UnauthorizedError


class Argon2Hasher:
    def __init__(self) -> None:
        self._h = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._h.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._h.verify(password, hashed)


class JwtTokens:
    _ALG = "HS256"

    def __init__(self, secret: str, expire_minutes: int) -> None:
        self._secret = secret
        self._ttl = timedelta(minutes=expire_minutes)

    def issue(self, subject: str) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {"sub": subject, "iat": now, "exp": now + self._ttl}, self._secret, self._ALG
        )

    def verify(self, token: str) -> str:
        try:
            sub = jwt.decode(token, self._secret, algorithms=[self._ALG])["sub"]
        except (jwt.PyJWTError, KeyError) as exc:
            raise UnauthorizedError("Invalid or expired token") from exc
        return str(sub)
