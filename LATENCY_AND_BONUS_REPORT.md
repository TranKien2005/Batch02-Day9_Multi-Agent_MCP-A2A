# Latency and Bonus Report

## Bonus HTML Demo

Static demo file:

```text
docs/agent_interaction_demo.html
```

For real browser-based measurement, run the local dashboard server:

```powershell
.\.venv\Scripts\python.exe demo_server.py
```

Then open:

```text
http://localhost:8080
```

The dashboard can animate the Stage 5 A2A request flow and call the real local backend to measure the currently running Stage 5 system. It shows:

- Client -> Customer Agent
- Registry service discovery
- Customer Agent -> Law Agent
- Law Agent -> Tax, Compliance, and Financial agents
- Aggregation back to the client
- Normal route vs. fast route
- Buttons to measure baseline/optimized latency through `demo_server.py`
- A metrics button that reads `/metrics` from running services

## Measuring Stage 5 Latency

Start the full system:

```powershell
.\start_all.ps1
```

In another terminal, measure end-to-end latency:

```powershell
.\.venv\Scripts\python.exe measure_latency.py
```

For repeated runs:

```powershell
$env:LATENCY_RUNS="3"
.\.venv\Scripts\python.exe measure_latency.py
```

The script reports:

```text
Run 1: <seconds>s, response_chars=<n>
min=<seconds>s
max=<seconds>s
avg=<seconds>s
median=<seconds>s
```

The same measurement can also be triggered from the HTML dashboard through `demo_server.py`.

The latency measured here is the total user-facing time for one Stage 5 request:

```text
test_client/measure_latency
  -> Customer Agent
  -> Law Agent
  -> Tax + Compliance + Financial specialists
  -> Law aggregate
  -> Customer Agent
  -> client
```

## Latency Reduction Proposal

The default Customer Agent uses a ReAct agent to decide whether to delegate legal questions to the Law Agent. For this codelab, most test questions are legal questions, so that extra LLM decision can be skipped.

Optimization:

```text
CUSTOMER_FAST_ROUTE=true
```

Effect:

```text
Normal route:
Client -> Customer ReAct LLM decision -> Registry -> Law Agent -> specialists -> aggregate

Fast route:
Client -> Customer direct delegate -> Registry -> Law Agent -> specialists -> aggregate
```

This removes one LLM call at the entry point. It keeps the Law Agent routing, specialist delegation, A2A communication, and final aggregation intact.

## Demo Reduced Latency

Baseline:

```powershell
# Ensure CUSTOMER_FAST_ROUTE is disabled or unset
Remove-Item Env:CUSTOMER_FAST_ROUTE -ErrorAction SilentlyContinue
.\start_all.ps1
```

In another terminal:

```powershell
$env:LATENCY_RUNS="3"
.\.venv\Scripts\python.exe measure_latency.py
```

Record the `avg=<seconds>s` value.

Optimized run:

1. Stop the running services with `Ctrl+C`.
2. Restart with fast route enabled:

```powershell
$env:CUSTOMER_FAST_ROUTE="true"
.\start_all.ps1
```

3. Measure again:

```powershell
$env:LATENCY_RUNS="3"
.\.venv\Scripts\python.exe measure_latency.py
```

4. Compare average latency:

```text
improvement_percent = ((baseline_avg - optimized_avg) / baseline_avg) * 100
```

## Latency Result Table

Fill this table after running `measure_latency.py` in both modes. This is the section to show during grading.

| Mode | Env Setting | Runs | Average Latency | Notes |
|---|---|---:|---:|---|
| Baseline | `CUSTOMER_FAST_ROUTE` unset/false | `LATENCY_RUNS=3` | `____ s` | Customer Agent uses ReAct decision before delegating. |
| Optimized | `CUSTOMER_FAST_ROUTE=true` | `LATENCY_RUNS=3` | `____ s` | Customer Agent delegates directly to Law Agent. |

Latency difference:

```text
baseline_avg = ____ seconds
optimized_avg = ____ seconds
saved_seconds = baseline_avg - optimized_avg = ____ seconds
improvement_percent = (saved_seconds / baseline_avg) * 100 = ____ %
```

Interpretation:

```text
The optimization reduces latency by removing one Customer Agent LLM routing hop. The Law Agent still performs specialist routing and still calls Tax, Compliance, and Financial agents through A2A, so the architecture remains distributed.
```

## Monitoring and Observability

Each service exposes a lightweight Prometheus-style `/metrics` endpoint:

| Service | Metrics URL |
|---|---|
| Registry | `http://localhost:10000/metrics` |
| Customer Agent | `http://localhost:10100/metrics` |
| Law Agent | `http://localhost:10101/metrics` |
| Tax Agent | `http://localhost:10102/metrics` |
| Compliance Agent | `http://localhost:10103/metrics` |
| Financial Agent | `http://localhost:10104/metrics` |

Collect all metrics:

```powershell
.\.venv\Scripts\python.exe collect_metrics.py
```

Metrics include:

```text
a2a_requests_total
a2a_errors_total
a2a_request_latency_seconds_total
a2a_request_latency_seconds_avg
a2a_requests_by_path_total
```

## Other Advanced Features Implemented

| Challenge | Implementation |
|---|---|
| Memory/conversation history | `customer_agent/agent_executor.py` stores recent turns by `context_id`. |
| Authentication | Optional `A2A_API_KEY` protects A2A endpoints with `X-A2A-API-Key`. |
| Retry logic | `common/a2a_client.py` and `common/registry_client.py` retry transient failures with exponential backoff. |
| Monitoring | `common/observability.py` adds Prometheus-style `/metrics` endpoints. |
| Bonus HTML demo | `docs/agent_interaction_demo.html` visualizes Stage 5 agent interactions. |
| Latency reduction | `CUSTOMER_FAST_ROUTE=true` removes one Customer Agent LLM decision hop. |

## Notes

- Authentication is optional. If `A2A_API_KEY` is not set, services behave like the original codelab.
- Memory is in-process only and resets when Customer Agent restarts.
- Fast route is an optimization for known legal-entry workflows; keep it disabled if Customer Agent must decide whether to answer non-legal questions itself.
