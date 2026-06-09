"""Financial Agent server entry point - port 10104."""

from __future__ import annotations

import asyncio
import logging

import uvicorn
from dotenv import load_dotenv

load_dotenv()

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from common.registry_client import register
from common.observability import add_metrics
from common.security import add_api_key_middleware
from financial_agent.agent_executor import FinancialAgentExecutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [financial_agent] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

PORT = 10104
AGENT_ENDPOINT = f"http://localhost:{PORT}"


async def _register_with_retry(max_attempts: int = 10, delay: float = 2.0) -> None:
    """Retry registration until the registry is up."""
    info = {
        "agent_name": "financial-agent",
        "version": "1.0",
        "description": "Financial damages and business-risk analyst for legal matters",
        "tasks": ["financial_question"],
        "endpoint": AGENT_ENDPOINT,
        "tags": ["financial", "damages", "risk", "revenue", "losses"],
    }
    for attempt in range(1, max_attempts + 1):
        try:
            await register(info)
            logger.info("Registered with registry (attempt %d)", attempt)
            return
        except Exception as exc:
            logger.warning(
                "Registry not ready (attempt %d/%d): %s - retrying in %.0fs",
                attempt, max_attempts, exc, delay,
            )
            await asyncio.sleep(delay)
    logger.error("Failed to register after %d attempts", max_attempts)


async def main() -> None:
    await _register_with_retry()

    agent_card = AgentCard(
        name="Financial Agent",
        description=(
            "Financial damages and business-risk analyst for contract breaches, "
            "tax exposure, regulatory remediation costs, and revenue impact."
        ),
        url=AGENT_ENDPOINT,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="financial_question",
                name="Financial Question",
                description=(
                    "Analyze financial damages, business impact, remediation cost, "
                    "revenue exposure, and risk reserves for legal matters."
                ),
                tags=["financial", "damages", "risk", "revenue", "losses"],
            )
        ],
    )

    executor = FinancialAgentExecutor()
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
    )
    app_builder = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    app = app_builder.build()
    add_metrics(app, "financial-agent")
    add_api_key_middleware(app)

    config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    logger.info("Financial Agent listening on port %d", PORT)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
