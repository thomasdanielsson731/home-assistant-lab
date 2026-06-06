# Bicycle Analytics

Understand family mobility patterns — who cycles, when, and how often.

---

## Goal

Answer:

- How many bike trips per person per week?
- Arriving vs departing patterns?
- Seasonal trends (more cycling in spring/summer)?
- Correlation with door unlock (did they enter the house?)

---

## Detection Pipeline (v1 live)

```
Frigate detects person at driveway_id
    +
Bicycle-shaped object OR metadata.trip_type hint
    +
Optional: Double Take identifies rider
    +
Optional: Yale door unlock within 60s
    ↓
Event type: bicycle
```

### Detection strategies (in priority order)

| Strategy | Confidence | Notes |
|---|---|---|
| Custom ACAP bicycle model | High | Axis on-camera inference |
| Frigate `bicycle` label | Medium | Add to Frigate objects if supported |
| Heuristic: person + two-wheel shape | Low | Scene metadata correlation |
| Manual tag in timeline | — | Fallback |

**v0 heuristic:** Person detected at `driveway_id` + person identified (Nils/Hugo) + no vehicle → infer `bicycle` if speed/trajectory suggests bike (future). Simpler v0: user tags or time-of-day pattern (school hours = Hugo bike).

---

## Event Model

```json
{
  "type": "bicycle",
  "location": { "zone": "driveway", "camera": "driveway_id" },
  "identity": {
    "person": "Nils",
    "source": "double_take",
    "confidence": 0.85
  },
  "metadata": {
    "direction": "arriving",
    "trip_type": "bike",
    "correlated_door_unlock": true,
    "door_event_id": "evt_..._door",
    "time_to_door_seconds": 45
  }
}
```

### Trip correlation rules

| Signal | Window | Effect |
|---|---|---|
| Person identified at `driveway_id` | — | Candidate bicycle trip |
| Door unlock (Yale) | +60 s | `correlated_door_unlock: true` |
| Person identified at `front` | +120 s | `direction: arriving` confirmed |
| Person at `driveway_id` leaving | — | `direction: departing` |

---

## Outputs

| Output | Description |
|---|---|
| Trips per person | Daily/weekly count |
| Arriving vs departing | Direction breakdown |
| Weekly trend | Mini-graph per person |
| Seasonal trend | Monthly aggregation (quarter view) |
| Trip pairs | Bike arrive + door unlock sequences |

---

## Dashboard Concepts

### Mobility Summary (Home view future card)

```
This week
  Nils    5 bike trips
  Hugo    3 bike trips
```

### Trip Timeline

```
Mon 15:32  Nils arrived by bicycle → door unlocked
Tue 07:45  Hugo departed by bicycle
Wed 15:28  Nils arrived by bicycle → door unlocked
```

### Seasonal Chart

90-day aggregate: bicycle trips per week, stacked by person.

---

## AI Insights (Phase 6)

- "Nils cycles home from school between 15:15 and 15:45 on weekdays"
- "Bicycle trips up 20% compared to last month"
- "Hugo's first bike trip this year was March 12"

---

## Dependencies

| Dependency | Status |
|---|---|
| Face recognition (Nils, Hugo) | Phase 4 — CodeProject.AI |
| Yale door events | HA MQTT ingestion live — map `YALE_LOCK_ENTITIES` in `.env` |
| Bicycle detection model | Scene `bicycles` count + Frigate `bicycle` label |
| Event store + correlation | Live — `correlation_engine.py` |

---

## Implementation Phases

| Phase | Task |
|---|---|
| 1 | Face recognition working at `driveway_id` |
| 2 | Yale → `door` events | ✅ HA MQTT |
| 3 | Bicycle detection (Frigate label or ACAP) | ✅ scene + Frigate label |
| 4 | Correlation engine (person + bike + door) | ✅ |
| 5 | Bicycle aggregates + dashboard cards |
| 6 | AI mobility summaries |
