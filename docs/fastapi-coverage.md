# FastAPI documentation coverage map

Every topic of the official docs (<https://fastapi.tiangolo.com>) has a runnable example. Core service code lives in
`apps/api/src/app/api/`; the *playground* (`apps/api/src/app/playground/`, `/api/v1/playground/*`, toggled by
`RIO_PLAYGROUND_ENABLED`, **forbidden in production**) is one dummy API per topic. Tests: `apps/api/tests/integration/`.

## Tutorial - user guide
| Docs topic | Where |
|---|---|
| First steps, path operations | `api/v1/*`, `playground/params.py` |
| Path parameters, enums, path convertor (`:path`) | `params.py::path_param`, `enum_param`, `file_path` |
| Query parameters, validation, aliases, lists, deprecated, hidden | `params.py::query_params` |
| Query / Header / Cookie parameter **models** | `params.py::query_model`, `header_model` |
| Request body, nested models, sets, `Field`, examples | `bodies.py::customer`, `models.py` |
| Multiple body params, `Body(embed=True)`, singular values | `bodies.py::multiple`, `embed` |
| Response model, `response_model` filtering (hide password) | `bodies.py::create_account` |
| Extra models (In/Out), union / discriminated unions | `models.py`, `bodies.py::pet` |
| Response status code, headers, cookies, `Response`, `JSONResponse`, HTML/Text/XML/Redirect/Streaming | `responses.py` |
| Form data & form models, `File`, `UploadFile`, multiple files | `forms.py`, `api/v1/files.py` |
| Handling errors, `HTTPException`, custom exceptions & handlers, overriding validation handler | `errors_demo.py`, `app/errors.py` |
| Path operation configuration (tags, summary, deprecated, operation_id, responses) | `app/openapi.py`, `advanced.py` |
| JSON-compatible encoder | `bodies.py::encode` |
| Body - updates (PUT vs PATCH, `exclude_unset`) | `bodies.py::put_prefs/patch_prefs`, `shop.py` |
| Dependencies: classes, sub-dependencies, parametrised, in decorators / router, **yield** | `dependencies_demo.py`, `api/deps.py` |
| Security: OAuth2 password + JWT, hashing | `api/v1/auth.py`, `infrastructure/security.py` |
| Security: API key, HTTP Basic, OAuth2 **scopes** | `playground/security_demo.py` |
| Middleware, CORS | `app/middleware.py`, `app/main.py` |
| SQL databases (async SQLAlchemy 2) | `packages/db`, `infrastructure/*` |
| Bigger applications (routers, `include_router`, versioning) | `api/router.py`, `playground/router.py` |
| Background tasks | `api/v1/auth.py`, `advanced.py`, `shop.py::pay_order` |
| Metadata & docs URLs, static files | `app/openapi.py`, `app/main.py`, `playground/router.py` |
| Testing (`TestClient`, dependency overrides, lifespan) | `apps/api/tests/` |
| Debugging | `RIO_DEBUG`, `scripts/dev.sh` |

## Advanced user guide
| Topic | Where |
|---|---|
| Additional status codes / responses, custom response classes | `responses.py` (`responses={...}`) |
| Return a response directly, custom headers | `responses.py::json_direct` |
| Advanced dependencies | `dependencies_demo.py::MaxSize` |
| Advanced security (scopes) | `security_demo.py` |
| Using the `Request` directly, `app.state`, `request.state` | `advanced.py::request_info` |
| Custom `APIRoute` class | `advanced.py::TimedRoute` |
| WebSockets (+ dependencies, rooms) | `api/v1/realtime.py`, `advanced.py::chat` |
| Lifespan events | `app/lifespan.py` |
| Server-Sent Events / streaming | `api/v1/realtime.py`, `shop.py::order_events` |
| Templates (Jinja2) | `advanced.py::page`, `templates/hello.html` |
| OpenAPI **callbacks** | `shop.py::create_order` (`callbacks=`) |
| OpenAPI **webhooks** | `playground/router.py` (`app.webhooks`) |
| Sub-applications / mounts | `playground/subapp.py` (`/subapi/docs`) |
| Behind a proxy (`root_path`, `servers`, proxy headers) | `RIO_PUBLIC_URL`, `scripts/start.sh` |
| Settings & env vars | `packages/core/.../config.py` |
| Testing WebSockets / events | `tests/integration/test_playground.py` |

## Deployment topics
Docker, workers, HTTPS-behind-proxy, health probes: `Dockerfile`, `compose*.yaml`, [deployment.md](deployment.md).
