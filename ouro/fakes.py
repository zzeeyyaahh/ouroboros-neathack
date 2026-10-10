from __future__ import annotations

import json
from typing import Any

from .tools.crustdata import CrustdataClient, CrustdataError

FIXTURES: dict[str, Any] = {
    "/company/identify": {"companies": [{"company_id": "mock-co", "name": "Mock Co", "domain": "example.com"}]},
    "/company/enrich": {
        "company": {
            "company_id": "mock-co",
            "name": "Mock Co",
            "headcount": 120,
            "industry": "Software",
            "hq": "San Francisco, CA",
        }
    },
    "/person/search": {"people": [{"name": "Ada Lovelace", "title": "CEO"}, {"name": "Grace Hopper", "title": "CTO"}]},
    "/web/search/live": {"results": [{"title": "Mock Co raises Series A", "url": "https://example.com/news"}]},
    "/account/endpoints": {"endpoints": ["/company/identify", "/company/enrich", "/web/search/live"]},
}


class _Field:
    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)

    def model_dump(self, exclude_none: bool = True) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


class _Function(_Field):
    pass


class _ToolCall(_Field):
    def model_dump(self, exclude_none: bool = True) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": "function",
            "function": {"name": self.function.name, "arguments": self.function.arguments},
        }


class _Message(_Field):
    def model_dump(self, exclude_none: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {"content": self.content, "role": "assistant"}
        if self.tool_calls:
            data["tool_calls"] = [tc.model_dump() for tc in self.tool_calls]
        return data


class _Choice(_Field):
    pass


class _Response(_Field):
    pass


def _tool_call_response(call_id: str, name: str, arguments: dict[str, Any]) -> _Response:
    call = _ToolCall(id=call_id, function=_Function(name=name, arguments=json.dumps(arguments)))
    message = _Message(content="", tool_calls=[call])
    return _Response(choices=[_Choice(message=message, index=0)])


def _raw_tool_call_response(call_id: str, name: str, raw_arguments: str) -> _Response:
    call = _ToolCall(id=call_id, function=_Function(name=name, arguments=raw_arguments))
    message = _Message(content="", tool_calls=[call])
    return _Response(choices=[_Choice(message=message, index=0)])


def _content_response(content: str) -> _Response:
    message = _Message(content=content, tool_calls=None)
    return _Response(choices=[_Choice(message=message, index=0)])


GOOD_DOSSIER: dict[str, Any] = {
    "domain": "example.com",
    "overview": "Mock Co is a 120-person software company headquartered in San Francisco.",
    "people": ["Ada Lovelace (CEO)", "Grace Hopper (CTO)"],
    "recent_news": ["Mock Co raises Series A"],
    "risks": ["Early stage", "Concentrated leadership"],
    "outreach_angles": ["Congratulate on Series A", "Pitch to CTO first"],
}


class MockLLM:
    def __init__(self, script: list[_Response] | None = None) -> None:
        self.script = script if script is not None else build_worker_script()
        self.calls: list[dict[str, Any]] = []
        outer = self
        outer.ref = self

        class _Completions:
            def create(self, **kwargs: Any) -> _Response:
                return outer.create(**kwargs)

        class _Chat:
            completions = _Completions()

        self.chat = _Chat()

    def create(self, **kwargs: Any) -> _Response:
        self.calls.append(kwargs)
        if self._is_verify_call(kwargs):
            return _content_response(json.dumps(self._verdict(kwargs)))
        if self.script:
            item = self.script.pop(0)
            if isinstance(item, _Response) and not item.choices[0].message.tool_calls:
                return item
            return item
        return _content_response(json.dumps(GOOD_DOSSIER))

    def _is_verify_call(self, kwargs: dict[str, Any]) -> bool:
        messages = kwargs.get("messages") or []
        for msg in messages:
            if msg.get("role") == "user":
                text = msg.get("content") or ""
                return isinstance(text, str) and text.startswith("Verify this dossier")
        return False

    def _verdict(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        messages = kwargs.get("messages") or []
        text = next((m.get("content") or "" for m in messages if m.get("role") == "user"), "")
        missing = [s for s in ("overview", "people", "recent_news", "risks", "outreach_angles") if f"{s}:" not in text and s not in text]
        if missing:
            return {"passed": False, "issues": [f"missing or empty section: {s}" for s in missing]}
        return {"passed": True, "issues": []}


def build_worker_script(domain: str = "example.com") -> list[_Response]:
    return [
        _tool_call_response("call_1", "identify_company", {"domain": domain}),
        _tool_call_response("call_2", "enrich_company", {"company_id": "mock-co"}),
        _tool_call_response("call_3", "search_people", {"company_id": "mock-co"}),
        _tool_call_response("call_4", "web_search", {"query": f"{domain} recent news"}),
        _content_response(json.dumps(GOOD_DOSSIER)),
    ]


class MockCrustdata(CrustdataClient):
    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        record: dict[str, Any] = {"path": path, "payload_keys": sorted(payload), "status": None, "error": None}
        self.calls.append(record)
        self._maybe_inject_fault(path)
        record["status"] = 200
        record["latency_ms"] = 1
        return FIXTURES.get(path, {})

    def _maybe_inject_fault(self, path: str) -> None:
        if not self.fault_inject:
            return
        if sum(1 for c in self.calls if c["path"] == path) <= 1:
            record = self.calls[-1]
            record["status"] = 429
            record["error"] = "rate_limited (injected)"
            raise CrustdataError("rate_limited (injected)", status=429)
