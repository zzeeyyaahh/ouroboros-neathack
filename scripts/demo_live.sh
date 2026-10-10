#!/usr/bin/env bash
# Live contrast pair for the demo video: real Crustdata + OpenAI calls, real neatlogs traces.
# T1 = baseline run with injected 429s; supervisor classification; T2 = healed rerun with backoff.
# Usage: bash scripts/demo_live.sh [domain]
set -euo pipefail
cd "$(dirname "$0")/.."
export OURO_FAULT_INJECT=1
DOMAIN="${1:-crustdata.com}"

echo "=== T1 (baseline): live run, first call per endpoint 429s ==="
.venv/bin/python -m ouro run "$DOMAIN" || true

echo
echo "=== Supervisor: classify failure, remediate (retry_with_backoff), rerun ==="
.venv/bin/python -m ouro supervise --window-hours 24

echo
echo "=== Before/after run log ==="
.venv/bin/python -m ouro runs

echo
echo "=== Cost/throughput summary for the cfo.ai business plan ==="
.venv/bin/python scripts/trace_costs.py
