# Deployment & Docker

## Image targets (one Dockerfile)
| Target | Purpose | Notes |
|---|---|---|
| `toolchain` | clang, lld, uv | build-only |
| `deps` → `builder` | cached dependency layer, then app install (`--no-editable`) | cache mounts for apt + uv |
| `dev` | full venv incl. dev tools, `--reload` | bind-mount source |
| `runtime` | `python:slim` + `/opt/venv` + alembic files, non-root uid 10001 | no compilers, no uv |
| `staging` | runtime + `RIO_ENVIRONMENT=staging`, docs on | same bits as prod |
| `prod` | runtime + `RIO_ENVIRONMENT=production`, docs off | |

Staging is deliberately the *same slim image shape* as prod so it validates what will ship.

## Compose
`compose.yaml` (db, one-shot `migrate`, api) + an override per environment:
```bash
scripts/docker.sh dev up                 # hot reload
RIO_SECRET_KEY=$(openssl rand -hex 32) scripts/docker.sh staging up
scripts/docker.sh prod build
scripts/docker.sh staging logs
```
`api` starts only after `migrate` completes. Staging/prod run read-only, all caps dropped, `no-new-privileges`,
memory limits.

## Environment variables
See `.env.example`. Required outside dev: `RIO_SECRET_KEY`, `RIO_DATABASE_URL`, `POSTGRES_PASSWORD` (compose).

## Promotion
CI builds `staging` on every PR (smoke test) and publishes on tags. Promote the **same digest**
staging → prod; only env vars differ.

## Running without Docker
`scripts/migrate.sh && scripts/start.sh` behind a reverse proxy (set `FORWARDED_ALLOW_IPS`).
