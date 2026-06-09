#!/usr/bin/env bash
set -euo pipefail

# Start all Legal Multi-Agent System services.
# Registry must be first, then leaf agents, then orchestrators.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/Scripts/python.exe" ]]; then
  PYTHON_CMD=".venv/Scripts/python.exe"
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_CMD=".venv/bin/python"
else
  PYTHON_CMD="python"
fi

PIDS=()

cleanup() {
  echo ""
  echo "Stopping services..."
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}

trap cleanup EXIT INT TERM

echo "Using Python: $PYTHON_CMD"

echo "Starting Registry service on port 10000..."
"$PYTHON_CMD" -m registry &
PIDS+=("$!")
sleep 2

echo "Starting Tax Agent on port 10102..."
"$PYTHON_CMD" -m tax_agent &
PIDS+=("$!")

echo "Starting Compliance Agent on port 10103..."
"$PYTHON_CMD" -m compliance_agent &
PIDS+=("$!")

echo "Starting Financial Agent on port 10104..."
"$PYTHON_CMD" -m financial_agent &
PIDS+=("$!")
sleep 3

echo "Starting Law Agent on port 10101..."
"$PYTHON_CMD" -m law_agent &
PIDS+=("$!")
sleep 3

echo "Starting Customer Agent on port 10100..."
"$PYTHON_CMD" -m customer_agent &
PIDS+=("$!")

echo ""
echo "All services started:"
echo "  Registry:         http://localhost:10000"
echo "  Customer Agent:   http://localhost:10100"
echo "  Law Agent:        http://localhost:10101"
echo "  Tax Agent:        http://localhost:10102"
echo "  Compliance Agent: http://localhost:10103"
echo "  Financial Agent:  http://localhost:10104"
echo ""
echo "Run test_client.py to send a query:"
echo "  $PYTHON_CMD test_client.py"
echo ""
echo "Press Ctrl+C to stop all services."

wait "${PIDS[@]}"
