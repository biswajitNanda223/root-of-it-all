# API guide
Interactive docs: `/docs` (Swagger) and `/redoc` — disabled when `RIO_DOCS_ENABLED=false`.
Contract snapshot: `scripts/export-openapi.sh` → `docs/openapi.json`.

| Method & path | Auth | Notes |
|---|---|---|
| `GET /health/live`, `/health/ready` | – | probes (ready → 503 if DB down) |
| `POST /api/v1/auth/register` | – | 201; 409 on duplicate; welcome mail via BackgroundTasks |
| `POST /api/v1/auth/token` | – | form: `username`(email), `password` → bearer JWT |
| `GET /api/v1/users/me` | user | |
| `GET /api/v1/users` | superuser | paginated |
| `GET/POST /api/v1/items`, `GET/PATCH/DELETE /api/v1/items/{id}` | user | owner-scoped; superuser may access all |
| `POST /api/v1/files` | user | multipart, streamed, 413 over `RIO_MAX_UPLOAD_BYTES` |
| `GET /api/v1/stream/ticks` | – | SSE |
| `WS /api/v1/ws/echo` | – | echo |

Errors are `application/problem+json`: `{type,title,status,detail,request_id}`.
Pagination: `?limit=1..100&offset=0` → `{items,total,limit,offset}`.
