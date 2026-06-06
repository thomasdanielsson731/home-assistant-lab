# Danielsson Home Intelligence

The Danielsson Home project is evolving from a smart home platform into a **Home Intelligence Platform** (Danielsson Insights in code/docs).

```
Collect → Enrich → Analyze → Visualize → Understand
```

**Focus:** event collection, correlation, timeline API, House Intelligence Timeline UI, metrics layer, AI insights.

**Primary UX:** House Intelligence Timeline — HA sidebar **Timeline** (`house-timeline`) or `http://192.168.68.118:8765/timeline` on dev PC.

**Not:** lamp automation (HomeKit handles that). The goal is understanding what happens around the house.

---

## Infrastructure (today)

| Layer | Technology | Role in Insights |
|---|---|---|
| Event hub | Home Assistant OS | State + automation trigger, not the analytics store |
| Vision | Frigate + 6× Axis cameras | Detections, snapshots, clips |
| On-camera analytics | Axis AOA + scene metadata | Fast presence, counts |
| Face context | Double Take + CodeProject.AI | Person identity |
| Access | Yale Doorman V3 (hardware pending) | Door events via HA MQTT (`door` type live in normalizer) |
| Environment | D6210 via MQTT bridge | Environmental events |
| Future | Zigbee, custom ACAP models | Smoke, cat |

---

## Focus Domains

| Domain | Event type | Status |
|---|---|---|
| Persons | `person` | Frigate + AOA live; face recognition in progress |
| Vehicles | `vehicle` | Frigate + AOA on driveway cameras |
| Bicycles | `bicycle` | Live — correlation engine (person + scene bike + optional door) |
| Cats | `cat` | Planned — custom model or Frigate label |
| Deliveries | `delivery` | Live — correlation engine + scene automation |
| Arrivals | `arrival` | Live — identity, vehicle→person, door unlock |
| Environment | `environment` | D6210 live via `air_quality_bridge.py` |
| Doors | `door` | Live — `homeassistant/lock/+/state` (map `YALE_LOCK_ENTITIES`) |
| Smoke | `smoke` | Future Zigbee |

---

## Cursor / Codex Prompts

Use these when starting a new analytics task. Read [event-model.md](../analytics/event-model.md) first.

### Prompt 1 — Vision and Architecture

> You are the lead architect for Danielsson Insights.
>
> This is not primarily a home automation project. Build a Home Analytics Platform that collects, enriches, visualizes and analyzes activity around a private home.
>
> Generate: (1) high-level architecture, (2) event model, (3) data model, (4) metadata strategy, (5) dashboard strategy, (6) timeline strategy, (7) future AI enrichment strategy.
>
> Avoid traditional home automation unless it contributes to analytics.

### Prompt 2 — Event Store

> Design an event-centric architecture. Every event: timestamp, location, camera, object type, confidence, snapshot, metadata.
>
> Generate: JSON schema, event taxonomy, event lifecycle, retention strategy, best-picture strategy.

### Prompt 3 — Timeline Dashboard

> Design a timeline dashboard. Display: timestamp, best picture, event type, enriched metadata, AI description.
>
> Example: `18:12 Nils arrived home by bicycle` · `19:42 Neighbour cat visited backyard`
>
> Generate: UX design, data model, dashboard layout, implementation options.

### Prompt 4 — Floorplan Analytics

> Design a floorplan analytics view — not automation. Visualize activity, detections, events, environmental data.
>
> Layers: house floorplan, property map, camera coverage, event heatmaps.

### Prompt 5 — Cat Analytics

> Track neighbouring cat visits. Input: Axis + Frigate (+ future custom model). Output: visit timeline, active cats, duration, heatmaps, weekly reports.

### Prompt 6 — Bicycle Analytics

> Understand family mobility. Input: camera detections, face recognition, Yale lock events. Output: trips, person attribution, weekly/seasonal trends.

---

## Core Rule

**Everything is an event.** Timeline, dashboards, floorplans, and AI insights consume the same [event model](../analytics/event-model.md) — not separate HA entity silos.

---

## Related Documents

| Document | Purpose |
|---|---|
| [event-model.md](../analytics/event-model.md) | Canonical event schema |
| [event-taxonomy.md](../analytics/event-taxonomy.md) | Types, lifecycle, retention |
| [timeline.md](../analytics/timeline.md) | Timeline UX and data model |
| [floorplan.md](../analytics/floorplan.md) | Floorplan layers |
| [ai-insights.md](../analytics/ai-insights.md) | Enrichment and NL queries |
| [../vision.md](../vision.md) | Lab vision and phase map |
