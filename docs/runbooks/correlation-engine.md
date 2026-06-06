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
| `arrival` | door unlock | person at `front`/`driveway` within 5 min before unlock; named person uses `door_unlock`, with vehicle uses `door_unlock_vehicle_person` | 30 min |
| `bicycle` | person, scene, bicycle, or door | person + bike signal (Frigate `bicycle` or scene `bicycles`≥1) at `front`/`driveway`/`driveway_id` within 5 min; door unlock adds `correlated_door_unlock` | 20 min |

Enriched events include:

- `enriched: true`
- `parent_event_ids: [...]`
- `metadata.correlations` — linked raw events with offset seconds
- `source: correlation_engine`

## Output

Written to the same event store as raw events (`events/timeline.jsonl`, `events/arrival/`, `events/delivery/`).

Visible on **House Intelligence Timeline** (`/timeline`) in `arrival`, `delivery`, `bicycle`, and `door` lanes.

## Door ingestion

`event_normalizer.py` subscribes to `homeassistant/lock/+/state` (HA MQTT discovery). Map entities in `.env`:

```
YALE_LOCK_ENTITIES=front_door:front,yale_doorman:front
```

Emits raw `door` events on lock state transitions (`locked` / `unlocked`).

## Future rules

- LLM enrichment (`ai_summary`) in Phase 6

## Manual test

```powershell
python scripts/event_normalizer.py
# Trigger Frigate person + vehicle at front within 10 min
# HA sidebar → Timeline, or http://192.168.68.118:8765/timeline
```
