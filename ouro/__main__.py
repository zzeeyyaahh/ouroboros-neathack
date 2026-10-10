from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid

from .config import settings
from .state import read_runs
from .trace import init_tracing, shutdown_tracing
from .worker import run_dossier


def _doctor() -> int:
    print(f"model:                {settings.model}")
    print(f"OPENAI_API_KEY:       {'set' if settings.openai_api_key else 'MISSING'}")
    print(f"NEATLOGS_API_KEY:     {'set' if settings.neatlogs_api_key else 'MISSING'}")
    print(f"CRUSTDATA_API_KEY:    {'set' if settings.crustdata_api_key else 'MISSING'}")
    print(f"OURO_FAULT_INJECT:    {settings.fault_inject}")

    if settings.neatlogs_api_key:
        proc = subprocess.run(
            [sys.executable, "-m", "neatlogs", "doctor", "--probe"],
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )
        print("\n--- neatlogs doctor --probe ---")
        print(proc.stdout.strip() or proc.stderr.strip())

    if settings.crustdata_api_key:
        from .tools.crustdata import CrustdataClient, CrustdataError

        client = CrustdataClient()
        try:
            endpoints = client.account_endpoints()
            print("\n--- crustdata /account/endpoints ---")
            print(json.dumps(endpoints, indent=2, default=str)[:1500])
        except CrustdataError as exc:
            print(f"\ncrustdata check failed: {exc} (status={exc.status})")

    missing = [n for n, v in [("OPENAI_API_KEY", settings.openai_api_key), ("NEATLOGS_API_KEY", settings.neatlogs_api_key), ("CRUSTDATA_API_KEY", settings.crustdata_api_key)] if not v]
    if missing:
        print(f"\nmissing keys: {', '.join(missing)}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ouro")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run the dossier worker for one domain")
    run_p.add_argument("domain")

    batch_p = sub.add_parser("batch", help="Run the dossier worker for a comma-separated domain list")
    batch_p.add_argument("domains")

    sup_p = sub.add_parser("supervise", help="Watch recent runs and heal failures")
    sup_p.add_argument("--window-hours", type=float, default=24)
    sup_p.add_argument("--dry-run", action="store_true")

    sub.add_parser("doctor", help="Check keys, neatlogs probe, and Crustdata endpoint access")
    sub.add_parser("runs", help="Show the run log")

    args = parser.parse_args(argv)

    if args.command == "doctor":
        return _doctor()
    if args.command == "runs":
        for row in read_runs():
            print(json.dumps({k: row.get(k) for k in ("run_id", "domain", "status", "duration_s")}, default=str))
        return 0

    run_id = uuid.uuid4().hex[:8]
    tracker = init_tracing(run_id)
    try:
        if args.command == "run":
            record = run_dossier(args.domain)
            print(json.dumps({k: record.get(k) for k in ("run_id", "domain", "status", "duration_s", "schema_issues", "verify_issues")}, indent=2))
            return 0 if record["status"] == "success" else 2
        if args.command == "batch":
            domains = [d.strip() for d in args.domains.split(",") if d.strip()]
            records = [run_dossier(d) for d in domains]
            print(json.dumps([{ "domain": r["domain"], "status": r["status"], "run_id": r["run_id"]} for r in records], indent=2))
            return 0 if all(r["status"] == "success" for r in records) else 2
        if args.command == "supervise":
            from .supervisor import supervise

            reports = supervise(args.window_hours, rerun=not args.dry_run)
            print(json.dumps(reports, indent=2, default=str)[:4000])
            return 0
    finally:
        shutdown_tracing(tracker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
