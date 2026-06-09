"""Optional API-key authentication helpers for A2A services."""

from __future__ import annotations

import os
from collections.abc import Iterable

from fastapi import Request
from fastapi.responses import JSONResponse

AUTH_HEADER = "X-A2A-API-Key"
API_KEY_ENV = "A2A_API_KEY"


def get_api_key() -> str:
    """Return the configured A2A API key, or an empty string when auth is disabled."""
    return os.getenv(API_KEY_ENV, "").strip()


def auth_headers() -> dict[str, str]:
    """Headers clients should send to authenticated A2A endpoints."""
    api_key = get_api_key()
    return {AUTH_HEADER: api_key} if api_key else {}


def add_api_key_middleware(app, public_paths: Iterable[str] | None = None) -> None:
    """Protect A2A request endpoints when A2A_API_KEY is configured.

    Agent Cards remain public so discovery can still fetch `/.well-known/agent.json`.
    Auth is disabled by default to keep the codelab easy to run.
    """
    public = set(public_paths or {"/.well-known/agent.json", "/health", "/metrics"})

    @app.middleware("http")
    async def api_key_auth(request: Request, call_next):
        api_key = get_api_key()
        if not api_key or request.url.path in public:
            return await call_next(request)

        if request.headers.get(AUTH_HEADER, "") != api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid A2A API key"},
            )

        return await call_next(request)
