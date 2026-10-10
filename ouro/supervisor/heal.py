from __future__ import annotations

import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .. import state
from ..config import settings
from ..state import read_runs
from ..worker import run_dossier

REMEDIATIONS: dict[str, str] = {
    "429": "retry_with_backoff",
    "401": "refresh_credentials",
    "403": "switch_tool_alternate_endpoint",
    "404": "revise_plan_skip_step",
    "verify_failed": "revise_synthesis_prompt",
    "missing_section": "revise_synthesis_prompt",
    "no_evidence": "revise_plan_expand_search",
    "invalid_args": "revise_tool_args",
    "network_error": "retry_with_backoff",
}


def classify_run(run: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for failure in run.get("tool_failures", []):
        if failure.get("kind") == "invalid_args":
            reasons.append("invalid_args")
        elif failure.get("status"):
            reasons.append(str(failure["status"]))
        else:
            reasons.append("network_error")
    if run.get("status") != "success":
        if run.get("verify_issues"):
            reasons.append("verify_failed")
        if run.get("schema_issues"):
            reasons.append("missing_section")
        if not run.get("tools_succeeded"):
            reasons.append("no_evidence")
    out: list[str] = []
    for reason in reasons:
        if reason not in out:
            out.append(reason)
    return out


def plan_remediation(run: dict[str, Any]) -> dict[str, Any]:
    reasons = classify_run(run)
    actions = [REMEDIATIONS.get(r, "manual_review") for r in reasons]
    return {"run_id": run.get("run_id"), "domain": run.get("domain"), "reasons": reasons, "actions": actions}


def failed_runs(window_hours: float | None = None) -> list[dict[str, Any]]:
    runs = [r for r in read_runs() if r.get("status") != "success"]
    if window_hours is not None:
        cutoff = time.time() - window_hours * 3600
        runs = [r for r in runs if r.get("started_epoch", 0) >= cutoff]
    return runs


def read_recent_traces(limit: int = 5) -> list[dict[str, Any]]:
    if settings.mock_mode:
        return [{"trace_id": "mock-trace", "status": "ok"}]
    try:
        proc = subprocess.run(
            ["neatlogs", "traces", "list", "--limit", str(limit), "--json"],
            capture_output=True,
            check=False,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else data.get("traces", [])


def _heal_one_run(run: dict[str, Any], llm: Any | None = None, client: Any | None = None, out_root: Any | None = None) -> dict[str, Any]:
    report = plan_remediation(run)
    report["traces_seen"] = len(read_recent_traces())
    issues = list(run.get("schema_issues", [])) + list(run.get("verify_issues", []))
    remediation = {"actions": report["actions"], "issues": issues}
    after = run_dossier(run["domain"], out_root=out_root, llm=llm, client=client, remediation=remediation)
    report["remediation_applied"] = remediation
    report["before"] = {
        "status": run.get("status"),
        "schema_issues": run.get("schema_issues", []),
        "verify_issues": run.get("verify_issues", []),
        "duration_s": run.get("duration_s"),
    }
    report["after"] = {
        "status": after.get("status"),
        "schema_issues": after.get("schema_issues", []),
        "verify_issues": after.get("verify_issues", []),
        "duration_s": after.get("duration_s"),
    }
    report["healed"] = run.get("status") != "success" and after.get("status") == "success"
    return report


def supervise(
    window_hours: float | None = None,
    rerun: bool = True,
    llm: Any | None = None,
    client: Any | None = None,
    out_root: Any | None = None,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for run in failed_runs(window_hours):
        report = plan_remediation(run)
        report["traces_seen"] = len(read_recent_traces())
        if rerun:
            report.update(_heal_one_run(run, llm=llm, client=client, out_root=out_root))
        reports.append(report)
    return reports


def _watch_state_path() -> Path:
    return state.LOG_PATH.parent / "watch_state.json"


def load_watch_state() -> dict[str, Any]:
    path = _watch_state_path()
    if not path.exists():
        return {"healed_run_ids": [], "cycles": 0, "started_at": None}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {"healed_run_ids": [], "cycles": 0, "started_at": None}


def save_watch_state(watch_state: dict[str, Any]) -> None:
    path = _watch_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(watch_state, indent=2))


def watch_once(
    window_hours: float = 24,
    llm: Any | None = None,
    client: Any | None = None,
    out_root: Any | None = None,
) -> dict[str, Any]:
    watch_state = load_watch_state()
    watch_state.setdefault("healed_run_ids", [])
    watch_state["cycles"] = watch_state.get("cycles", 0) + 1
    if not watch_state.get("started_at"):
        watch_state["started_at"] = _now_iso()

    seen: list[str] = []
    healed: list[str] = []
    for run in failed_runs(window_hours):
        run_id = run.get("run_id")
        if run_id in watch_state["healed_run_ids"]:
            continue
        seen.append(run_id)
        report = _heal_one_run(run, llm=llm, client=client, out_root=out_root)
        if report["healed"]:
            watch_state["healed_run_ids"].append(run_id)
            healed.append(run_id)

    watch_state["last_cycle_at"] = _now_iso()
    save_watch_state(watch_state)
    return {"cycle": watch_state["cycles"], "seen": seen, "healed": healed, "total_healed": len(watch_state["healed_run_ids"])}


def watch_daemon(
    window_hours: float = 24,
    interval_s: float = 300,
    max_cycles: int | None = None,
    llm: Any | None = None,
    client: Any | None = None,
    out_root: Any | None = None,
) -> int:
    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        result = watch_once(window_hours, llm=llm, client=client, out_root=out_root)
        cycle += 1
        print(json.dumps(result), flush=True)
        if max_cycles is None or cycle < max_cycles:
            time.sleep(interval_s)
    return cycle


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
