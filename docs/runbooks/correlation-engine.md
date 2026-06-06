# Correlation Engine Runbook

Phase 7e — derive enriched events from raw timeline events.

## Module

`scripts/correlation_engine.py` — invoked automatically by `event_normalizer.py` after each raw event is stored (and after Double Take identity attach).

## Rules (v1)

| Enriched type | Trigger | Conditions | Cooldown |
|---|---|---|---|
| `delivery` | person, vehicle, or scene at `front`/`driveway` | person + vehicle in 10 min, OR scene with persons≥1 and vehicles≥1 | 20 min |
| `arrival` | identified person at entrance | `identity.name` at `front` or `driveway` | 30 min per person |
| `arrival` | vehicle then person | vehicle + person within 2 min at entrance zones | 30 min |

Enriched events include:

- `enriched: true`
- `parent_event_ids: [...]`
- `metadata.correlations` — linked raw events with offset seconds
- `source: correlation_engine`

## Output

Written to the same event store as raw events (`events/timeline.jsonl`, `events/arrival/`, `events/delivery/`).

Visible on **House Intelligence Timeline** (`/timeline`) in `arrival` and `delivery` lanes.

## Future rules

- `bicycle` — person + two-wheel shape + optional door unlock
- `door` events from Yale Doorman → strengthen `arrival` correlation
- LLM enrichment (`ai_summary`) in Phase 6

## Manual test

```powershell
python scripts/event_normalizer.py
# Trigger Frigate person + vehicle at front within 10 min
# Check http://localhost:8765/timeline for delivery/arrival entries
```
