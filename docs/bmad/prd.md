# PRD – root-of-it-all platform template

## Functional requirements
- FR1 Users can register and obtain an OAuth2 bearer token.
- FR2 Authenticated users CRUD their own items with pagination; superusers administer.
- FR3 Upload files with size limits; stream events (SSE) and bidirectional messages (WebSocket).
- FR4 Probes for liveness/readiness.
- FR5 Machine-readable API contract (OpenAPI) exported to the repo.

## Non-functional requirements
- NFR1 Typed (mypy strict) and linted; ≥ 85 % coverage gate.
- NFR2 12-factor config, secrets never in image; prod refuses insecure defaults.
- NFR3 Reproducible: single lockfile, `--frozen` builds.
- NFR4 Light images: slim runtime, no toolchain; non-root, read-only FS.
- NFR5 Observability: structured logs with request ids.
- NFR7 Native code links with lld using layered, per-project profiles; verified in CI.
- NFR8 Commit hygiene enforced locally and in CI; CI scoped to affected projects.
- NFR6 Every developer action available as `scripts/*.sh` and a mise task.

## Epics
| # | Epic | Stories |
|---|---|---|
| E1 | Foundation & tooling | 1.1 workspace, 1.2 scripts/mise, 1.3 CI |
| E2 | Identity | 2.1 register/login, 2.2 authorization |
| E3 | Items domain | 3.1 CRUD, 3.2 pagination |
| E4 | Platform | 4.1 Docker/compose, 4.2 migrations, 4.3 observability |
| E5 | Realtime & files | 5.1 uploads, 5.2 SSE/WS |

| E6 | Playground | 6.1 docs-topic coverage, 6.2 shop E2E, 6.3 OpenAPI quality |
| E7 | Toolchain | 7.1 lld layers + native ext, 7.2 commit checks, 7.3 Docker optimisation |

Status: E1–E5 in v0.1.0; E6–E7 in v0.2.0. Next candidates: refresh tokens, rate limiting, worker app, OpenTelemetry.
