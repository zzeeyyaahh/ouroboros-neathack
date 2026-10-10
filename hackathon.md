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

### Later on Day 1: watch daemon + failure-kind hardening

- Watch daemon (`ouro watch --once` / `--interval N`): polls the run log, heals each *new* failure exactly once, tracks state in `state/watch_state.json`. Verified via CLI: seeded failure → cycle 1 healed it → cycle 2 healed nothing (dedup confirmed).
- Tool-failure taxonomy: failures now carry `kind` (`http`, `network`, `invalid_args`) so the supervisor classifies malformed LLM tool calls (`invalid_args` → `revise_tool_args`) instead of crashing the run — regression tests added. 20 tests green, ruff clean.

### Later on Day 1: Entire checkpoint capture (root cause)

- Symptom: `entire session list` empty and `entire checkpoint list` shows 0 after every commit.
- Cause: the Entire opencode plugin lives at `.opencode/plugins/entire.ts` inside this repo, but the opencode session driving the build runs with project root `/Users/sathwik` (home), so the plugin never loads and no session hooks fire. Git hooks work; session capture does not.
- Fix for future sessions: launch opencode from inside the repo (`cd ~/ouroboros && opencode`) so the plugin loads and checkpoints attach automatically.
- For this session: attach manually via `entire session attach <session-id> --agent opencode`.
- Safety gate: an earlier debug command printed a TinyFish API key into this session's transcript. Before any attach is pushed, redaction rules in `.entire/settings.local.json` (untracked) must strip it, verified by grepping the checkpoint ref for the key prefix. `strategy_options.push_sessions` is also `false` so raw session logs never auto-push.
- **Outcome**: attached session `ses_edb2b8d9fffeh2VUE94nABtTOh` → checkpoint `01M4JKMTFRFR19HC9RQWX942M2` on commit `b4aea17` (trailer added). Redaction verified before push: exact key 0 matches, key-shaped tokens 0, REDACTED tokens 15+3 — safe to publish. Checkpoint link recorded in docs/submission.md.
