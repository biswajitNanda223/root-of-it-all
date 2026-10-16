# lld in the monorepo

**Why**: linking dominates native build time and is never cached by uv. lld is 2-10x faster than GNU ld and
supports ThinLTO, ICF and section GC, which also shrink the artifact.

**Where native code exists**: `packages/native` - a small CPython C extension (`fnv1a64`, used by uploads) with a
pure-Python fallback (`optional=True`, so no compiler = still works). It is the real, tested showcase; any future
Rust/maturin or cffi dependency inherits the same flags.

## Layered configuration (`tooling/lld/`)
```
base.env              repo-wide: CC/CXX=clang, LDSHARED, -fuse-ld=lld, relro/now, stack protector, RUSTFLAGS
profiles/dev.env      -O0 -g, compressed debug sections          (fast edit-link loop)
profiles/release.env  -O2, ThinLTO (+cache dir), --gc-sections, --icf=safe, build-id=sha1, Rust LTO
<project>/lld.env     per-project override, e.g. packages/native/lld.env: -fvisibility=hidden, --exclude-libs
```
`tooling/lld/load.sh <project> [profile]` composes the layers. It is used identically by
`scripts/_lib.sh` (every script), the `Dockerfile` (per-project, per-stage) and CI.
`LDSHARED="$CC -shared"` is pinned because setuptools otherwise links with the interpreter's build-time `gcc`
even when `CC=clang` (we verified this: compiled with clang, linked with GNU ld).

## Commands
```bash
scripts/lld-doctor.sh [project] [profile]   # links a probe binary and checks the ELF .comment says "Linker: ... LLD"
scripts/native.sh [dev|release]             # force-rebuild rio-native under that profile and verify the .so
LLD_PROFILE=release scripts/test.sh         # any script honours LLD_PROFILE
```
uv caches built wheels by source, not by flags - use `scripts/native.sh` after changing a profile.

## Docker
Build args: `LLD_PROFILE` (default `release`; `dev` target uses `dev`). The `deps` stage compiles third-party
sdists under the repo layer; the `builder` stage builds `rio-native` under `packages/native/lld.env`, then `api`
under `apps/api/lld.env`. BuildKit cache mounts keep uv downloads and the ThinLTO cache (`/cache/lld`) warm.
Compiled extensions are `strip --strip-unneeded`'d; compilers never reach the runtime image.

## Rust
`.cargo/config.toml` sets `linker = "clang"` + `-fuse-ld=lld` for x86_64 and aarch64 Linux; `RUSTFLAGS` from the
profiles adds ThinLTO in release.
