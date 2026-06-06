# Event Store

Canonical storage for Danielsson Insights events. Each subfolder holds events of that type.

```
events/
├── person/       # Person detected or identified
├── vehicle/      # Cars, trucks, motorcycles
├── bicycle/      # Bicycle trips with rider attribution
├── cat/          # Cat visits
├── delivery/     # Package and courier events
├── environment/  # D6210 air quality snapshots
├── door/         # Yale lock/unlock (planned)
└── smoke/        # Smoke detector alerts (future)
```

## File Layout (planned)

```
events/{type}/{yyyy}/{mm}/{dd}/{event_id}.json
events/{type}/{yyyy}/{mm}/{dd}/{event_id}.jpg      # best picture
events/{type}/{yyyy}/{mm}/{dd}/{event_id}_thumb.jpg
```

## Status

**v0 implemented** — `scripts/event_normalizer.py` writes JSON events here from Frigate, Double Take, and D6210 MQTT.

- Timeline log: `events/timeline.jsonl`
- Daily counts: `events/aggregates/YYYY-MM-DD.json`
- Viewer: `python scripts/timeline_server.py` → http://localhost:8765

Phase 7 next: InfluxDB/SQLite for time-series; keep media in this tree.

## Schema

See [docs/analytics/event-model.md](../docs/analytics/event-model.md) and [schemas/danielsson-event.schema.json](../schemas/danielsson-event.schema.json).

## Git

Event JSON and media files are **not committed** — add `events/**` to `.gitignore` except this README.
