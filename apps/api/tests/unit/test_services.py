"""Services tested against in-memory fakes - proves the ports make them framework-free."""

import pytest

from app.domain.entities import User
from app.services.auth import AuthService
from rio_auth import Argon2Hasher, JwtTokens
from rio_core.errors import ConflictError, UnauthorizedError


class FakeUsers:
    def __init__(self) -> None:
        self.rows: dict[int, User] = {}

    async def get(self, user_id: int) -> User | None:
        return self.rows.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    async def add(self, *, email, hashed_password, full_name, is_superuser=False):  # type: ignore[no-untyped-def]
        from datetime import UTC, datetime

        u = User(
            len(self.rows) + 1,
            email,
            hashed_password,
            full_name,
            True,
            is_superuser,
            datetime.now(UTC),
        )
        self.rows[u.id] = u
        return u

    async def list(self, *, limit, offset):  # type: ignore[no-untyped-def]
        return list(self.rows.values()), len(self.rows)


@pytest.fixture
def auth() -> AuthService:
    return AuthService(FakeUsers(), Argon2Hasher(), JwtTokens("s" * 32, 5))  # type: ignore[arg-type]


async def test_register_login_authenticate(auth: AuthService) -> None:
    user = await auth.register(email="X@Example.com", password="password123", full_name=None)
    assert user.email == "x@example.com"
    token = await auth.login(email="x@example.com", password="password123")
    assert (await auth.authenticate(token)).id == user.id


async def test_duplicate_and_bad_password(auth: AuthService) -> None:
    await auth.register(email="a@b.co", password="password123", full_name=None)
    with pytest.raises(ConflictError):
        await auth.register(email="a@b.co", password="password123", full_name=None)
    with pytest.raises(UnauthorizedError):
        await auth.login(email="a@b.co", password="wrong")
