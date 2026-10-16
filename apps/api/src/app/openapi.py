"""OpenAPI presentation: metadata, tag docs and stable operation ids."""

from __future__ import annotations

import re
from typing import Any

from fastapi.routing import APIRoute

DESCRIPTION = """
Production-grade **FastAPI** reference service.

## Quick tour
1. `POST /api/v1/auth/register` then `POST /api/v1/auth/token` - use **Authorize** (top right) with the email as *username*.
2. Try `items` (owner-scoped CRUD with pagination), `files` (streamed uploads), `realtime` (SSE / WebSocket).
3. Explore the **playground** groups: one dummy API per FastAPI docs topic, plus an end-to-end *shop*
   (products → orders → pay → events) that also documents **callbacks** and **webhooks**.

## Conventions
* Errors are `application/problem+json` (RFC 7807) and carry the `X-Request-ID` as `request_id`.
* Lists are paginated with `limit` (1-100) and `offset`; responses are `{items,total,limit,offset}`.
* Every response carries `X-Request-ID` and `X-Process-Time-Ms`.
"""

TAGS: list[dict[str, Any]] = [
    {"name": "health", "description": "Liveness and readiness probes (outside `/api/v1`)."},
    {
        "name": "auth",
        "description": "Registration and OAuth2 password-flow tokens.",
        "externalDocs": {
            "description": "FastAPI: OAuth2 + JWT",
            "url": "https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/",
        },
    },
    {"name": "users", "description": "User profile and administration."},
    {"name": "items", "description": "Owner-scoped CRUD with pagination."},
    {"name": "files", "description": "Streaming, size-capped uploads."},
    {"name": "realtime", "description": "Server-Sent Events and WebSocket examples."},
]


def operation_id(route: APIRoute) -> str:
    """`items-create_item` style ids: stable, readable, and good for generated clients."""
    tag = re.sub(r"[^a-z0-9]+", "_", str(route.tags[0] if route.tags else "default").lower()).strip(
        "_"
    )
    return f"{tag}-{route.name}"


CONTACT = {"name": "Platform team", "url": "https://github.com/biswajitNanda223/root-of-it-all"}
TERMS = "https://github.com/biswajitNanda223/root-of-it-all/blob/main/SECURITY.md"
SWAGGER_UI: dict[str, Any] = {
    "persistAuthorization": True,
    "displayRequestDuration": True,
    "filter": True,
    "tryItOutEnabled": True,
    "docExpansion": "list",
    "defaultModelsExpandDepth": 0,
}
