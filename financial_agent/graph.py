"""Financial Agent LangGraph definition.

Uses create_react_agent with a finance-specialised system prompt.
"""

from __future__ import annotations

from langgraph.prebuilt import create_react_agent

from common.llm import get_llm

FINANCIAL_SYSTEM_PROMPT = """You are a financial damages and risk analyst supporting legal counsel.

Focus on:
- Contract damages exposure: direct damages, consequential damages, cover costs,
  liquidated damages, mitigation costs, and attorney-fee exposure
- Business impact: cash flow, revenue disruption, customer churn, reputational harm,
  insurance coverage, and financing/investor risk
- Tax and regulatory financial exposure: back taxes, interest, fraud penalties,
  investigation costs, remediation costs, and reserve estimates
- Practical risk framing: low/medium/high exposure, key assumptions, and what data
  would be needed for a defensible calculation

When answering, distinguish between legal conclusions and financial estimates. Use
clear bullet points, include assumptions, and avoid inventing precise figures unless
the user provided enough numeric facts.
"""


def create_graph():
    """Return a compiled LangGraph create_react_agent for financial risk questions."""
    llm = get_llm()
    graph = create_react_agent(
        model=llm,
        tools=[],
        prompt=FINANCIAL_SYSTEM_PROMPT,
    )
    return graph
