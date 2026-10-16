# syntax=docker/dockerfile:1.9
# Monorepo build. Targets: dev | test | staging | prod      (see docker-bake.hcl and docs/deployment.md)
#
#   toolchain ──► deps ──► builder ──► runtime ──► staging | prod       (slim, non-root, no compilers)
#        └──────► dev ──► test                                          (fat, tests + dev tools)
ARG PYTHON_VERSION=3.13

# ============================================================ toolchain
FROM python:${PYTHON_VERSION}-slim-bookworm AS toolchain
SHELL ["/bin/bash", "-euo", "pipefail", "-c"]
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/
# clang + lld + binutils(strip). Build-only: never copied into runtime.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential clang lld
ARG LLD_PROFILE=release
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/opt/venv \
    LLD_PROFILE=${LLD_PROFILE} LLD_CACHE_DIR=/cache/lld ROOT=/workspace
WORKDIR /workspace
# Layered lld env (repo -> profile -> project) - the same files developers use locally.
COPY tooling/lld tooling/lld

# ================================================================= deps
# Third-party wheels only. Manifests are bind-mounted (no COPY layer), so this layer is rebuilt only
# when a pyproject.toml or the lockfile changes - never for source edits.
FROM toolchain AS deps
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/cache/lld \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=apps/api/pyproject.toml,target=apps/api/pyproject.toml \
    --mount=type=bind,source=packages/core/pyproject.toml,target=packages/core/pyproject.toml \
    --mount=type=bind,source=packages/db/pyproject.toml,target=packages/db/pyproject.toml \
    --mount=type=bind,source=packages/native/pyproject.toml,target=packages/native/pyproject.toml \
    . tooling/lld/load.sh "" "$LLD_PROFILE" \
    && uv sync --frozen --no-dev --no-install-workspace --package api

# =============================================================== builder
# Workspace members, built per project: each one sees its own lld.env (e.g. packages/native hides symbols).
FROM deps AS builder
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/src apps/api/src
COPY packages/core packages/core
COPY packages/db packages/db
COPY packages/native packages/native
COPY apps/api/lld.env apps/api/lld.env
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/cache/lld \
    ( . tooling/lld/load.sh packages/native "$LLD_PROFILE" \
      && uv sync --frozen --no-dev --no-editable --inexact --package rio-native ) \
    && ( . tooling/lld/load.sh apps/api "$LLD_PROFILE" \
      && uv sync --frozen --no-dev --no-editable --package api ) \
    && find /opt/venv -name '*.so*' -type f -exec strip --strip-unneeded {} + \
    && find /opt/venv -depth -type d \( -name tests -o -name test \) -path '*/site-packages/*' -exec rm -rf {} +

# ===================================================================== dev
FROM toolchain AS dev
ENV LLD_PROFILE=dev PATH="/opt/venv/bin:$PATH" RIO_ENVIRONMENT=development
COPY pyproject.toml uv.lock ./
COPY apps apps
COPY packages packages
RUN --mount=type=cache,target=/root/.cache/uv \
    . tooling/lld/load.sh packages/native dev && uv sync --frozen --package api
EXPOSE 8000
CMD ["uvicorn", "app.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "apps/api/src", "--reload-dir", "packages"]

# ==================================================================== test
# `docker build --target test .` == run the whole gate inside the image (lint, types, tests).
FROM dev AS test
COPY scripts scripts
RUN uv run --frozen ruff check . && uv run --frozen mypy apps/api/src packages/core/src packages/db/src packages/native/src \
    && uv run --frozen pytest -q

# ================================================================= runtime
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ARG VERSION=0.0.0
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.title="rio-api" \
      org.opencontainers.image.source="https://github.com/biswajitNanda223/root-of-it-all" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}"
# Non-root user; drop pip (not needed at runtime, smaller attack surface and ~10 MB).
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && python -m pip uninstall -y pip >/dev/null 2>&1 || true
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app apps/api/alembic.ini /app/alembic.ini
COPY --chown=app:app apps/api/migrations /app/migrations
WORKDIR /app
# uvicorn reads WEB_CONCURRENCY / FORWARDED_ALLOW_IPS itself, so CMD stays exec-form (PID 1 gets SIGTERM).
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=random \
    RIO_LOG_JSON=true WEB_CONCURRENCY=2
USER app
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u,sys; sys.exit(u.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status != 200)"]
CMD ["uvicorn", "app.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header", "--timeout-graceful-shutdown", "20"]

FROM runtime AS staging
ENV RIO_ENVIRONMENT=staging RIO_DOCS_ENABLED=true

FROM runtime AS prod
ENV RIO_ENVIRONMENT=production RIO_DOCS_ENABLED=false RIO_PLAYGROUND_ENABLED=false
