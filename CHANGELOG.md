# Changelog
## 0.3.0
- **dotenvx**: encrypted `.env.staging|production|ci`, plaintext `.env.development`, `scripts/env.sh` (init/set/get/decrypt/encrypt/check/run), automatic decryption in dev/start/migrate/docker scripts, hygiene hook + CI check, mise tool pin, docs/secrets.md, ADR 0008.

## 0.2.0
- **lld**: layered toolchain (`tooling/lld`: base -> dev/release -> per-project), `LDSHARED` fix, `lld-doctor.sh`, `native.sh`; new `packages/native` C extension (ThinLTO, ICF, GC, hidden symbols), used by uploads.
- **Git**: Conventional Commits hook, secret scan, shellcheck, migration-drift, no-commit-to-main, affected-only pre-push; CI mirrors them; `tooling/affected.py`.
- **Docker**: bind-mounted manifests, per-project lld in builder, strip, cache mounts (apt/uv/ThinLTO), allow-list `.dockerignore`, `test` target, bake file (multi-arch, SBOM, provenance), `init`, graceful shutdown, image-size/non-root CI budgets.
- **FastAPI/Swagger**: playground covering the whole docs (params, bodies, responses, forms, errors, deps, security/scopes, advanced, webhooks, callbacks, mounts, templates, WebSockets) + end-to-end shop; richer OpenAPI (description, contact, stable operation ids, examples, 422 problem+json, tags); committed `docs/openapi.json`.
- Docs: coverage map, lld, git workflow, deployment, API guide.

## 0.1.0
- Initial monorepo: uv workspace, FastAPI service, shared packages, Alembic, scripts, mise, Docker (dev/staging/prod), CI, docs, BMAD artifacts.
