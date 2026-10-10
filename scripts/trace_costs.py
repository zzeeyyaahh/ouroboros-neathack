"""Aggregate dossier run records into the cost/throughput numbers for the cfo.ai business plan."""
import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "out"


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [r for r in runs if r.get("status") == "success"]
    failures = [r for r in runs if r.get("status") != "success"]
    durations = [float(r.get("duration_s") or 0) for r in runs]
    failures_by_status: dict[str, int] = {}
    for run in failures:
        for failure in run.get("tool_failures", []):
            key = str(failure.get("status") or "unknown")
            failures_by_status[key] = failures_by_status.get(key, 0) + 1
    healed = [r for r in successes if r.get("remediation")]
    return {
        "runs": len(runs),
        "successes": len(successes),
        "failures": len(failures),
        "success_rate": round(len(successes) / len(runs), 3) if runs else None,
        "healed_by_supervisor": len(healed),
        "avg_duration_s": round(sum(durations) / len(durations), 2) if durations else None,
        "tool_calls_total": sum(len(r.get("tool_calls", [])) for r in runs),
        "llm_calls_total": sum(int(r.get("llm_calls", 0)) for r in runs),
        "prompt_tokens_total": sum(int((r.get("usage") or {}).get("prompt_tokens", 0)) for r in runs),
        "completion_tokens_total": sum(int((r.get("usage") or {}).get("completion_tokens", 0)) for r in runs),
        "failures_by_http_status": failures_by_status,
    }


def load_runs(out_dir: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in sorted(out_dir.glob("*/*/run.json")):
        try:
            runs.append(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    return runs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    print(json.dumps(summarize(load_runs(args.out_dir)), indent=2))


if __name__ == "__main__":
    main()
