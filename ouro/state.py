from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "state" / "runs.jsonl"


def append_run(record: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def read_runs() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    return [json.loads(line) for line in LOG_PATH.read_text().splitlines() if line.strip()]


def read_runs_for(domain: str) -> list[dict[str, Any]]:
    return [r for r in read_runs() if r.get("domain") == domain]
