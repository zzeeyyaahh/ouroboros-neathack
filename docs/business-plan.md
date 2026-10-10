# Business plan (cfo.ai model)

Numbers marked TO FILL come from live runs via `scripts/trace_costs.py` and the neatlogs dashboard (token usage + cost per trace). Pricing/revenue/runway get entered into cfo.ai.

## Product

Company dossiers produced by an agent that verifies its own work and heals its own failures. Runners: sales teams, recruitors, investors doing account research today.

## Unit economics (per dossier)

| Line | Value | Source |
|---|---|---|
| LLM tokens (prompt) | TO FILL | trace_costs.py `prompt_tokens_total / runs` |
| LLM tokens (completion) | TO FILL | trace_costs.py `completion_tokens_total / runs` |
| LLM cost | TO FILL | provider pricing × tokens above |
| Crustdata credits per dossier | TO FILL | Crustdata dashboard consumption |
| Supervisor overhead (heals) | ~1 extra run per failure | heal rate from trace_costs.py |
| **Cost per dossier** | TO FILL | sum of the above |

## Pricing

| Plan | Price | Includes |
|---|---|---|
| Free | $0 | 1 dossier, no supervisor |
| Pro | $29/mo | 50 dossiers, auto-heal, exports |
| Team | $99/mo | 300 dossiers, batch mode, shared state |

## Revenue scenarios (cfo.ai)

| Scenario | Customers | Dossiers/mo | Revenue | Infra+inference | Gross margin |
|---|---|---|---|---|---|
| Base | 100 | 2,000 | $5,800 | TO FILL | TO FILL |
| Growth | 250 | 6,000 | $14,500 | TO FILL | TO FILL |

## Runway

- Build cost so far: TO FILL (credits used during hackathon)
- Position at submission: pre-seed / self-funded, hackathon credits carry first 3 months
- Break-even customer count: TO FILL (fixed infra ÷ contribution margin per customer)

## Why the agent matters commercially

Self-healing directly reduces cost per successful dossier (fewer failed runs, fewer retries by humans) and raises the defensible margin. Every healed failure is measurable: before/after traces with success rate and cost.
