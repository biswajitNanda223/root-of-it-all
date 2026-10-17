# ADR 0009 - One app per project, database per service, shared packages
Status: accepted
**Context** The monorepo must host different projects without coupling them. **Decision** Each deployable is a full app
under `apps/` with its own database, declarative `Base`/`MetaData`, Alembic environment (own version table), settings
(own DB env var) and DI composition root; code reuse happens only through `packages/*`. Services talk through ports
(HTTP adapters), authenticate users with stateless JWTs from the identity service and each other with a service key.
**Consequences** Independent deploy/scale/migrate; no cross-service transactions - use saga + idempotent reservations +
transactional outbox; shared packages are the one place where a change fans out (CI builds every dependent app).
