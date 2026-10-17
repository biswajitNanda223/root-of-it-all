from __future__ import annotations

from pwdlib import PasswordHash


class Argon2Hasher:
    def __init__(self) -> None:
        self._h = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._h.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._h.verify(password, hashed)
