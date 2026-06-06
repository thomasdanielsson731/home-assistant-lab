# Event Normalizer Runbook

Danielsson Insights Phase 7 v0 — MQTT → canonical JSON events on the dev PC.

## What It Does

`scripts/event_normalizer.py` subscribes to Mosquitto and writes events to `events/`:

| MQTT topic | Event type | Notes |
|---|---|---|
| `frigate/events` | `person`, `vehicle` | On `type: end` only (one event per track) |
| `double_take/matches` | identity enrichment | Attaches name to recent person event |
| `axis/driveway_env/air/#` | `environment` | Snapshot every 15 min |

Output:

```
events/
├── timeline.jsonl          # Append-only log for Timeline v0
├── aggregates/YYYY-MM-DD.json
└── {type}/YYYY/MM/DD/{event_id}.json
```

Event JSON and media are gitignored.

## Prerequisites

```powershell
pip install requests paho-mqtt python-dotenv
```

`.env` must include `MQTT_USER`, `MQTT_PASS`, `HA_HOST`. Optional: `HA_TOKEN` (snapshot download via HA Frigate proxy).

## Run

```powershell
# Manual
python scripts/event_normalizer.py

# With other bridges
.\scripts\start-bridges.ps1

# Scheduled (on logon)
.\scripts\install-scheduled-tasks.ps1
```

## Timeline v0

```powershell
python scripts/timeline_server.py
# Open http://localhost:8765
```

## Verify

1. Walk in front of `front` camera — wait for Frigate track to end (~5–10 s).
2. Check `events/timeline.jsonl` for a new `person` line.
3. Open Timeline UI — event should appear with summary and optional snapshot.

Environment events appear within 15 min of air quality bridge running.

## Troubleshooting

| Symptom | Fix |
|---|---|
| No Frigate events | Confirm Frigate is detecting (`http://192.168.68.175:5000`) |
| No snapshots | Set `HA_TOKEN` in `.env`; verify `/api/frigate/notifications/{id}/snapshot.jpg` |
| Duplicate events | Dedup window is 30 s per camera+type; adjust in `EventStore` |
| No environment events | Ensure `air_quality_bridge.py` is running and publishing |

## Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

38 tests cover event store, normalizer handlers, and timeline server. CI enforces ≥85% coverage on the three scripts.

## Next Steps (Phase 7)

- InfluxDB time-series for metrics
- AOA/scene → person events (lower latency than Frigate)
- Delivery detection from scene dwell automations
- Nightly aggregate job + AI summaries
