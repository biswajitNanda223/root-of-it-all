import pytest

from rio_auth import Argon2Hasher, JwtTokens
from rio_core.errors import UnauthorizedError


def test_hash_roundtrip() -> None:
    h = Argon2Hasher()
    hashed = h.hash("password123")
    assert h.verify("password123", hashed)
    assert not h.verify("nope", hashed)


def test_token_claims_roundtrip() -> None:
    t = JwtTokens("s" * 32)
    p = t.decode(t.issue("42", {"adm": True, "scopes": ["a"]}))
    assert (p.subject, p.is_superuser, p.scopes) == ("42", True, ("a",))
    assert t.verify(t.issue("7")) == "7"


def test_bad_signature_rejected() -> None:
    with pytest.raises(UnauthorizedError):
        JwtTokens("a" * 32).decode(JwtTokens("b" * 32).issue("1"))
