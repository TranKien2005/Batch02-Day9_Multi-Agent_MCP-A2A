"""Measure end-to-end latency for Stage 5 Customer Agent requests."""

from __future__ import annotations

import asyncio
import os
import statistics
import time
from uuid import uuid4

import httpx
from dotenv import load_dotenv

from common.security import auth_headers

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")
DEFAULT_QUESTION = (
    "If a company breaks a $2M contract, avoids taxes, and faces revenue loss, "
    "what are the legal, regulatory, tax, and financial consequences?"
)


async def main() -> None:
    from a2a.client import A2AClient
    from a2a.types import AgentCard, Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart

    runs = int(os.getenv("LATENCY_RUNS", "1"))
    question = os.getenv("LATENCY_QUESTION", DEFAULT_QUESTION)
    timings: list[float] = []

    async with httpx.AsyncClient(timeout=300.0, headers=auth_headers()) as http_client:
        card_resp = await http_client.get(f"{CUSTOMER_AGENT_URL}/.well-known/agent.json")
        card_resp.raise_for_status()
        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        for run in range(1, runs + 1):
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
            response = await client.send_message(request)
            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            answer = _extract_text(response)
            print(f"Run {run}: {elapsed:.2f}s, response_chars={len(answer)}")

    print("=" * 60)
    print(f"runs={runs}")
    print(f"min={min(timings):.2f}s")
    print(f"max={max(timings):.2f}s")
    print(f"avg={statistics.mean(timings):.2f}s")
    if len(timings) > 1:
        print(f"median={statistics.median(timings):.2f}s")


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
    asyncio.run(main())
