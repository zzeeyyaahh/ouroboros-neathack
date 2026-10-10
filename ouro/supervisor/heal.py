from __future__ import annotations

import json
import subprocess
from typing import Any

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
}


def classify_run(run: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for failure in run.get("tool_failures", []):
        status = failure.get("status")
        if status:
            reasons.append(str(status))
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
        import time

        cutoff = time.time() - window_hours * 3600
        runs = [r for r in runs if r.get("started_epoch", 0) >= cutoff]
    return runs


def read_recent_traces(limit: int = 5) -> list[dict[str, Any]]:
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


def supervise(window_hours: float | None = None, rerun: bool = True) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for run in failed_runs(window_hours):
        report = plan_remediation(run)
        traces = read_recent_traces()
        report["trace_count_seen"] = len(traces)
        if rerun:
            report["rerun"] = run_dossier(run["domain"])
        reports.append(report)
    return reports
