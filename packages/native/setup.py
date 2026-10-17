"""The extension is optional: if no compiler is present the pure-Python fallback is used."""

from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension(
            "rio_native._fast",
            sources=["src/rio_native/_fast.c"],
            optional=True,
            # Project-wide flags (CC / CFLAGS / LDFLAGS incl. -fuse-ld=lld) come from
            # tooling/lld/*.env via scripts/_lib.sh, the Dockerfile, or CI - not hard-coded here.
        )
    ],
)
