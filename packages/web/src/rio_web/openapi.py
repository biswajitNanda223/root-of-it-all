from __future__ import annotations

import re

from fastapi.routing import APIRoute


def operation_id(route: APIRoute) -> str:
    """`items-create_item` style ids: stable, readable, and good for generated clients."""
    tag = re.sub(r"[^a-z0-9]+", "_", str(route.tags[0] if route.tags else "default").lower()).strip(
        "_"
    )
    return f"{tag}-{route.name}"
