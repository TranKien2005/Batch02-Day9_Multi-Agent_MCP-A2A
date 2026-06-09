"""Local web dashboard server for the Stage 5 A2A demo.

Run with:
    .\.venv\Scripts\python.exe demo_server.py

Then open:
    http://localhost:8080
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from uuid import uuid4

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse

from common.security import auth_headers

load_dotenv()

ROOT = Path(__file__).resolve().parent
HTML_FILE = ROOT / "docs" / "agent_interaction_demo.html"
CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")
DEFAULT_QUESTION = (
    "If a company breaks a $2M contract, avoids taxes, and faces revenue loss, "
    "what are the legal, regulatory, tax, and financial consequences?"
)

SERVICES = {
    "registry": "http://localhost:10000",
    "customer": "http://localhost:10100",
    "law": "http://localhost:10101",
    "tax": "http://localhost:10102",
    "compliance": "http://localhost:10103",
    "financial": "http://localhost:10104",
}

app = FastAPI(title="Stage 5 A2A Demo Dashboard", version="1.0.0")


def log(message: str) -> None:
    """Print progress immediately so long A2A requests do not look frozen."""
    print(f"[demo_server] {message}", flush=True)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(HTML_FILE)


@app.get("/api/latency")
async def measure_latency(
    slot: str = Query("baseline", pattern="^(baseline|optimized|current)$"),
    question: str = DEFAULT_QUESTION,
) -> dict:
    """Measure one real end-to-end request against the running Customer Agent."""
    from a2a.client import A2AClient
    from a2a.types import AgentCard, Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart

    log(f"latency measurement started: slot={slot}, customer={CUSTOMER_AGENT_URL}")
    log("fetching Customer Agent card...")
    async with httpx.AsyncClient(timeout=300.0, headers=auth_headers()) as http_client:
        card_resp = await http_client.get(f"{CUSTOMER_AGENT_URL}/.well-known/agent.json")
        card_resp.raise_for_status()
        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)
        log(f"connected to agent card: {agent_card.name} v{agent_card.version}")

        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=question))],
            message_id=str(uuid4()),
            context_id=str(uuid4()),
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(message=message),
        )

        start = time.perf_counter()
        log("sending A2A message; waiting for agent chain and LLM response...")
        response = await client.send_message(request)
        elapsed = time.perf_counter() - start
        log(f"A2A response received in {elapsed:.3f}s")

    answer = _extract_text(response)
    log(f"extracted response text: {len(answer)} chars")
    return {
        "slot": slot,
        "seconds": round(elapsed, 3),
        "response_chars": len(answer),
        "preview": answer[:600],
        "customer_agent_url": CUSTOMER_AGENT_URL,
    }


@app.get("/api/metrics")
async def collect_metrics() -> dict:
    """Fetch metrics text from all running local Stage 5 services."""
    results: dict[str, dict[str, str | bool]] = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, base_url in SERVICES.items():
            try:
                resp = await client.get(f"{base_url}/metrics")
                resp.raise_for_status()
                results[name] = {"ok": True, "metrics": resp.text}
            except Exception as exc:
                results[name] = {"ok": False, "metrics": str(exc)}
    return results


def _extract_text(response: object) -> str:
    if hasattr(response, "root"):
        response = response.root
    result = getattr(response, "result", None)
    if result is None:
        return ""

    text = ""
    for artifact in getattr(result, "artifacts", []) or []:
        for part in getattr(artifact, "parts", []) or []:
            text += _part_text(part)
    if text:
        return text

    for part in getattr(result, "parts", []) or []:
        text += _part_text(part)
    return text


def _part_text(part: object) -> str:
    inner = getattr(part, "root", part)
    return getattr(inner, "text", "") or ""


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
