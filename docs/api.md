# API guide

* Swagger UI `/docs` · ReDoc `/redoc` · schema `/openapi.json` (disabled with `RIO_DOCS_ENABLED=false`)
* Committed contract: [`docs/openapi.json`](openapi.json) (`scripts/export-openapi.sh`; CI fails if stale)
* Mounted sub-app docs: `/subapi/docs`

## Using Swagger
1. `POST /api/v1/auth/register`, then click **Authorize** and log in with the email as *username*.
   The token persists across reloads (`persistAuthorization`).
2. Playground security demos have their own *Authorize* entries: `PlaygroundApiKey` (`demo-key`), `PlaygroundBasic`
   (`demo`/`demo`), `PlaygroundScopes` (`demo`/`demo`, tick scopes).
3. Operation ids are `<tag>-<function>` (e.g. `items-create_item`) - stable names for generated clients.

## Core API (`/api/v1`)
| Endpoint | Auth | Notes |
|---|---|---|
| `GET /health/live`, `/health/ready` | - | probes (ready -> 503 if the DB is down) |
| `POST /auth/register`, `/auth/token` | - | 201 / 409; OAuth2 password form -> JWT |
| `GET /users/me`, `GET /users` | user / superuser | paginated list |
| `GET/POST /items`, `GET/PATCH/DELETE /items/{id}` | user | owner-scoped |
| `POST /files` | user | streamed, 413 over `RIO_MAX_UPLOAD_BYTES`; response includes `fnv1a64` from the C extension |
| `GET /stream/ticks`, `WS /ws/echo` | - | SSE / WebSocket |

## Playground (`/api/v1/playground`, off in production)
| Group | What it demonstrates |
|---|---|
| `params` | path/query/header/cookie, enums, `:path`, constraints, aliases, lists, parameter models |
| `bodies` | nested, multiple, embedded, discriminated union, In/Out models, PUT vs PATCH |
| `responses` | status codes, headers, cookies, HTML/text/XML, redirect, CSV streaming, documented extra responses |
| `forms` | form fields/models, bytes, `UploadFile`, multi-file |
| `errors` | `HTTPException`, domain errors, custom exception handler, sanitized 500 |
| `deps` | class / sub / parametrised / yield / router-level dependencies |
| `security` | API key, HTTP Basic, OAuth2 scopes |
| `advanced` | `Request`, custom route class, deprecated/hidden/operationId, background tasks, Jinja2, WebSocket rooms |
| `shop` | **end-to-end flow** (below) |

### Shop flow (end-to-end)
```
POST /shop/products          create (sku pattern, Decimal price, 409 on duplicate sku)
GET  /shop/products          ?q=&min_price=&max_price=&in_stock=&sort=-price&limit=&offset=
PUT|PATCH|DELETE /shop/products/{id}
POST /shop/orders            reserves stock all-or-nothing; `Idempotency-Key` header replays safely
POST /shop/orders/{id}/pay   pending -> paid; background task emits the `order-paid` webhook
POST /shop/orders/{id}/cancel  pending -> cancelled; restocks
GET  /shop/orders/{id}/events  timeline as SSE      GET /shop/orders/export.csv  streaming CSV
POST /shop/_reset            wipe the in-memory store
```
`create_order` documents an OpenAPI **callback** (`callback_url`) and the app documents a **webhook** `order-paid`;
both are documentation-only (the demo never makes outbound HTTP, so a public sandbox cannot be used for SSRF).

## Errors
`application/problem+json`: `{type,title,status,detail,request_id}`; 422 adds `errors: [{type,loc,msg}]`
(inputs are stripped so secrets in bad requests are not echoed). Unhandled exceptions return a sanitized 500.
