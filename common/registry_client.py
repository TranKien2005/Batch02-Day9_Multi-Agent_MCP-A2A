"""Registry client helpers with lightweight retry.

Provides `discover(task)` to look up an agent endpoint from the registry,
and `register(agent_info)` for agents to self-register on startup.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:10000")
logger = logging.getLogger(__name__)

T = TypeVar("T")


async def discover(task: str) -> str:
    """Return the endpoint URL of the agent that handles the given task."""
    async def _request() -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{REGISTRY_URL}/discover/{task}")
            resp.raise_for_status()
            return resp.json()["endpoint"]

    return await _with_retry(_request, label=f"discover({task})")


async def register(agent_info: dict) -> None:
    """Register an agent with the registry."""
    async def _request() -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{REGISTRY_URL}/register", json=agent_info)
            resp.raise_for_status()

    await _with_retry(_request, label=f"register({agent_info.get('agent_name', 'agent')})")


async def _with_retry(operation: Callable[[], Awaitable[T]], label: str) -> T:
    attempts = int(os.getenv("REGISTRY_RETRY_ATTEMPTS", "3"))
    base_delay = float(os.getenv("REGISTRY_RETRY_BASE_DELAY", "0.25"))
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise
            last_exc = exc
        except Exception as exc:
            last_exc = exc

        if attempt < attempts:
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Registry %s failed on attempt %d/%d: %s; retrying in %.2fs",
                label,
                attempt,
                attempts,
                last_exc,
                delay,
            )
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
