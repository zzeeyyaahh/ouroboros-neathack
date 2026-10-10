# Public build posts (#neatHack)

Drafts for the "building in public" criterion (15%). Rules applied: no em dash, no buzzwords, no fabricated numbers or claims. Every fact below is real and checkable in the repo or run log.

## Post 1: the failure moment (Day 1 evening)

```
#neatHack day 1, team um: my dossier agent failed its first full run. Every Crustdata endpoint returned 429, it gathered no evidence, and its own verification rejected the output.

Keeping the red trace. The fix is the project.

github.com/zzeeyzaahh/ouroboros-neathack
```

Attach: screenshot of the failing run (`state/runs.jsonl` entry with `status: failed`, 429 tool failures).

## Post 2: the heal (Day 2 morning)

```
#neatHack day 2: the supervisor read that failed run, classified the 429s, retried with backoff, and reran.

Every tool call succeeded and verification passed: healed: true.

Checkpoint 01M4JKMTFRFR19HC9RQWX942M2: github.com/zzeeyzaahh/ouroboros-neathack
```

Attach: the before/after run summary from `ouro runs`, or the two neatlogs traces.

Note: confirm the checkpoint link opens for a logged-out viewer before posting. It needs the `entire login` + repo connection steps from the handoff. If it does not open yet, post the checkpoint ID (`01M4JKMTFRFR19HC9RQWX942M2`) and the repo link instead.

## Post 3: the stack (Day 2 evening)

```
What team um is building at #neatHack: an agent that watches its own failures and heals them.

neatlogs traces on every run, Entire checkpoints on every fix, cfo.ai economics from per-run token costs. 20 offline tests keep it honest.

github.com/zzeeyzaahh/ouroboros-neathack
```

Attach: `bash scripts/demo.sh --fresh` terminal recording, or the repo README card.

## Before posting

- [ ] Each post checked against the checklist: no em dashes, no "AI-powered / seamless / revolutionary" language, no invented stats
- [ ] Claimed evidence (healed run, checkpoint, tests) is real at posting time
- [ ] Post 1 goes out after the first failing run exists; Post 2 only after a real healed pair
- [ ] Tag the official neatlogs post where the hackathon guide asks for a quote-tweet at submission time
