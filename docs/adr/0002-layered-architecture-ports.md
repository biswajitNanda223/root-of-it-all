# ADR 0002 – Layered architecture with ports
Status: accepted
**Context** Keep business rules testable and storage swappable. **Decision** domain/services/infrastructure/api
with Protocol ports and constructor injection; FastAPI `Depends` is the composition root.
**Consequences** More files than a flat CRUD app; unit tests need no DB or HTTP.
