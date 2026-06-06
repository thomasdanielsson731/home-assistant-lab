# Danielsson Insights — Analytics

Event-first analytics platform documentation. Home Assistant is the **ingestion layer**; this is the **insights layer**.

```
Sources → Events → Storage → Aggregates → Views (Timeline / Floorplan / Dashboard / AI)
```

## Documents

| File | Purpose |
|---|---|
| [event-model.md](event-model.md) | Canonical event schema — read this first |
| [event-taxonomy.md](event-taxonomy.md) | Event types, lifecycle, zones, cameras |
| [timeline.md](timeline.md) | Timeline view design |
| [floorplan.md](floorplan.md) | Floorplan and property map layers |
| [bicycle-analytics.md](bicycle-analytics.md) | Bicycle trip detection and attribution |
| [cat-analytics.md](cat-analytics.md) | Cat visit tracking |
| [ai-insights.md](ai-insights.md) | AI enrichment and summaries |

## Implementation Status

| Component | Status | Notes |
|---|---|---|
| Event schema defined | ✅ | `schemas/danielsson-event.schema.json` |
| Event store | ⬜ | Phase 7 — InfluxDB or SQLite/JSONL |
| HA → Event normalizer | ⬜ | Bridge scripts publish MQTT; normalizer TBD |
| Timeline UI | ⬜ | Design complete, not built |
| Floorplan UI | ⬜ | Design complete, not built |
| Daily aggregates | ⬜ | Phase 7 |
| AI enrichment | ⬜ | Phase 6 |

## For AI Assistants

Before building dashboards or YAML, ask: **does this produce or consume an Event?**

If it only adds another HA entity without fitting the event model, defer it.

See [../vision/danielsson-insights.md](../vision/danielsson-insights.md) for Cursor prompts.
