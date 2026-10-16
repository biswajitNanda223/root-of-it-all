from __future__ import annotations

from app.domain.entities import User
from app.domain.ports import PasswordHasher, TokenIssuer, UserRepository
from rio_core.errors import ConflictError, UnauthorizedError


class AuthService:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenIssuer) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def register(
        self, *, email: str, password: str, full_name: str | None, is_superuser: bool = False
    ) -> User:
        email = email.lower()
        if await self._users.get_by_email(email):
            raise ConflictError("Email already registered")
        return await self._users.add(
            email=email,
            hashed_password=self._hasher.hash(password),
            full_name=full_name,
            is_superuser=is_superuser,
        )

    async def login(self, *, email: str, password: str) -> str:
        user = await self._users.get_by_email(email.lower())
        if (
            not user
            or not user.is_active
            or not self._hasher.verify(password, user.hashed_password)
        ):
            raise UnauthorizedError("Incorrect email or password")
        return self._tokens.issue(str(user.id))

    async def authenticate(self, token: str) -> User:
        user = await self._users.get(int(self._tokens.verify(token)))
        if not user or not user.is_active:
            raise UnauthorizedError("Invalid credentials")
        return user
