"""FNV-1a hashing: C extension when built, identical pure-Python fallback otherwise."""

from __future__ import annotations

from collections.abc import Buffer

_OFFSET, _PRIME, _MASK = 14695981039346656037, 1099511628211, (1 << 64) - 1


def _fnv1a64_py(data: Buffer) -> int:
    h = _OFFSET
    for b in memoryview(data).cast("B"):
        h = ((h ^ b) * _PRIME) & _MASK
    return h


try:
    from rio_native._fast import fnv1a64

    NATIVE = True
except ImportError:  # extension not built (no compiler) -> still correct, just slower
    fnv1a64 = _fnv1a64_py
    NATIVE = False

__all__ = ["NATIVE", "fnv1a64"]
