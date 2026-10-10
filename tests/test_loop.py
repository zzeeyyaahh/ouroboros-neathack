from __future__ import annotations

import json

from ouro import state
from ouro.fakes import (
    GOOD_DOSSIER,
    MockCrustdata,
    MockLLM,
    _content_response,
    _raw_tool_call_response,
    _tool_call_response,
    build_worker_script,
)
from ouro.state import append_run
from ouro.supervisor.heal import classify_run, plan_remediation, supervise
from ouro.worker import run_dossier


def _patch_state(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(state, "LOG_PATH", tmp_path / "runs.jsonl")


def test_mock_worker_success(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    record = run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(build_worker_script()),
        client=MockCrustdata(),
    )
    assert record["status"] == "success"
    assert record["tools_succeeded"] == ["enrich_company", "identify_company", "search_people", "web_search"]
    assert record["schema_issues"] == []
    assert record["verify_issues"] == []
    dossier_file = tmp_path / "out" / "example_com" / record["run_id"] / "dossier.json"
    assert dossier_file.exists()


def test_mock_worker_fails_when_tools_fail(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    client = MockCrustdata()
    client.fault_inject = True
    record = run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(build_worker_script()),
        client=client,
    )
    assert record["status"] == "failed"
    assert record["tool_failures"]
    assert all(f["status"] == 429 for f in record["tool_failures"])
    assert "no successful tool calls in evidence" in record["schema_issues"]


def test_backoff_remediation_heals_failed_run(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    failing = MockCrustdata()
    failing.fault_inject = True
    first = run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(build_worker_script()),
        client=failing,
    )
    assert first["status"] == "failed"

    healthy = MockCrustdata()
    healthy.fault_inject = True
    healed = run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(build_worker_script()),
        client=healthy,
        remediation={"actions": ["retry_with_backoff"], "issues": []},
    )
    assert healed["status"] == "success"
    assert healed["remediation"] == ["retry_with_backoff"]


def test_supervisor_reads_run_log_and_heals(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    failing = MockCrustdata()
    failing.fault_inject = True
    run_dossier("example.com", out_root=tmp_path / "out", llm=MockLLM(build_worker_script()), client=failing)

    appended = state.read_runs()
    assert len(appended) == 1
    reasons = classify_run(appended[0])
    assert "429" in reasons
    plan = plan_remediation(appended[0])
    assert "retry_with_backoff" in plan["actions"]

    healthy = MockCrustdata()
    healthy.fault_inject = True
    reports = supervise(
        window_hours=24,
        llm=MockLLM(build_worker_script()),
        client=healthy,
        out_root=tmp_path / "out",
    )
    assert len(reports) == 1
    assert reports[0]["healed"] is True
    assert reports[0]["after"]["status"] == "success"


def test_failed_runs_respects_window(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    append_run({"run_id": "old", "domain": "a.com", "status": "failed", "started_epoch": 0})
    append_run({"run_id": "new", "domain": "a.com", "status": "failed", "started_epoch": 9_999_999_999_999})
    from ouro.supervisor.heal import failed_runs

    recent = failed_runs(1)
    assert [r["run_id"] for r in recent] == ["new"]


def test_malformed_tool_args_recorded_not_crashing(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    script = [
        _tool_call_response("call_1", "identify_company", {"domain": "example.com"}),
        _tool_call_response("call_2", "search_people", {}),
        _raw_tool_call_response("call_3", "web_search", "{not-json"),
        _tool_call_response("call_4", "enrich_company", {"company_id": "mock-co"}),
        _content_response(json.dumps(GOOD_DOSSIER)),
    ]
    record = run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(script),
        client=MockCrustdata(),
    )
    assert record["status"] == "success"
    bad = record["tool_failures"]
    assert len(bad) == 2
    assert all(f["kind"] == "invalid_args" for f in bad)
    assert {f["tool"] for f in bad} == {"search_people", "web_search"}
    assert "enrich_company" in record["tools_succeeded"]

    reasons = classify_run(record)
    assert "invalid_args" in reasons
    plan = plan_remediation(record)
    assert "revise_tool_args" in plan["actions"]


def test_revise_tool_args_action_edits_system_prompt(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    llm = MockLLM(build_worker_script())
    run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=llm,
        client=MockCrustdata(),
        remediation={"actions": ["revise_tool_args"], "issues": []},
    )
    system_msg = llm.calls[0]["messages"][0]["content"]
    assert "identify_company takes" in system_msg


def test_all_invalid_tool_args_fails_run(tmp_path, monkeypatch):
    _patch_state(tmp_path, monkeypatch)
    script = [
        _raw_tool_call_response("call_1", "identify_company", "not json at all"),
        _content_response(json.dumps(GOOD_DOSSIER)),
    ]
    record = run_dossier(
        "example.com",
        out_root=tmp_path / "out",
        llm=MockLLM(script),
        client=MockCrustdata(),
    )
    assert record["status"] == "failed"
    assert "no successful tool calls in evidence" in record["schema_issues"]
    assert record["tool_failures"][0]["kind"] == "invalid_args"
    reasons = classify_run(record)
    assert "invalid_args" in reasons and "no_evidence" in reasons
