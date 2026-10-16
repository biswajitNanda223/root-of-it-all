# ADR 0004 – Async SQLAlchemy 2 + Alembic
Status: accepted
**Decision** asyncpg in prod, aiosqlite in dev/test, one transaction per request, Alembic as the only prod
schema mechanism with CI drift check. **Consequences** Dialect differences must be watched; SQLite uses batch mode.
