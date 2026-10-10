from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from ..config import settings
from ..state import append_run
from ..tools.crustdata import CrustdataClient, CrustdataError

DOSSIER_SECTIONS = ["overview", "people", "recent_news", "risks", "outreach_angles"]

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "identify_company",
            "description": "Resolve a company domain to a Crustdata company_id.",
            "parameters": {
                "type": "object",
                "properties": {"domain": {"type": "string"}},
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enrich_company",
            "description": "Fetch a full company profile. Provide company_id (preferred) or domain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "domain": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_people",
            "description": "Find key people at a company by its company_id.",
            "parameters": {
                "type": "object",
                "properties": {"company_id": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["company_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live web for recent news, reviews, or context about a company.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]

_SYSTEM = (
    "You are the Ouroboros research worker. You produce verified company dossiers from a domain. "
    "Use the provided tools to gather evidence, then answer with a single JSON object (no markdown fences) "
    "with exactly these keys: domain, overview, people, recent_news, risks, outreach_angles. "
    "Every factual claim must come from tool results. If a tool fails, note it and continue with the other tools."
)


def _llm():
    from openai import OpenAI

    return OpenAI(api_key=settings.openai_api_key)


def _dispatch(name: str, args: dict[str, Any], client: CrustdataClient) -> dict[str, Any]:
    if name == "identify_company":
        return client.identify(args["domain"])
    if name == "enrich_company":
        return client.enrich(company_id=args.get("company_id"), domain=args.get("domain"))
    if name == "search_people":
        return client.search_people(args["company_id"], limit=int(args.get("limit", 10)))
    if name == "web_search":
        return client.web_search(args["query"])
    raise ValueError(f"unknown tool: {name}")


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json")
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def validate_dossier(dossier: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for section in DOSSIER_SECTIONS:
        value = dossier.get(section)
        if value is None or value == "" or value == [] or value == {}:
            issues.append(f"missing section: {section}")
    if not evidence.get("tools_succeeded"):
        issues.append("no successful tool calls in evidence")
    if not evidence.get("company_id"):
        issues.append("company never resolved via identify_company")
    return issues


def run_dossier(domain: str, out_root: Path | None = None) -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:8]
    started = time.monotonic()
    out_root = out_root or Path(__file__).resolve().parent.parent.parent / "out"
    client = CrustdataClient()
    evidence: dict[str, Any] = {
        "domain": domain,
        "tool_results": {},
        "tools_succeeded": [],
        "tool_failures": [],
        "company_id": None,
    }

    llm = _llm()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Build a dossier for: {domain}"},
    ]

    dossier: dict[str, Any] = {}
    steps = 0
    for _ in range(12):
        steps += 1
        resp = llm.chat.completions.create(model=settings.model, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            dossier = parse_json_object(msg.content or "")
            break
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            try:
                result = _dispatch(call.function.name, args, client)
                evidence["tools_succeeded"].append(call.function.name)
                evidence["tool_results"][call.function.name] = result
                if call.function.name == "identify_company" and isinstance(result, dict):
                    evidence["company_id"] = _extract_company_id(result)
                payload = json.dumps(result, default=str)[:6000]
            except CrustdataError as exc:
                evidence["tool_failures"].append(
                    {"tool": call.function.name, "args": args, "status": exc.status, "error": str(exc)}
                )
                payload = json.dumps({"error": str(exc), "status": exc.status})
            messages.append({"role": "tool", "tool_call_id": call.id, "content": payload})

    schema_issues = validate_dossier(dossier, evidence)
    verdict = _verify(domain, dossier, evidence)
    passed = verdict.get("passed", False) and not schema_issues

    run_record: dict[str, Any] = {
        "run_id": run_id,
        "domain": domain,
        "status": "success" if passed else "failed",
        "started_epoch": time.time(),
        "duration_s": round(time.monotonic() - started, 2),
        "steps": steps,
        "tools_succeeded": sorted(set(evidence["tools_succeeded"])),
        "tool_failures": evidence["tool_failures"],
        "schema_issues": schema_issues,
        "verify_issues": verdict.get("issues", []),
        "llm_calls": len([m for m in messages if m.get("role") == "assistant"]),
        "tool_calls": client.calls,
    }

    out_dir = out_root / domain.replace(".", "_") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dossier.json").write_text(json.dumps(dossier, indent=2, default=str))
    (out_dir / "run.json").write_text(json.dumps(run_record, indent=2, default=str))
    append_run(run_record)
    return run_record


def _extract_company_id(result: dict[str, Any]) -> str | None:
    for key in ("companies", "results", "data"):
        rows = result.get(key)
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return rows[0].get("company_id") or rows[0].get("id")
    return result.get("company_id") or result.get("id")


def _verify(domain: str, dossier: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    llm = _llm()
    prompt = (
        "Verify this dossier against the evidence. Reply with JSON only: "
        '{"passed": true|false, "issues": ["..."]}.\n'
        f"Domain: {domain}\nDossier: {json.dumps(dossier, default=str)[:4000]}\n"
        f"Tools that succeeded: {evidence['tools_succeeded']}\n"
        f"Tools that failed: {json.dumps(evidence['tool_failures'], default=str)[:1500]}"
    )
    resp = llm.chat.completions.create(
        model=settings.model,
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_json_object(resp.choices[0].message.content or "")
