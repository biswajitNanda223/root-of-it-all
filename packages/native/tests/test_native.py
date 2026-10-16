import rio_native
from rio_native import _fnv1a64_py, fnv1a64


def test_known_vectors() -> None:
    assert fnv1a64(b"") == 0xCBF29CE484222325
    assert fnv1a64(b"a") == 0xAF63DC4C8601EC8C
    assert fnv1a64(b"foobar") == 0x85944171F73967E8


def test_native_matches_fallback() -> None:
    data = bytes(range(256)) * 10
    assert fnv1a64(data) == _fnv1a64_py(data)


def test_reports_build_flavour() -> None:
    assert isinstance(rio_native.NATIVE, bool)
