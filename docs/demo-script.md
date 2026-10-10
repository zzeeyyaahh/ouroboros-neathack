# Demo video script (3 minutes)

Record Monday morning. Two segments: offline deterministic loop (exact reproduction) + live runs with real traces.

## 0:00–0:25 — Hook

"Most agent demos show the happy path. I built one that watches itself fail and fixes itself." Show the red failing run: injected 429s, no evidence gathered, dossier rejected by verification.

## 0:25–1:00 — Architecture

Four boxes: Worker (plan → Crustdata tools → dossier → verify), Supervisor (reads the run log + its own neatlogs traces → classifies → remediates → reruns), Watch daemon (polls the run log, heals each new failure once), Evidence (neatlogs traces, Entire checkpoints, run.json before/after).

## 1:00–1:30 — The heal

Run `bash scripts/demo.sh --fresh` (or live pair with `scripts/demo_live.sh`): baseline failure T1 → supervisor classifies 429 → `retry_with_backoff` → T2 success. Show `healed: true` and the before/after summary. Open the neatlogs trace for both runs: span tree, failed tool span, then green.

## 1:30–1:50 — Background healing (watch daemon)

Seed another failure, then `ouro watch --once`: it finds and heals the new failure with no human prompt. Second cycle: `seen: []` — each failure is healed exactly once, tracked in `state/watch_state.json`. This is the "watch a running system" pattern from the hackathon brief.

## 1:45–2:20 — Tool evidence (25% of the score)

- neatlogs: both trace links, span trees, tokens/cost per run — the inputs to the business model
- Entire: checkpoint link(s) showing the fix commit with session context; `entire checkpoint explain HEAD`
- cfo.ai: business plan numbers pulled from trace costs (cost per dossier → pricing → margin)

## 2:20–2:50 — Close

Why it matters: the judges' hardest-to-fake evidence — "a run where an action failed, showing what the agent did next" — is the product. Repo + hackathon.md build log + Discord handle. "Team um, Ouroboros."

## Recording checklist

- [ ] Terminal font ≥ 16pt, clean background
- [ ] Run demo before recording (warm caches, no stale state)
- [ ] neatlogs dashboard visible for both T1 and T2
- [ ] Entire checkpoint link ready to paste
- [ ] Keep under 3:00
