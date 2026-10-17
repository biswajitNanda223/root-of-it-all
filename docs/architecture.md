# Architecture

## Goals
Many deployables, one toolchain, one lockfile, strict boundaries, fast CI, small images.

> Multiple independent services? Read [services.md](services.md) first - this page describes the shared architecture.

## Monorepo layout & dependency rule
```
apps/*      deployables      may depend on  packages/*
packages/*  libraries        must NOT depend on apps/*
```
`uv` workspace members share one `uv.lock`; `[tool.uv.sources]` marks internal deps as `workspace = true`.
Add a new service by creating `apps/<name>/pyproject.toml` (it is picked up by `members = ["apps/*"]`).

## Service layering (every app: `api`, `catalog`, `orders`, ...)
```
api/             HTTP only: routers, DTOs (schemas), DI wiring (deps.py)
services/        use-cases; depend only on domain ports
domain/          entities (dataclasses) + ports (Protocols)
infrastructure/  adapters: SQLAlchemy repos, Argon2, JWT
```
Dependencies point inward. `api → services → domain ← infrastructure`; only `api/deps.py` (the composition
root) knows concrete classes.

### SOLID in practice
- **S**: routers translate HTTP; services hold rules; repositories own persistence.
- **O**: new storage = new adapter implementing a port; no service change.
- **L**: any `UserRepository` satisfies the Protocol (see `tests/unit` fakes).
- **I**: small, role-specific ports (`PasswordHasher`, `TokenIssuer`, repos).
- **D**: services receive ports via constructor; FastAPI `Depends` is the injector.

## Request lifecycle
`RequestContextMiddleware` (id, timing, headers) → CORS/TrustedHost/GZip → router → dependencies
(`get_session` opens one transaction/unit of work; commit on success, rollback on error) → service → repo.
`AppError` subclasses map to `application/problem+json` in one handler.

## Data
Async SQLAlchemy 2. SQLite (aiosqlite) for dev/test, Postgres (asyncpg) for compose/staging/prod.
Schema changes ship as Alembic migrations (`scripts/migrate.sh revision -m ...`); CI fails on drift
(`alembic check`). `RIO_AUTO_CREATE_TABLES` exists only for dev/test.

## Configuration
12-factor env vars, prefix `RIO_`, validated at boot. Staging/production refuse to start with the default secret
or `debug=true`.

## Observability
Structured JSON logs (`RIO_LOG_JSON`), `X-Request-ID` correlation, `/health/live` & `/health/ready`.

## Security
Argon2id, short-lived JWT, non-root read-only container with dropped capabilities, security headers,
upload size cap, docs disabled in prod, secrets only via env.

## Native builds & lld (see [lld.md](lld.md))
Python deps are wheels almost always; when one must compile, the builder image uses `clang` + `lld`
(`LDFLAGS=-fuse-ld=lld`, `RUSTFLAGS`, `.cargo/config.toml`) for much faster links. `scripts/_lib.sh::use_lld`
applies the same flags locally when `ld.lld` is installed. Runtime images contain none of it.

## Playground (optional module)
`app/playground/` is mounted by one call (`playground.register(app)`) when `RIO_PLAYGROUND_ENABLED`; core code never
imports it, and settings *refuse to start in production* with it enabled. Its in-memory shop uses the same patterns
(DI, problem+json, pagination) so it doubles as a template for new features.

## Tooling layer
`tooling/lld` (toolchain profiles), `tooling/affected.py` (dependency-aware change detection) and `scripts/hooks`
(commit checks) are shared by local scripts, Docker and CI so all three behave identically.

## Evolution
Add `apps/worker` (queue consumer) reusing `rio-core`/`rio-db`; split `domain` into a package once a second app
needs it. See ADRs.
