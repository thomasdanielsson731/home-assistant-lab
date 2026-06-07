# Timeline Design

The timeline is the primary narrative view of Danielsson Insights — a chronological feed of enriched events.

**Implemented (v1):** `scripts/timeline_server.py` — horizontal timeline at `/timeline` with zoom, pan, custom time range, occupancy blocks, env metric overlay. Access via HA sidebar **Analytics** (`house-timeline`) or `http://192.168.68.136:8765/timeline`. List view at `/`.

---

## Purpose

Answer: **"What happened today (or this week)?"**

Not a logbook of HA state changes. A human-readable activity stream with pictures.

---

## Entry Model

```json
{
  "timestamp": "2026-06-06T18:12:00+02:00",
  "type": "bicycle",
  "summary": "Nils arrived home by bicycle",
  "thumbnail": "events/bicycle/2026/06/06/evt_..._thumb.jpg",
  "zone": "driveway",
  "identity": { "person": "Nils" },
  "metadata": { "direction": "arriving" },
  "ai_summary": null,
  "event_id": "evt_..."
}
```

Timeline entries are **projections** of Events — optimized for display, not the canonical store.

---

## UX Layout

```
┌─────────────────────────────────────────┐
│  TIMELINE · Today                       │
├─────────────────────────────────────────┤
│  18:12  [thumb]  Nils arrived by bike   │
│         driveway · bicycle              │
├─────────────────────────────────────────┤
│  18:15  [thumb]  Front door unlocked    │
│         front · door · Thomas           │
├─────────────────────────────────────────┤
│  19:42  [thumb]  Cat visited backyard   │
│         backyard · cat · 42s            │
├─────────────────────────────────────────┤
│  20:01  [thumb]  Package delivery       │
│         front · delivery                │
└─────────────────────────────────────────┘
```

### Filters

- Date range: today / 7 days / 30 days / custom
- Type: person, vehicle, bicycle, cat, delivery, all
- Zone: front, driveway, backyard, all
- Identity: Thomas, Nils, Hugo, Anna, unknown

### Interactions

- Tap entry → full event detail (best picture, clip, metadata, correlations)
- Swipe → next/previous day
- Long press → "Ask AI about this event" (Phase 6)

---

## Summary Generation Rules (v1 — template)

| Type + context | Summary template |
|---|---|
| person + identity + arriving | `{name} arrived at {zone}` |
| person + identity + departing | `{name} left via {zone}` |
| person + unknown | `Person detected at {zone}` |
| vehicle | `Vehicle at {zone}` |
| bicycle + identity | `{person} arrived by bicycle` |
| cat + identity | `{cat} visited {zone}` |
| cat + unknown | `Cat detected in {zone}` |
| delivery | `Delivery detected at {zone}` |
| door + identity | `Door unlocked by {person}` |
| environment | `Air quality update · {temp}°C CO₂ {co2}` |

Phase 6 replaces templates with LLM-generated `ai_summary`.

---

## Implementation (current)

| Layer | Status | Detail |
|---|---|---|
| Event store | ✅ | `events/timeline.jsonl` |
| API v1 | ✅ | `/api/v1/events`, `metrics`, `occupancy` |
| Timeline UI v1 | ✅ | Horizontal scale, zoom, pan, custom range |
| HA access | ✅ | Sidebar dashboard `house-timeline` |
| List view | ✅ | `http://localhost:8765/` |
| Floorplan cross-links | ⬜ | Phase 8 |
| LLM `ai_summary` | ⬜ | Phase 6 |

---

## Data Flow

```
Events (JSONL/DB)
    ↓
Timeline projection query (by date, filters)
    ↓
Summary template / AI enrichment
    ↓
Timeline UI
```

---

## Example Day

```
06:42  Vehicle departed driveway
07:15  Thomas left via front door
15:30  Vehicle arrived driveway
15:31  Person detected driveway (unknown)
15:32  Nils arrived by bicycle
15:33  Door unlocked · Nils
19:42  Cat visited backyard (42s)
20:01  Delivery detected front
```
