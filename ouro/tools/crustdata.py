from __future__ import annotations

import time
from typing import Any

import httpx

from ..config import settings

BASE_URL = "https://api.crustdata.com"
API_VERSION = "2025-11-01"


class CrustdataError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class CrustdataClient:
    def __init__(self, token: str | None = None, http: httpx.Client | None = None) -> None:
        self.token = token if token is not None else settings.crustdata_api_key
        self.fault_inject = settings.fault_inject
        self.calls: list[dict[str, Any]] = []
        self._http = http

    def _client(self) -> httpx.Client:
        if self._http is not None:
            return self._http
        return httpx.Client(base_url=BASE_URL, timeout=30.0)

    def _headers(self) -> dict[str, str]:
        return {
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            "x-api-version": API_VERSION,
        }

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        record: dict[str, Any] = {"path": path, "payload_keys": sorted(payload), "status": None, "error": None}
        self.calls.append(record)
        try:
            self._maybe_inject_fault(path)
            owns_client = self._http is None
            http = self._client()
            try:
                response = http.post(path, json=payload, headers=self._headers())
            finally:
                if owns_client:
                    http.close()
            record["status"] = response.status_code
            if response.status_code >= 400:
                record["error"] = response.text[:300]
                raise CrustdataError(f"{path} -> HTTP {response.status_code}", status=response.status_code, body=response.text[:300])
            record["latency_ms"] = round((time.monotonic() - started) * 1000)
            return response.json()
        except CrustdataError:
            raise
        except httpx.HTTPError as exc:
            record["error"] = str(exc)
            raise CrustdataError(str(exc)) from exc

    def _maybe_inject_fault(self, path: str) -> None:
        if not self.fault_inject:
            return
        seen = sum(1 for c in self.calls if c["path"] == path)
        if seen <= 1:
            record = self.calls[-1]
            record["status"] = 429
            record["error"] = "rate_limited (injected)"
            raise CrustdataError("rate_limited (injected)", status=429, body="injected 429 for demo")

    def identify(self, domain: str) -> dict[str, Any]:
        return self.post("/company/identify", {"domains": [domain]})

    def enrich(self, company_id: str | None = None, domain: str | None = None) -> dict[str, Any]:
        if company_id:
            return self.post("/company/enrich", {"company_id": company_id})
        return self.post("/company/enrich", {"domains": [domain]})

    def search_people(self, company_id: str, limit: int = 10) -> dict[str, Any]:
        return self.post(
            "/person/search",
            {"filters": [{"filter_type": "COMPANY_ID", "type": "in", "value": [company_id]}], "page": 1, "limit": limit},
        )

    def web_search(self, query: str) -> dict[str, Any]:
        return self.post("/web/search/live", {"query": query})

    def account_endpoints(self) -> dict[str, Any]:
        return self.post("/account/endpoints", {})
