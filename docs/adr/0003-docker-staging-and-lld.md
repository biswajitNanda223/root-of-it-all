# ADR 0003 – Slim multi-stage Docker, staging = prod shape, lld
Status: accepted
**Context** Small, reproducible images; staging must predict prod. **Decision** One Dockerfile with `runtime`
shared by `staging`/`prod`; compilers only in the builder, using clang+lld; BuildKit cache mounts.
**Consequences** Faster builds and links, ~no toolchain in runtime; dev uses a separate fat target.
