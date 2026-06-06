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

**Not yet implemented.** Events are currently implicit in HA entities and MQTT messages.

Phase 7 will add a normalizer that writes JSON events here (or to InfluxDB/SQLite with media in this tree).

## Schema

See [docs/analytics/event-model.md](../docs/analytics/event-model.md) and [schemas/danielsson-event.schema.json](../schemas/danielsson-event.schema.json).

## Git

Event JSON and media files are **not committed** — add `events/**` to `.gitignore` except this README.
