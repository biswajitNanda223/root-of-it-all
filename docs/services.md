# Services: how the monorepo hosts different projects

Every deployable lives in `apps/<name>` and is a **complete FastAPI project**: own models, own Alembic history, own
dependency-injection wiring, own settings, own tests, own container image, own OpenAPI contract. Shared code lives in
`packages/*` and is the *only* thing services have in common.

| Service | Port | Owns | Talks to | Purpose |
|---|---|---|---|---|
| `api` | 8000 | users (`RIO_DATABASE_URL`) | - | **Identity** (register/login, mints JWTs) + demo/playground (items, files, SSE/WS, every FastAPI topic) |
| `catalog` | 8001 | products, categories, reservations (`CATALOG_DATABASE_URL`) | - | Public product search, admin writes, **stock reservation protocol** |
| `orders` | 8002 | orders, lines, outbox (`ORDERS_DATABASE_URL`) | catalog (HTTP) | Order placement saga, state machine, **transactional outbox** |
| `billing` | 8003 | invoices (`BILLING_DATABASE_URL`) | - | One invoice per order, `issued -> paid \| void`; created with `scripts/new-service.sh` (worked example below) |

Run them: `scripts/dev-all.sh` (all) or `scripts/dev.sh catalog`. Swagger: `:8000/docs`, `:8001/docs`, `:8002/docs`.
Contracts: `docs/openapi/<service>.json` (CI fails when stale).

## Shared packages (the dependency rule: `apps -> packages`, never the reverse, never `app -> app`)
| Package | Provides |
|---|---|
| `rio-core` | `CoreSettings` (per-service subclasses), error types, logging, pagination |
| `rio-db` | `Database` (engine + unit of work), `new_metadata()`, `TimestampMixin` |
| `rio-web` | `create_service_app()` (same middleware/errors/probes/docs everywhere), `database_lifespan()`, `get_session` |
| `rio-auth` | Argon2 hasher, `JwtTokens`/`Principal`, `principal_dependency()`, `require_service_key` |
| `rio-native` | lld-linked C extension with pure-Python fallback |

## Boundaries that make them independent
* **Database per service.** Own URL env var, own declarative `Base` (own `MetaData`), own Alembic env and version table
  (`alembic_version_<service>`), so even a shared Postgres instance never mixes schemas. Compose creates one database per
  service. A test (`test_each_service_only_creates_its_own_tables`) pins this.
* **No imports between apps.** `orders` knows catalog only through the `CatalogGateway` port; the adapter
  (`HttpCatalogGateway`) speaks HTTP. Tests plug the real catalog app in through an in-process ASGI transport.
* **Identity once, verified everywhere.** `api` mints HS256 JWTs (claims `sub`, `adm`); every service verifies them
  statelessly with the shared `RIO_SECRET_KEY` (no call to identity, no shared user table). Swagger's *Authorize* in
  catalog/orders points at identity's token URL (`IDENTITY_TOKEN_URL`).
* **Service-to-service auth.** `/internal/*` requires `X-Service-Key` (`RIO_SERVICE_KEY`, constant-time compare).

## Dependency injection, per service
```
api/deps.py   composition root: Depends() builds repositories -> use-cases from adapters (request scope)
services/     use-cases depend on ports (Protocols) only
domain/       entities + ports
infrastructure/ SQLAlchemy repos, HTTP clients - the only place that knows concrete classes
```
Swap anything at the seam: `orders.create_app(settings, catalog_transport=...)` replaces the HTTP transport,
`app.dependency_overrides[...]` replaces any dependency, unit tests inject in-memory fakes.

## The order flow (saga + outbox)
```
client --POST /api/v1/orders--> orders
   1. catalog.reserve(reservation_id)      idempotent, all-or-nothing (atomic conditional UPDATE per line)
   2. persist order + outbox event          ONE local transaction
      if 2 fails -> catalog.release(reservation_id)   (compensation)
cancel -> state machine pending->cancelled -> catalog.release (idempotent upstream)
relay  -> GET /internal/outbox -> publish -> POST /internal/outbox/{id}/ack
```
Prices always come from the catalog reservation, never from the client. Known trade-off: if the process dies between
(1) and (2) the reservation is orphaned; reservations are keyed and idempotent so a reconciliation job can release them.

## Testing pyramid
| Level | Where | Example |
|---|---|---|
| Unit (fakes, no I/O) | `apps/*/tests/test_*service*.py` | saga compensation, state machine |
| Service (TestClient + SQLite) | `apps/*/tests/` | catalog atomic reservation, auth rules |
| **End-to-end (3 services, one loop)** | `tests/e2e/` | register -> admin creates product -> order -> oversell -> cancel -> outbox |

## Add a service (one command)
```bash
scripts/new-service.sh billing --title Billing      # port auto-assigned (or --port 8010)
scripts/dev.sh billing && scripts/test.sh apps/billing/tests
```
It copies `tooling/templates/service` (layered skeleton with an example `notes` resource), registers the app in the
workspace (deps, sources, ruff/mypy/pytest/coverage paths), adds `BILLING_DATABASE_URL` to `.env.development`, creates the
first Alembic revision, and regenerates `compose*.yaml` + `docker-bake.services.hcl` from `[tool.rio.service]`.

`[tool.rio.service]` in `apps/<name>/pyproject.toml` is the single source of truth: `module`, `port`, `database`,
`database_env`, `depends_on`, and `[tool.rio.service.env]` (extra container env). Everything else is derived.

## Add a shared package
Create `packages/<name>/pyproject.toml` (hatchling, `src/rio_<name>`), add it to the workspace `dependencies`/`sources`, then
run `scripts/generate.sh` - it updates the manifest bind-mounts in the Dockerfile (CI fails if you forget).

## Checklist for a new service (what the template already gives you)
`create_service_app` (probes, problem+json, request ids, docs) - `database_lifespan` with its own metadata - settings
subclass with its own DB env var - Alembic with its own version table - port/adapters/DI split - JWT principal dependency -
tests with a per-test SQLite file - container image + compose + bake targets - OpenAPI contract export.

## Worked example: how `billing` was created
```bash
scripts/new-service.sh billing --title Billing     # 1. scaffold (port 8003 auto-assigned)
```
Result of step 1: `apps/billing/` with a working example resource, `BILLING_DATABASE_URL` in `.env.development`, the app
registered in the root `pyproject.toml`, a first migration, and updated `compose*.yaml` / `docker-bake.services.hcl`.

Then the template's `notes` example was replaced by a real domain, layer by layer (same order every time):

| # | File (`apps/billing/src/billing_service/`) | Change |
|---|---|---|
| 1 | `domain/entities.py`, `domain/ports.py` | `Invoice` + `InvoiceStatus`; `InvoiceRepository` Protocol |
| 2 | `services/invoices.py` | rules: one invoice per order, ownership, `issued -> paid \| void` (admin-only void) |
| 3 | `infrastructure/models.py`, `repositories.py` | `InvoiceModel` on the service's own `Base`; SQL adapter |
| 4 | `api/deps.py` | composition root: repository -> service, `PrincipalDep`, `AdminDep` |
| 5 | `api/v1/invoices.py`, `main.py` | DTOs + routes, registered in `create_service_app` |
| 6 | `migrations/versions/0001_*.py` | regenerated with `scripts/migrate.sh billing revision -m "initial schema"` |
| 7 | `tests/test_invoices.py` | state machine, isolation, one-per-order, own-tables-only |

Finally `scripts/export-openapi.sh billing` wrote `docs/openapi/billing.json`, and `scripts/check.sh` was green.
