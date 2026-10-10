#!/usr/bin/env bash
# Deterministic offline demo of the full self-healing loop: no API keys, no network.
# Usage: bash scripts/demo.sh [--fresh]  (--fresh wipes state/ and out/ first)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" = "--fresh" ]; then
  rm -rf state out
  echo "(fresh state)"
fi

export OURO_MOCK=1
export OURO_FAULT_INJECT=1

echo "=== Act 1: worker hits injected 429s (baseline failure) ==="
.venv/bin/python -m ouro run example.com || true

echo
echo "=== Act 2: supervisor classifies, remediates (retry_with_backoff), reruns ==="
.venv/bin/python -m ouro supervise --window-hours 24

echo
echo "=== Act 3: a fresh failure appears... ==="
.venv/bin/python -m ouro run example.com || true

echo
echo "=== Act 3: the watch daemon finds and heals it in the background ==="
.venv/bin/python -m ouro watch --once

echo
echo "=== Act 3: next cycle — already healed, so it does nothing (each failure healed once) ==="
.venv/bin/python -m ouro watch --once

echo
echo "=== Run log (before -> after -> before -> after) ==="
.venv/bin/python -m ouro runs

echo
echo "=== Cost/throughput summary for the cfo.ai business plan ==="
.venv/bin/python scripts/trace_costs.py
