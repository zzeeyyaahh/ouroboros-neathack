from __future__ import annotations

from pathlib import Path

from scripts.trace_costs import load_runs, summarize


def _write_run(out_dir: Path, domain: str, run_id: str, record: dict) -> None:
    run_dir = out_dir / domain.replace(".", "_") / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(__import__("json").dumps(record))


def test_summarize_counts_healed_and_failures():
    runs = [
        {"status": "failed", "duration_s": 1.0, "tool_failures": [{"status": 429}, {"status": 429}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
        {"status": "success", "duration_s": 3.0, "remediation": ["retry_with_backoff"], "usage": {"prompt_tokens": 20, "completion_tokens": 10}},
    ]
    summary = summarize(runs)
    assert summary["runs"] == 2
    assert summary["success_rate"] == 0.5
    assert summary["healed_by_supervisor"] == 1
    assert summary["failures_by_http_status"] == {"429": 2}
    assert summary["prompt_tokens_total"] == 30
    assert summary["avg_duration_s"] == 2.0


def test_summarize_empty():
    assert summarize([])["runs"] == 0


def test_load_runs_from_disk(tmp_path):
    out_dir = tmp_path / "out"
    _write_run(out_dir, "a.com", "r1", {"status": "failed", "run_id": "r1"})
    _write_run(out_dir, "b.com", "r2", {"status": "success", "run_id": "r2"})
    runs = load_runs(out_dir)
    assert len(runs) == 2
    assert {r["run_id"] for r in runs} == {"r1", "r2"}
