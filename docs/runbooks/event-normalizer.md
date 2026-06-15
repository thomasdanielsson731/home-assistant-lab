# Event Normalizer Runbook

Danielsson Home Intelligence — MQTT → canonical events + metrics.

**Production:** runs inside the **Danielsson Insights add-on** on HAOS. Event files: `/share/danielsson-insights/events/`.

## What It Does

`scripts/event_normalizer.py` subscribes to Mosquitto and writes to `events/`:

| MQTT topic | Output | Notes |
|---|---|---|
| `frigate/events` | `person`, `vehicle` | On `type: end` only |
| `axis/driveway_env/air/#` | `environment` + metrics | Every 15 min |
| `axis/+/audio/spl` | `metrics.jsonl` | SPL every 5 min per zone |
| `axis/+/scene/frame` | `scene` | On detection count change |
| `axis/+/event/ObjectAnalytics/ScenarioOccupancy/#` | `occupancy` | PersonOccupancy start/end only (≥120 s, 90 s cooldown; VehicleOcc skipped) |
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

Timeline UI: HA sidebar **Analytics** or `http://192.168.68.175:8765/timeline` · API: `/api/v1/*`

Event JSON and media are gitignored.

## Prerequisites

```powershell
pip install requests paho-mqtt python-dotenv
```

`.env` must include `MQTT_USER`, `MQTT_PASS`, `HA_HOST`. Optional: `HA_TOKEN` (snapshot download via HA Frigate proxy).

## Run

**Production (HAOS add-on):** automatic when Danielsson Insights is started.

**Dev / debug only:**

```powershell
python scripts/event_normalizer.py
```

Deploy script changes:

```powershell
.\scripts\deploy-insights-to-ha.ps1
ha apps restart 25d01a20_danielsson_insights   # on HA via SSH
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
| No environment events | Ensure add-on is started; check `air_quality_bridge` in add-on logs |

## Tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

38 tests cover event store, normalizer handlers, and timeline server. CI enforces ≥85% coverage on the three scripts.

## Next Steps

- Grafana dashboards for InfluxDB metrics
- Event rate baselines (zone × hour)
- Nightly aggregate job + AI summaries
