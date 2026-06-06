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
| Event store (JSONL) | ✅ v0 | `events/timeline.jsonl` + per-type folders |
| HA → Event normalizer | ✅ v0 | `scripts/event_normalizer.py` — Frigate, DT, D6210 |
| Timeline UI | ✅ v1 | `:8765/timeline` + HA sidebar `house-timeline` |
| Correlation engine | ✅ | `arrival`, `delivery`, `bicycle`, door boost |
| InfluxDB bridge | ✅ ready | `influx_metrics_bridge.py` |
| Floorplan UI | ⬜ | Design complete, not built |
| Daily aggregates | ✅ v0 | `events/aggregates/` updated on each event |
| AI enrichment | ⬜ | Phase 6 |

## For AI Assistants

Before building dashboards or YAML, ask: **does this produce or consume an Event?**

If it only adds another HA entity without fitting the event model, defer it.

See [../vision/danielsson-insights.md](../vision/danielsson-insights.md) for Cursor prompts.
