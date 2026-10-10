# hackathon.md — neatHack build log

- Project: Ouroboros — a self-watching agent pipeline: a dossier worker that traces every run in neatlogs, and a supervisor that reads its own traces to classify failures, remediate, and verify fixes.
- Team: um (solo — Sathwik Giddi)
- Stack: Python 3.14, OpenAI (tool-calling loop), Crustdata API (company/people/web endpoints), neatlogs SDK + CLI, Entire checkpoints, cfo.ai (business plan)
- Build log: (dated entries below)
- Demo: (URL + instructions when available)
- Known limitations and next steps: (filled in during build)
- Submission: (confirmed requirements and outstanding items)

## 2026-10-10 (Day 1)

- Repo scaffolded: worker (dossier agent), supervisor skeleton, Crustdata client, JSONL state log, neatlogs tracing hooks, offline tests. All tests passing.
- Locked concept: self-watching pipeline; failure evidence is the product.
- Enabled Entire checkpoint tracking for opencode; CLI installed and enabled on the repo (Entire CLI 0.11.4). neatlogs CLI 0.2.0 installed and profile `work` configured.
- Worker v1: tool-calling loop (identify → enrich → people → web search) → dossier synthesis → LLM verification pass against evidence. Run records (status, duration, tool failures, schema/verify issues, usage, remediation applied) written to state/runs.jsonl.
- Supervisor v1: classifies failures from the run log (429 → retry_with_backoff, verify/schema issues → revise_synthesis_prompt, etc.), remediates, reruns, and records before/after comparison.
- Offline proof of the loop (OURO_MOCK=1 + OURO_FAULT_INJECT=1): baseline run failed with 4× 429s and no evidence; supervisor reran with backoff → success ("healed": true). 14 tests green, ruff clean.
- Blocker: .env key names present but values empty — awaiting user signups (Crustdata promo NEATLOGS-OCT2026, neatlogs Project API key, OpenAI key) for live runs.
