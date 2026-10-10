# Submission checklist — neatHack 2026

Deadline: **Monday 12 Oct, 7:00–11:55 PM IST**. Submit early at 7 PM; hard stop for being ready: noon IST.

## Mechanics

- [ ] Quote-tweet the official neatlogs post with: team *um*, name, project name, public repo URL, demo video URL
- [ ] Submit via the hackathon submission form (check hackathon page for the link)
- [ ] Post in Discord #submissions if that's the channel the organisers name

## Judging evidence map

| Criterion (weight) | Evidence artifact | Where |
|---|---|---|
| The agent (30%) | before/after run pair with compared numbers: success rate, duration, failure counts | `state/runs.jsonl`, `out/*/run.json`, demo video |
| Use of neatlogs/Entire/cfo.ai (25%) | T1 + T2 trace links (span trees, tokens, cost); Entire checkpoint link `entire.io/gh/<owner>/<repo>/commit/<SHA>`; business plan in submission | neatlogs dashboard, Entire, docs/business-plan.md |
| Demo video (20%) | 3-min video following docs/demo-script.md | YouTube/Loom link |
| Building in public (15%) | 3+ posts tagged #neatHack (incl. the failure moment), Discord activity | X + Discord links |
| Usefulness/originality (10%) | README problem statement + demo narrative | README.md |

## Pre-submission gates

- [ ] `ouro doctor` output: neatlogs probe PASS + Crustdata endpoint list
- [ ] At least two improvement loops with before/after evidence (T1→T2, T3→T4)
- [ ] Public repo with commits dated Oct 10–12 only for hackathon work (initial scaffold IS hackathon work — fine)
- [ ] Business plan TO FILLs resolved with live numbers
- [ ] hackathon.md build log complete with evidence links
- [ ] Demo video uploaded and link verified unlisted-accessible
