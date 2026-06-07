# Event Normalizer Runbook

Danielsson Home Intelligence — MQTT → canonical events + metrics on the dev PC.

## What It Does

`scripts/event_normalizer.py` subscribes to Mosquitto and writes to `events/`:

| MQTT topic | Output | Notes |
|---|---|---|
| `frigate/events` | `person`, `vehicle` | On `type: end` only |
| `double_take/matches` | identity enrichment | Attaches name to recent person event |
| `axis/driveway_env/air/#` | `environment` + metrics | Every 15 min |
| `axis/+/audio/spl` | `metrics.jsonl` | SPL every 5 min per zone |
| `axis/+/scene/frame` | `scene` | On detection count change |
| `axis/+/event/ObjectAnalytics/ScenarioOccupancy/#` | `occupancy` | Start/end blocks for timeline |
| `homeassistant/lock/+/state` | `door` | Lock/unlock — map `YALE_LOCK_ENTITIES` in `.env` |

After each raw event, `correlation_engine.py` may write enriched `arrival`, `delivery`, or `bicycle` events.

Output:

```
events/
├── timeline.jsonl          # Point events
├── metrics.jsonl           # Continuous metrics (env, SPL)
├── aggregates/YYYY-MM-DD.json
└── {type}/YYYY/MM/DD/{event_id}.json
```

Timeline UI: HA sidebar **Analytics** or `http://192.168.68.136:8765/timeline` · API: `/api/v1/*`

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

## Timeline UI

```powershell
.\scripts\start-bridges.ps1
# HA: sidebar → Timeline
# Or direct: http://localhost:8765/timeline
# LAN clients: .\scripts\open-timeline-firewall.ps1 (run as Administrator once)
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
