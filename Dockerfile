# syntax=docker/dockerfile:1.9
# One Dockerfile for EVERY service in the monorepo (api, catalog, orders, ...).
#   docker build --target staging --build-arg SERVICE=catalog --build-arg SERVICE_MODULE=catalog_service.main:app_factory \
#                --build-arg SERVICE_PORT=8001 .
# Build args come from apps/<svc>/pyproject.toml [tool.rio.service] (see docker-bake.hcl / compose.yaml, both generated).
# Targets: dev | test | staging | prod
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
# Third-party wheels of ONE service. Manifests are bind-mounted (no COPY layer), so this layer is rebuilt only when
# uv.lock or a pyproject.toml changes - never for source edits, and never for another service's changes.
FROM toolchain AS deps
ARG SERVICE=api
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/cache/lld \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=apps/${SERVICE}/pyproject.toml,target=apps/${SERVICE}/pyproject.toml \
# >>> generated: package manifests (tooling/service.py)
    --mount=type=bind,source=packages/auth/pyproject.toml,target=packages/auth/pyproject.toml \
    --mount=type=bind,source=packages/core/pyproject.toml,target=packages/core/pyproject.toml \
    --mount=type=bind,source=packages/db/pyproject.toml,target=packages/db/pyproject.toml \
    --mount=type=bind,source=packages/native/pyproject.toml,target=packages/native/pyproject.toml \
    --mount=type=bind,source=packages/web/pyproject.toml,target=packages/web/pyproject.toml \
# <<< generated
    . tooling/lld/load.sh "" "$LLD_PROFILE" \
    && uv sync --frozen --no-dev --no-install-workspace --package "$SERVICE"

# =============================================================== builder
# Shared packages + this service, built under the layered lld env: repo -> profile -> packages/native -> this service.
FROM deps AS builder
ARG SERVICE=api
COPY pyproject.toml uv.lock ./
COPY packages packages
COPY apps/${SERVICE} apps/${SERVICE}
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/cache/lld \
    . tooling/lld/load.sh "packages/native:apps/${SERVICE}" "$LLD_PROFILE" \
    && uv sync --frozen --no-dev --no-editable --package "$SERVICE" \
    # shrink: drop debug symbols from compiled extensions, delete test suites shipped by dependencies
    && find /opt/venv -name '*.so*' -type f -exec strip --strip-unneeded {} + \
    && find /opt/venv -depth -type d \( -name tests -o -name test \) -path '*/site-packages/*' -exec rm -rf {} +

# ===================================================================== dev
FROM toolchain AS dev
ARG SERVICE=api
ARG SERVICE_MODULE=app.main:app_factory
ARG SERVICE_PORT=8000
ENV LLD_PROFILE=dev PATH="/opt/venv/bin:$PATH" RIO_ENVIRONMENT=development \
    SERVICE=${SERVICE} SERVICE_MODULE=${SERVICE_MODULE} PORT=${SERVICE_PORT}
COPY pyproject.toml uv.lock ./
COPY apps apps
COPY packages packages
RUN --mount=type=cache,target=/root/.cache/uv \
    . tooling/lld/load.sh packages/native dev && uv sync --frozen
EXPOSE ${SERVICE_PORT}
CMD ["sh", "-c", "exec uvicorn \"$SERVICE_MODULE\" --factory --host 0.0.0.0 --port \"$PORT\" --reload --reload-dir \"apps/$SERVICE/src\" --reload-dir packages"]

# ==================================================================== test
# `docker build --target test .` == run the whole gate inside the image (lint, types, tests for ALL services).
FROM dev AS test
COPY tests tests
COPY scripts scripts
RUN uv run --frozen ruff check . \
    && uv run --frozen mypy apps/*/src packages/*/src \
    && uv run --frozen pytest -q

# ================================================================= runtime
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ARG SERVICE=api
ARG SERVICE_MODULE=app.main:app_factory
ARG SERVICE_PORT=8000
ARG VERSION=0.0.0
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.title="rio-${SERVICE}" \
      org.opencontainers.image.source="https://github.com/biswajitNanda223/root-of-it-all" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}"
# Non-root user; drop pip (not needed at runtime, smaller attack surface and ~10 MB).
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && python -m pip uninstall -y pip >/dev/null 2>&1 || true
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=app:app /workspace/apps/${SERVICE}/alembic.ini /app/alembic.ini
COPY --from=builder --chown=app:app /workspace/apps/${SERVICE}/migrations /app/migrations
WORKDIR /app
# uvicorn reads WEB_CONCURRENCY / FORWARDED_ALLOW_IPS itself; `exec` makes uvicorn PID 1 so SIGTERM reaches it.
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=random \
    RIO_LOG_JSON=true WEB_CONCURRENCY=2 SERVICE_MODULE=${SERVICE_MODULE} PORT=${SERVICE_PORT}
USER app
EXPOSE ${SERVICE_PORT}
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os,sys,urllib.request as u; sys.exit(u.urlopen('http://127.0.0.1:%s/health/live' % os.environ['PORT'], timeout=2).status != 200)"
CMD ["sh", "-c", "exec uvicorn \"$SERVICE_MODULE\" --factory --host 0.0.0.0 --port \"$PORT\" --proxy-headers --no-server-header --timeout-graceful-shutdown 20"]

FROM runtime AS staging
ENV RIO_ENVIRONMENT=staging RIO_DOCS_ENABLED=true

FROM runtime AS prod
ENV RIO_ENVIRONMENT=production RIO_DOCS_ENABLED=false RIO_PLAYGROUND_ENABLED=false
