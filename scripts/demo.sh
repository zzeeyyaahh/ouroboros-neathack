#!/usr/bin/env bash
# Deterministic offline demo of the full self-healing loop: no API keys, no network.
# Run 1 fails on injected 429s -> supervisor classifies -> reruns with backoff -> heals.
set -euo pipefail
cd "$(dirname "$0")/.."

export OURO_MOCK=1
export OURO_FAULT_INJECT=1

echo "=== Run 1: worker hits injected 429s (baseline failure) ==="
.venv/bin/python -m ouro run example.com || true

echo
echo "=== Supervisor: classify failure, remediate (retry_with_backoff), rerun ==="
.venv/bin/python -m ouro supervise --window-hours 24

echo
echo "=== Run log (before -> after) ==="
.venv/bin/python -m ouro runs

echo
echo "=== Cost/throughput summary for the cfo.ai business plan ==="
.venv/bin/python scripts/trace_costs.py
