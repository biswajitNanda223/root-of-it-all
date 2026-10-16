# root-of-it-all

Production-grade **FastAPI monorepo** managed with **uv workspaces**, **mise**, plain `.sh` entry points,
and a light multi-stage **Docker** build (dev → staging → prod) that links native code with **lld**.

```
.
├── apps/api/            FastAPI service  (domain → services → infrastructure → api)
├── packages/core/       rio-core: settings, errors, logging, pagination
├── packages/db/         rio-db:   async SQLAlchemy Base / Database
├── packages/native/     rio-native: C extension (lld-linked) with pure-Python fallback
├── tooling/             lld profiles (base → dev/release → per-project) and affected-project detection
├── scripts/             *.sh wrappers around `uv run` (+ git hooks in scripts/hooks)
├── docs/                architecture, ADRs, BMAD artifacts, guides, OpenAPI contract
├── Dockerfile           targets: dev | test | staging | prod      docker-bake.hcl: multi-arch + SBOM
├── compose*.yaml        base + per-environment overrides
├── .env.development     plaintext dev defaults; .env.staging/.env.production are dotenvx-ENCRYPTED
├── mise.toml            tool pins (python, uv, node, dotenvx), tasks
└── pyproject.toml       uv workspace root + ruff / mypy / pytest config
```

## Quick start

```bash
mise install            # python 3.13 + uv   (or: install uv yourself)
scripts/bootstrap.sh    # uv sync --frozen, .env, git hooks
scripts/dev.sh          # http://localhost:8000/docs
scripts/check.sh        # lint + mypy --strict + tests(+coverage) + migration drift
```

| Script | What it does |
|---|---|
| `scripts/dev.sh` / `start.sh` | reload server / production server (workers, proxy headers) |
| `scripts/lint.sh` `format.sh` `typecheck.sh` `test.sh` | ruff, ruff fix, mypy strict, pytest (`COV=1` for coverage gate) |
| `scripts/env.sh init\|set\|get\|decrypt\|check` | encrypted env files via **dotenvx** ([docs/secrets.md](docs/secrets.md)) |
| `scripts/migrate.sh` | Alembic: `upgrade head`, `revision -m "msg"`, `check` |
| `scripts/docker.sh <dev\|staging\|prod> <up\|down\|logs\|build>` | compose stacks |
| `scripts/export-openapi.sh` | write `docs/openapi.json` contract (CI fails if stale) |
| `scripts/lld-doctor.sh` `native.sh` | prove lld links / rebuild the C extension under a profile |
| `scripts/affected.sh` | which workspace projects the current change touches |
| `scripts/lock.sh [--upgrade]` | refresh `uv.lock` |

Each is also a mise task (`mise run check`, `mise run docker:staging`, …).

## FastAPI features demonstrated
**Every topic of the official docs has a runnable example** - see [FastAPI coverage map](docs/fastapi-coverage.md). Core features:
App factory + lifespan · settings (pydantic-settings) · routers & versioning (`/api/v1`) · dependency injection
(`Annotated` aliases, per-request unit of work) · OAuth2 password flow + JWT · Argon2 hashing · typed
request/response models · pagination · RFC 7807 `application/problem+json` errors · custom exception handlers ·
pure-ASGI middleware (request-id, timing, security headers) · CORS / GZip / TrustedHost · `BackgroundTasks` ·
streaming uploads with size cap · Server-Sent Events · WebSockets · OpenAPI tags/metadata · health/readiness probes ·
`TestClient` integration tests. Plus a **playground** (`/api/v1/playground`, off in production): one dummy API per docs topic and an end-to-end *shop* (products → orders → pay → events, with idempotency keys, OpenAPI callbacks and webhooks).

## Docs
[Architecture](docs/architecture.md) · [Development](docs/development.md) · [Deployment & Docker](docs/deployment.md) ·
[Secrets (dotenvx)](docs/secrets.md) · [lld](docs/lld.md) · [Git workflow & hooks](docs/git-workflow.md) · [API guide](docs/api.md) ·
[FastAPI coverage](docs/fastapi-coverage.md) · [ADRs](docs/adr/) · [BMAD artifacts](docs/bmad/README.md) ·
[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)
