# lld toolchain profiles

Linking is the slowest, least-cached step of any native build. Everything here makes **LLVM lld** the linker for
C/C++ (setuptools / cffi) and Rust (maturin / pyo3) code, consistently on laptops, CI and Docker.

Layering (later wins), loaded by `scripts/_lib.sh::use_lld <project> [profile]`:

| Layer | File | Scope |
|---|---|---|
| 1 | `tooling/lld/base.env` | compiler + lld selection, hardening flags for the whole repo |
| 2 | `tooling/lld/profiles/<profile>.env` | `dev` (fast links, debug info) or `release` (ICF, GC, ThinLTO) |
| 3 | `<project dir>/lld.env` | per-project override, e.g. `packages/native/lld.env` |

The same files are copied into the Docker `toolchain` stage and loaded by `tooling/lld/load.sh`, so a project's
flags are identical in every environment. Profile is chosen with `LLD_PROFILE` (default `dev` locally, `release`
in Docker/CI). `scripts/lld-doctor.sh [project]` proves lld is really used (reads the ELF `.comment` section).

Rust: `.cargo/config.toml` points the linker at `clang -fuse-ld=lld`.
