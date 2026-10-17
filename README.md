# root-of-it-all

Production-grade **FastAPI monorepo** managed with **uv workspaces**, **mise**, plain `.sh` entry points,
and a light multi-stage **Docker** build (dev → staging → prod) that links native code with **lld**.

```
.
├── apps/
│   ├── api/             identity (JWT) + playground      :8000   own DB, own Alembic
│   ├── catalog/         products & stock reservation     :8001   own DB, own Alembic
│   ├── orders/          order saga + outbox → catalog    :8002   own DB, own Alembic
│   └── billing/         invoices (made with new-service) :8003   own DB, own Alembic
├── packages/
│   ├── core/  db/       settings · errors · logging · async SQLAlchemy unit of work
│   ├── web/             create_service_app(): middleware, problem+json, probes, DB lifespan, DI backbone
│   ├── auth/            Argon2, JWT principal, service-key guard
│   └── native/          C extension (lld-linked) with pure-Python fallback
├── tests/e2e/           identity → catalog → orders across three real apps
├── tooling/             service registry + generators, scaffolder, templates, lld profiles, affected-project detection
├── scripts/             *.sh wrappers around `uv run` (service-aware) + git hooks
├── docs/                architecture, services guide, ADRs, BMAD artifacts, OpenAPI contracts (docs/openapi/)
├── Dockerfile           ONE file for every service · targets dev | test | staging | prod
├── compose*.yaml        GENERATED from apps/*/pyproject.toml [tool.rio.service]
├── .env.development     plaintext dev defaults; .env.staging/.env.production are dotenvx-ENCRYPTED
└── mise.toml            tool pins (python, uv, node, dotenvx), tasks
```

**Add another project in one command:** `scripts/new-service.sh billing` — see [docs/services.md](docs/services.md).

## Quick start

```bash
mise install            # python 3.13 + uv   (or: install uv yourself)
scripts/bootstrap.sh    # uv sync --frozen, .env, git hooks
scripts/dev-all.sh      # all services: :8000 identity, :8001 catalog, :8002 orders, :8003 billing (each has /docs)
scripts/dev.sh catalog  # or just one
scripts/check.sh        # lint + mypy --strict + tests(+coverage) + migration drift
```

| Script | What it does |
|---|---|
| `scripts/dev.sh [svc]` / `dev-all.sh` / `start.sh [svc]` | reload server(s) / production server (workers, proxy headers) |
| `scripts/new-service.sh <name>` | scaffold a new service (workspace, Alembic, compose, bake) — [services.md](docs/services.md) |
| `scripts/generate.sh` | regenerate compose/bake/Dockerfile manifests from `[tool.rio.service]` |
| `scripts/lint.sh` `format.sh` `typecheck.sh` `test.sh` | ruff, ruff fix, mypy strict, pytest (`COV=1` for coverage gate) |
| `scripts/env.sh init\|set\|get\|decrypt\|check` | encrypted env files via **dotenvx** ([docs/secrets.md](docs/secrets.md)) |
| `scripts/migrate.sh [svc\|all]` | Alembic per service: `upgrade head`, `revision -m "msg"`, `check` |
| `scripts/docker.sh <dev\|staging\|prod> <up\|down\|logs\|build>` | compose stacks |
| `scripts/export-openapi.sh [svc]` | write `docs/openapi/<svc>.json` contracts (CI fails if stale) |
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
[Architecture](docs/architecture.md) · [Services guide](docs/services.md) · [Development](docs/development.md) · [Deployment & Docker](docs/deployment.md) ·
[Secrets (dotenvx)](docs/secrets.md) · [lld](docs/lld.md) · [Git workflow & hooks](docs/git-workflow.md) · [API guide](docs/api.md) ·
[FastAPI coverage](docs/fastapi-coverage.md) · [ADRs](docs/adr/) · [BMAD artifacts](docs/bmad/README.md) ·
[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)
