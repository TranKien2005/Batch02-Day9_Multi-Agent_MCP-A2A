# Advanced Features

This repository was extended with two optional advanced features for the codelab bonus task:

1. A distributed `financial_agent` A2A service.
2. Simple conversation memory in the Customer Agent.

## 1. Financial Agent

### Purpose

The Financial Agent adds a new specialist domain to Stage 5. It analyzes financial damages, revenue exposure, business risk, remediation cost, and practical financial assumptions for legal matters.

### Files Added

| File | Purpose |
|---|---|
| `financial_agent/__main__.py` | Starts the A2A service on port `10104`, exposes an Agent Card, and registers `financial_question` with the Registry. |
| `financial_agent/graph.py` | Defines the Financial Agent's LangGraph/ReAct graph and finance-focused system prompt. |
| `financial_agent/agent_executor.py` | Bridges incoming A2A requests to the Financial Agent graph and returns `financial_analysis`. |
| `financial_agent/__init__.py` | Makes `financial_agent` a Python package. |

### Integration Points

The Financial Agent is integrated into the Stage 5 system in these places:

| File | Change |
|---|---|
| `law_agent/graph.py` | Adds `needs_financial`, routes financial questions, discovers `financial_question`, calls the Financial Agent through A2A, and aggregates `financial_result`. |
| `pyproject.toml` | Adds `financial_agent` to the package list. |
| `start_all.sh` | Starts `financial_agent` for Bash/Git Bash users. |
| `start_all.ps1` | Starts `financial_agent` for PowerShell users. |
| `test_client.py` | Uses a question that includes financial damages/revenue/business risk so the Financial Agent can be triggered. |

### Runtime Flow

```text
test_client.py
  -> Customer Agent (:10100)
  -> Law Agent (:10101)
  -> Registry discover("financial_question")
  -> Financial Agent (:10104)
  -> Law Agent aggregate
  -> Customer Agent
  -> test_client.py
```

The Financial Agent runs alongside Tax and Compliance as another specialist branch in the Law Agent's LangGraph workflow.

## 2. Customer Agent Memory

### Purpose

The Customer Agent now remembers recent turns per A2A `context_id`, allowing follow-up questions to include conversation history.

### Implementation

Memory is implemented in `customer_agent/agent_executor.py` with an in-memory dictionary:

```python
_conversation_memory: dict[str, list[tuple[str, str]]] = {}
```

For each request:

1. The executor reads the current `context_id`.
2. If previous turns exist for that context, it prepends a short conversation history to the current question.
3. After the final answer is generated, it stores the `(question, answer)` pair.
4. It keeps only the latest `MAX_MEMORY_TURNS = 4` turns.

This is intentionally simple and in-memory. It is suitable for a codelab demonstration, not production persistence.

### Demo Client

`advanced_features_test.py` sends two questions using the same `context_id`:

1. A first question about a company with contract breach, customer loss, and tax exposure.
2. A follow-up asking what financial facts counsel should collect next.

Because both messages share the same `context_id`, the Customer Agent includes the first turn when processing the follow-up.

Run after Stage 5 services are started:

```powershell
.\.venv\Scripts\python.exe advanced_features_test.py
```

## How To Run

PowerShell:

```powershell
.\start_all.ps1
```

In another terminal:

```powershell
.\.venv\Scripts\python.exe test_client.py
.\.venv\Scripts\python.exe advanced_features_test.py
```

Bash/Git Bash:

```bash
./start_all.sh
```

In another terminal:

```bash
.venv/Scripts/python.exe test_client.py
.venv/Scripts/python.exe advanced_features_test.py
```

## Expected Registry State

The Registry should contain five agents:

| Agent | Task | Endpoint |
|---|---|---|
| `customer-agent` | entry point | `http://localhost:10100` |
| `law-agent` | `legal_question` | `http://localhost:10101` |
| `tax-agent` | `tax_question` | `http://localhost:10102` |
| `compliance-agent` | `compliance_question` | `http://localhost:10103` |
| `financial-agent` | `financial_question` | `http://localhost:10104` |

## Notes

- The Financial Agent is a real A2A service, not only an in-process Stage 4 node.
- Memory is local to the running Customer Agent process and resets when the process restarts.
- MCP is still not implemented; this advanced feature extends the A2A multi-agent system and local LangGraph workflows.
