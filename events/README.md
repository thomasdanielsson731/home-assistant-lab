# Event Store

Canonical storage for Danielsson Insights events. Each subfolder holds events of that type.

```
events/
├── person/       # Person detected or identified
├── vehicle/      # Cars, trucks, motorcycles
├── bicycle/      # Bicycle trips with rider attribution
├── cat/          # Cat visits
├── delivery/     # Package and courier events (enriched)
├── arrival/      # Household arrivals (enriched)
├── occupancy/    # AOA duration start/end
├── scene/        # Scene frame detection counts
├── environment/  # D6210 air quality snapshots
├── metrics.jsonl # Continuous env + SPL samples
├── door/         # Yale / HA lock unlock (live via MQTT)
└── smoke/        # Smoke detector alerts (future)
```

## File Layout

```
events/{type}/{yyyy}/{mm}/{dd}/{event_id}.json
events/{type}/{yyyy}/{mm}/{dd}/{event_id}.jpg      # best picture
events/{type}/{yyyy}/{mm}/{dd}/{event_id}_thumb.jpg
```

## Status

**Live** — `scripts/event_normalizer.py` writes from Frigate, Double Take, D6210, AOA, scene, SPL metrics, HA door locks.

- Timeline log: `events/timeline.jsonl`
- Metrics: `events/metrics.jsonl`
- Daily counts: `events/aggregates/YYYY-MM-DD.json`
- Viewer: `timeline_server.py` → `http://localhost:8765/timeline` or HA sidebar **Timeline**
- Correlation: `correlation_engine.py` → enriched `arrival`, `delivery`, `bicycle`
- Long retention: `influx_metrics_bridge.py` (optional)

## Schema

See [docs/analytics/event-model.md](../docs/analytics/event-model.md) and [schemas/danielsson-event.schema.json](../schemas/danielsson-event.schema.json).

## Git

Event JSON and media files are **not committed** — add `events/**` to `.gitignore` except this README.
