"""`uv run python -m app` - convenience entry point."""

import uvicorn

from rio_core.config import get_settings


def main() -> None:
    s = get_settings()
    uvicorn.run(
        "app.main:app_factory",
        factory=True,
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=s.environment == "development",
        log_config=None,
    )


if __name__ == "__main__":
    main()
