# Deployment & Docker

## Image graph (one Dockerfile)
```
toolchain (clang, lld, uv) ─► deps ─► builder ─► runtime ─► staging | prod
        └──────────────────► dev ───► test
```
| Target | Purpose |
|---|---|
| `deps` | third-party wheels only; manifests are **bind-mounted**, so it rebuilds only when `uv.lock`/a `pyproject.toml` changes |
| `builder` | workspace members built per project under their `lld.env`; `.so` files stripped; vendored test dirs removed |
| `runtime` | `python:slim` + `/opt/venv` + alembic files; non-root uid 10001; pip removed; exec-form `CMD` (SIGTERM reaches uvicorn); OCI labels (`VERSION`, `GIT_SHA`) |
| `staging` | runtime + `RIO_ENVIRONMENT=staging`, docs + playground on (QA) |
| `prod` | runtime + `RIO_ENVIRONMENT=production`, docs off, **playground off (enforced by settings)** |
| `dev` | fat image with dev tools, `--reload` |
| `test` | `docker build --target test .` runs ruff, `mypy --strict` and pytest inside the image |

### Optimisations in place
* BuildKit cache mounts for apt, uv and the ThinLTO cache; bind-mounted manifests (no COPY layers for lock data).
* Strict `.dockerignore` allow-list (context is a few hundred KB, not the whole repo).
* Layer order: toolchain -> deps -> sources, so source edits never recompile dependencies.
* lld + ThinLTO + `--gc-sections --icf=safe` + `strip` for native code; bytecode precompiled (`UV_COMPILE_BYTECODE`).
* No compilers, uv, pip or tests in the runtime image; `read_only` rootfs, `cap_drop: ALL`, `no-new-privileges` in compose.
* `init: true` + `stop_grace_period` > uvicorn graceful shutdown; HEALTHCHECK uses the stdlib only.
* `docker-bake.hcl`: multi-arch (amd64/arm64), SBOM + provenance attestations, registry/GHA cache.
* CI budgets: image < 200 MB and runs as uid 10001; the pipeline fails otherwise.

## Commands
```bash
scripts/docker.sh dev up                       # hot reload, bind-mounted source
RIO_SECRET_KEY=$(openssl rand -hex 32) scripts/docker.sh staging up
scripts/docker.sh staging size                 # image sizes
docker buildx bake test                        # gate inside the image
VERSION=1.2.3 GIT_SHA=$(git rev-parse HEAD) docker buildx bake release --push
```
`api` starts only after the one-shot `migrate` service succeeds.

## Environment & secrets
See `.env.example` and [secrets.md](secrets.md). Staging/production values live in **encrypted** `.env.staging` /
`.env.production`; `scripts/docker.sh <env> ...` decrypts them on the host (`dotenvx run`) so the image carries no
secrets and no dotenvx. Provide `DOTENV_PRIVATE_KEY_<ENV>` from your secret manager. Required outside dev:
`RIO_SECRET_KEY`, `RIO_DATABASE_URL`/`POSTGRES_PASSWORD`.
Behind a proxy: `FORWARDED_ALLOW_IPS`, `RIO_ALLOWED_HOSTS`, `RIO_PUBLIC_URL` (advertised in OpenAPI `servers`).

## Promotion
CI builds `staging` on every relevant PR (see `.github/workflows/ci.yml`). Promote the **same digest** staging -> prod;
only env vars differ.

> The image build itself could not be executed in the authoring sandbox (no Docker daemon). The builder commands were
> run locally step by step, compose files were validated with `docker compose config`, and CI builds and smoke-tests
> the image on every push.
