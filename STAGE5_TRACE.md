# Stage 5 Request Flow Trace

## Runtime Status

Stage 5 was started with the local multi-service A2A setup. The Registry health endpoint returned `status=ok` with `agent_count=4`.

Registered agents discovered from `http://localhost:10000/agents`:

| Agent | Task | Endpoint | Role |
|---|---|---|---|
| `customer-agent` | entry point | `http://localhost:10100` | Receives the user request and routes legal questions to the Law Agent. |
| `law-agent` | `legal_question` | `http://localhost:10101` | Legal orchestrator; analyzes the legal issue and delegates to specialists. |
| `tax-agent` | `tax_question` | `http://localhost:10102` | Tax specialist for IRS, penalties, tax evasion, and corporate tax liability. |
| `compliance-agent` | `compliance_question` | `http://localhost:10103` | Regulatory specialist for SEC, SOX, AML, FCPA, and governance issues. |

The following Registry discovery calls returned valid endpoints:

| Discovery Task | Registry Result |
|---|---|
| `legal_question` | `law-agent` at `http://localhost:10101` |
| `tax_question` | `tax-agent` at `http://localhost:10102` |
| `compliance_question` | `compliance-agent` at `http://localhost:10103` |

Agent Cards were also available at each service's `/.well-known/agent.json` endpoint, confirming A2A metadata exposure for Customer, Law, Tax, and Compliance agents.

## End-To-End Test

The test client connected successfully to the Customer Agent:

```text
Connecting to Customer Agent at http://localhost:10100
Connected to agent: Customer Agent v1.0.0
Sending request...
RESPONSE:
...
```

Test question:

```text
If a company breaks a contract and avoids taxes, what are the legal and regulatory consequences?
```

The final response covered contract breach, tax evasion, combined legal exposure, and immediate recommendations, showing that the Stage 5 entry point completed the full request and returned an aggregated legal answer.

## Sequence Diagram

```text
test_client.py
  -> Customer Agent (:10100)
       Receives the user legal question through A2A.

Customer Agent
  -> Registry (:10000)
       discover("legal_question")

Registry
  -> Customer Agent
       returns Law Agent endpoint: http://localhost:10101

Customer Agent
  -> Law Agent (:10101)
       sends the legal question through A2A.

Law Agent
  -> Law Agent LangGraph
       analyze_law: produces general contract/legal analysis.
       check_routing: decides whether tax and compliance specialists are needed.

Law Agent
  -> Registry (:10000)
       discover("tax_question")
       discover("compliance_question")

Registry
  -> Law Agent
       returns Tax Agent endpoint: http://localhost:10102
       returns Compliance Agent endpoint: http://localhost:10103

Law Agent
  -> Tax Agent (:10102)
       sends tax-related subtask through A2A.

Law Agent
  -> Compliance Agent (:10103)
       sends regulatory-compliance subtask through A2A.

Tax Agent
  -> Law Agent
       returns tax analysis.

Compliance Agent
  -> Law Agent
       returns compliance analysis.

Law Agent
  -> Law Agent LangGraph
       aggregate: combines law, tax, and compliance analyses.

Law Agent
  -> Customer Agent
       returns final aggregated legal response through A2A.

Customer Agent
  -> test_client.py
       returns final response to the user.
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| LangGraph | Controls the internal workflow inside each agent, especially Law Agent routing and aggregation. |
| A2A | Carries messages between independent agent services over HTTP/JSON-RPC. |
| Registry | Provides dynamic service discovery so agents do not hardcode each other's URLs. |
| MCP | Not implemented in this repository's Stage 5 code; tools are local LangChain tools or internal agent logic. |

## Conclusion

Stage 5 ran successfully as a distributed A2A multi-agent system. The Registry was healthy, agents registered their tasks, discovery returned the expected service endpoints, Agent Cards were available, and the end-to-end client received a final response from the Customer Agent.
