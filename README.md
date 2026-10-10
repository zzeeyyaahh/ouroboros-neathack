# Ouroboros

An agent pipeline that watches itself die, then fixes itself.

**neatHack 2026 project (team *um*, solo build).** Built for the "Build an agent that works (literally)" track.

## The idea

Most agent demos show the happy path. Ouroboros treats failure as the feature:

1. **Worker** (`ouro/worker/dossier.py`) — given a company domain, it plans, calls Crustdata tools (identify → enrich → people → web search), and synthesizes a verified company dossier. Every LLM call, tool call, and failure is traced in **neatlogs**.
2. **Supervisor** (`ouro/supervisor/heal.py`) — reads the worker's run log and its *own* neatlogs traces, classifies each failure (429s, missing data, verification gaps), picks a remediation, re-runs, and verifies the fix.

The judges' hard-to-fake evidence — *a run where an action failed, showing what the agent did next* — is the product itself.

## Docs

- `hackathon.md` — the build log (dated entries, evidence links)
- `docs/business-plan.md` — cfo.ai unit economics, pricing, runway (numbers pulled from trace costs)
- `docs/demo-script.md` — 3-minute demo narration and recording checklist
- `docs/submission.md` — judging-criteria evidence map and pre-submission gates

## Layout

```
ouro/
├── worker/dossier.py     # dossier agent: plan -> tools -> synthesize -> verify
├── supervisor/heal.py    # trace/run-log reader, failure classifier, remediation
├── tools/crustdata.py    # Crustdata API client (with optional fault injection)
├── state.py              # JSONL run log (state across runs)
└── trace.py              # neatlogs init/shutdown
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env   # fill in keys
```

Env vars:

| Var | Where from |
|---|---|
| `CRUSTDATA_API_KEY` | Crustdata dashboard (hackathon promo code `NEATLOGS-OCT2026`) |
| `OPENAI_API_KEY` | OpenAI |
| `NEATLOGS_API_KEY` | app.neatlogs.com → Settings → API keys → **top** key (Project API key, not the `nlw_` ingest key) |

Optional: `OURO_MODEL` (default `gpt-4o`), `OURO_FAULT_INJECT=1` (deterministic first-call 429 per endpoint, for repeatable demo runs).

## Usage

```bash
.venv/bin/python -m ouro doctor                      # keys + neatlogs probe + crustdata endpoint access
.venv/bin/python -m ouro run crustdata.com           # one dossier (traced)
.venv/bin/python -m ouro batch a.com,b.com           # batch, state across runs
.venv/bin/python -m ouro runs                        # run log summary
.venv/bin/python -m ouro supervise --window-hours 24  # classify failures, remediate, rerun, compare
```

Outputs land in `out/<domain>/<run_id>/` (`dossier.json`, `run.json`); the run log is `state/runs.jsonl`.

### Offline demo (no keys, no network)

```bash
bash scripts/demo.sh
```

`OURO_MOCK=1` swaps the LLM and Crustdata client for deterministic fakes; `OURO_FAULT_INJECT=1` makes the first call to each endpoint 429, so the demo shows the full loop: baseline failure → supervisor classification → `retry_with_backoff` rerun → healed.

`scripts/trace_costs.py` aggregates `out/**/run.json` into success rate, failure counts, token usage, and durations — the inputs for the cfo.ai unit-economics model.

## Tests

```bash
.venv/bin/pytest -q   # offline: state log, fault injection, schema validation
```
