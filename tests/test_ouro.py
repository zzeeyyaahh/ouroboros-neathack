from __future__ import annotations

import httpx
import pytest

from ouro.state import append_run, read_runs
from ouro.tools.crustdata import CrustdataClient, CrustdataError
from ouro.worker.dossier import parse_json_object, validate_dossier


def test_state_roundtrip(tmp_path, monkeypatch):
    from ouro import state

    log = tmp_path / "runs.jsonl"
    monkeypatch.setattr(state, "LOG_PATH", log)
    append_run({"run_id": "a1", "domain": "x.com", "status": "failed"})
    append_run({"run_id": "b2", "domain": "y.com", "status": "success"})
    runs = read_runs()
    assert len(runs) == 2
    assert runs[0]["domain"] == "x.com"


def test_validate_dossier_flags_missing_sections():
    issues = validate_dossier({"domain": "x.com", "overview": "hi"}, {"tools_succeeded": ["identify_company"], "company_id": "c1"})
    assert any("missing section: people" in i for i in issues)
    assert not any("company never resolved" in i for i in issues)


def test_validate_dossier_flags_no_evidence():
    issues = validate_dossier({}, {})
    assert issues


def test_parse_json_object_handles_fences():
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object("noise {\"b\": 2} tail") == {"b": 2}
    assert parse_json_object("plain text") == {}


def test_crustdata_fault_injection_first_call_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"companies": [{"company_id": "c-1"}]})

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.crustdata.com")
    client = CrustdataClient(token="fake", http=http)
    client.fault_inject = True
    with pytest.raises(CrustdataError) as exc:
        client.identify("x.com")
    assert exc.value.status == 429
    result = client.identify("x.com")
    assert result["companies"][0]["company_id"] == "c-1"


def test_crustdata_records_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "forbidden"})

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.crustdata.com")
    client = CrustdataClient(token="fake", http=http)
    with pytest.raises(CrustdataError) as exc:
        client.web_search("q")
    assert exc.value.status == 403
    assert client.calls[-1]["status"] == 403
