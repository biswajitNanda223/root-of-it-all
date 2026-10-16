# syntax=docker/dockerfile:1.9
# Multi-stage, monorepo-aware build. Targets: dev | staging | prod
#   docker build --target staging -t rio-api:staging .
ARG PYTHON_VERSION=3.13

# --------------------------------------------------------------- toolchain
FROM python:${PYTHON_VERSION}-slim-bookworm AS toolchain
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/
# clang + lld: fast linking when a dependency has to compile native code.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends build-essential clang lld
ENV CC=clang CXX=clang++ LDFLAGS="-fuse-ld=lld" \
    RUSTFLAGS="-C link-arg=-fuse-ld=lld" \
    UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /workspace

# ------------------------------------------------------------ deps (cached)
# Only manifests + lockfile: this layer survives source edits.
FROM toolchain AS deps
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/
COPY packages/core/pyproject.toml packages/core/
COPY packages/db/pyproject.toml packages/db/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace --package api

# ----------------------------------------------------------------- builder
FROM deps AS builder
COPY apps/api apps/api
COPY packages packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package api

# --------------------------------------------------------------------- dev
FROM toolchain AS dev
COPY pyproject.toml uv.lock ./
COPY apps apps
COPY packages packages
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --package api
ENV PATH="/opt/venv/bin:$PATH" RIO_ENVIRONMENT=development
EXPOSE 8000
CMD ["uvicorn", "app.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "apps/api/src", "--reload-dir", "packages"]

# ---------------------------------------------------- runtime (staging/prod)
# No compilers, no uv, no source tree: just Python + the prebuilt venv.
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app
COPY --from=builder --chown=app:app /opt/venv /opt/venv
COPY --chown=app:app apps/api/alembic.ini /app/alembic.ini
COPY --chown=app:app apps/api/migrations /app/migrations
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    RIO_LOG_JSON=true WEB_CONCURRENCY=2
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status==200 else 1)"]
CMD ["sh", "-c", "exec uvicorn app.main:app_factory --factory --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY} --proxy-headers --forwarded-allow-ips='*'"]

FROM runtime AS staging
ENV RIO_ENVIRONMENT=staging RIO_DOCS_ENABLED=true

FROM runtime AS prod
ENV RIO_ENVIRONMENT=production RIO_DOCS_ENABLED=false
