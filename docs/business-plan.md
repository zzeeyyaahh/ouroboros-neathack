# Business plan (cfo.ai model)

Source of truth for the cfo.ai model. Items marked TO FILL get real numbers from live runs (`scripts/trace_costs.py`), the neatlogs dashboard, and the Crustdata dashboard once API keys are in. Prices and scenario splits below are proposed model inputs, labeled as such, not measured results.

## Product

Company dossiers produced by an agent that verifies its own work and heals its own failures. Buyers: sales teams, recruiters, and investors who do account research by hand today.

## Sourced cost inputs

| Input | Value | Source |
|---|---|---|
| OpenAI gpt-6.1-sol (standard tier) | $2.00 / 1M input tokens, $10.00 / 1M output tokens | [OpenAI API pricing](https://developers.openai.com/api/docs/pricing), fetched 2026-10-10 |
| OpenAI gpt-6-luna (standard tier) | $0.10 / 1M input, $0.50 / 1M output | same page |
| OpenAI gpt-6-astra (standard tier) | $10.00 / 1M input, $50.00 / 1M output | same page |
| gpt-4o (current worker default via `OURO_MODEL`) | ~$2.50 / 1M input, $10.00 / 1M output, third-party trackers, verify at signup | not listed on the current official page |
| Crustdata | credit-based, no public per-credit dollar figure | [crustdata.com/pricing](https://crustdata.com/pricing) |

Model choice is the main inference cost lever: at equal token counts, luna-class models cut LLM cost per dossier by roughly 20x versus astra-class. Switching `OURO_MODEL` after the first live run is a one-line change with a traceable before/after cost pair.

## Unit economics (per dossier)

| Line | Value | Source |
|---|---|---|
| LLM prompt tokens | TO FILL | `trace_costs.py` `prompt_tokens_total / runs` |
| LLM completion tokens | TO FILL | `trace_costs.py` `completion_tokens_total / runs` |
| LLM cost | TO FILL | tokens x rates above |
| Crustdata credits per dossier | TO FILL | Crustdata dashboard consumption |
| Supervisor overhead multiplier | 1 + heal rate | `trace_costs.py` failures_by_http_status + healed count |
| **Cost per successful dossier** | TO FILL | sum of the above |

Worked example, assumptions until live data lands: 30k prompt + 3k completion tokens per dossier.

- at gpt-6.1-sol rates: 30,000 / 1M x $2.00 = $0.060, plus 3,000 / 1M x $10.00 = $0.030, so $0.090 before heals and data credits
- at third-party gpt-4o rates: $0.075 + $0.030 = $0.105 before heals and data credits

## Pricing (proposed model inputs)

| Plan | Price | Per-dossier revenue | Includes |
|---|---|---|---|
| Free | $0 | $0 | 1 dossier, no supervisor |
| Pro | $29/mo | $29 / 50 = $0.58 | 50 dossiers, auto-heal, exports |
| Team | $99/mo | $99 / 300 = $0.33 | 300 dossiers, batch mode, shared state |

## Revenue scenarios (inputs for cfo.ai)

Mix assumption, stated so the math is checkable: 70% of customers on Pro, 30% on Team. Revenue = Pro customers x $29 + Team customers x $99. Dossiers = Pro customers x 50 + Team customers x 300.

| Scenario | Customers | Mix | Revenue / mo | Dossiers / mo |
|---|---|---|---|---|
| Base | 100 | 70 Pro + 30 Team | 70 x 29 + 30 x 99 = $5,000 | 70 x 50 + 30 x 300 = 12,500 |
| Growth | 250 | 150 Pro + 100 Team | 150 x 29 + 100 x 99 = $14,250 | 150 x 50 + 100 x 300 = 37,500 |

Cost of goods per scenario = dossiers x cost per successful dossier (TO FILL). Enter both scenarios in cfo.ai, record the resulting gross margin and break-even customer count, and paste the cfo.ai outputs back into this file.

## Runway

- Build cost so far: TO FILL (hackathon credits consumed: Crustdata 5,000 credits, neatlogs Pro 3 months for winners, model spend TO FILL)
- Position at submission: pre-seed, self-funded, hackathon credits carry the first months of operation
- Break-even customer count: TO FILL (fixed infra / contribution margin per customer, from cfo.ai)

## Why the self-healing agent matters commercially

A failed dossier costs a full extra run. The supervisor converts failures into automatic retries with backoff and prompt revisions, so the effective cost per successful dossier stays near the clean-run cost instead of inflating with the failure rate. Every healed failure is documented with a before/after trace pair (success rate, duration, token cost), which is both the demo and the margin defense in the cfo.ai model.
