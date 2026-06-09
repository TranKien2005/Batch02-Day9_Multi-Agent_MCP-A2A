"""Small client to demonstrate Customer Agent memory with one shared context_id."""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import httpx
from dotenv import load_dotenv

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")

QUESTIONS = [
    (
        "A company breaches a $2M contract, loses major customers, and also has "
        "tax exposure. What are the legal and financial risks?"
    ),
    "Based on the same company, what financial facts should counsel collect next?",
]


async def main() -> None:
    from a2a.client import A2AClient
    from a2a.types import AgentCard, Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart

    context_id = str(uuid4())
    print(f"Using shared context_id: {context_id}")

    async with httpx.AsyncClient(timeout=300.0) as http_client:
        card_resp = await http_client.get(f"{CUSTOMER_AGENT_URL}/.well-known/agent.json")
        card_resp.raise_for_status()
        agent_card = AgentCard.model_validate(card_resp.json())
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        for idx, question in enumerate(QUESTIONS, start=1):
            print("=" * 70)
            print(f"QUESTION {idx}: {question}")

            message = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=question))],
                message_id=str(uuid4()),
                context_id=context_id,
            )
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(message=message),
            )
            response = await client.send_message(request)
            print(_extract_text(response))


def _extract_text(response: object) -> str:
    if hasattr(response, "root"):
        response = response.root
    result = getattr(response, "result", None)
    if result is None:
        return ""

    text = ""
    artifacts = getattr(result, "artifacts", None)
    if artifacts:
        for artifact in artifacts:
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
