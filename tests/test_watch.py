from __future__ import annotations

import json

from ouro import state
from ouro.fakes import MockCrustdata, MockLLM, build_worker_script
from ouro.supervisor.heal import load_watch_state, watch_daemon, watch_once
from ouro.worker import run_dossier


def _patch_state(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "LOG_PATH", tmp_path / "runs.jsonl")


def _failing_mock():
    client = MockCrustdata()
    client.fault_inject = True
    return client


def _healing_mock():
    client = MockCrustdata()
    client.fault_inject = True
    return client


def test_watch_once_heals_new_failure_and_records_it(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(build_worker_script()),
        client=_failing_mock(),
    )
    result = watch_once(24, llm=MockLLM(build_worker_script()), client=_healing_mock(), out_root=tmp_path / "out")
    assert result["healed"] != []
    ws = load_watch_state()
    assert len(ws["healed_run_ids"]) == len(result["healed"])
    assert ws["cycles"] == 1
    assert ws["started_at"] is not None


def test_watch_once_does_not_reheal(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(build_worker_script()),
        client=_failing_mock(),
    )
    first = watch_once(24, llm=MockLLM(build_worker_script()), client=_healing_mock(), out_root=tmp_path / "out")
    assert len(first["healed"]) == 1
    second = watch_once(24, llm=MockLLM(build_worker_script()), client=_healing_mock(), out_root=tmp_path / "out")
    assert second["seen"] == []
    assert second["healed"] == []
    ws = load_watch_state()
    assert ws["cycles"] == 2
    assert len(ws["healed_run_ids"]) == 1


def test_watch_daemon_terminates_on_max_cycles(tmp_path, monkeypatch, capsys):
    _patch_state(tmp_path, monkeypatch)
    cycles = watch_daemon(
        window_hours=24,
        interval_s=0,
        max_cycles=2,
        llm=MockLLM(build_worker_script()),
        client=_healing_mock(),
        out_root=tmp_path / "out",
    )
    assert cycles == 2
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.startswith("{")]
    assert len(lines) == 2
    assert all("cycle" in json.loads(line) for line in lines)
