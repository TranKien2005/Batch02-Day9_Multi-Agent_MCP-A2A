"""Collect Prometheus-style metrics from all local Stage 5 services."""

from __future__ import annotations

import asyncio

import httpx

SERVICES = {
    "registry": "http://localhost:10000",
    "customer": "http://localhost:10100",
    "law": "http://localhost:10101",
    "tax": "http://localhost:10102",
    "compliance": "http://localhost:10103",
    "financial": "http://localhost:10104",
}


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, base_url in SERVICES.items():
            print("=" * 70)
            print(f"{name}: {base_url}/metrics")
            try:
                resp = await client.get(f"{base_url}/metrics")
                resp.raise_for_status()
                print(resp.text.strip())
            except Exception as exc:
                print(f"unavailable: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
