# Cat Analytics

Track visits from neighbouring cats on the property.

---

## Goal

Understand cat activity patterns — not pest control, but **context and curiosity**:

- Which cats visit most?
- When do they visit?
- How long do they stay?
- Which zones are popular?

---

## Detection Pipeline (planned)

```
Axis/Frigate detect cat-shaped object
    ↓
Event type: cat (confidence ≥ 0.70)
    ↓
Track duration (AOA occupancy or scene track)
    ↓
Optional: custom ACAP model for re-identification
    ↓
Cat Analytics aggregates
```

### Input sources

| Source | Today | Future |
|---|---|---|
| Frigate `cat` label | If enabled in config | Tune per camera |
| Axis scene metadata | `detections[].type` if cat class available | — |
| Custom ACAP model | — | Train on backyard footage |
| Manual tagging | — | Confirm/rename in timeline UI |

**v0:** Frigate does not detect `cat` by default on all cameras — add `cat` to Frigate labels on `backyard` first.

---

## Event Model

```json
{
  "type": "cat",
  "location": { "zone": "backyard", "camera": "backyard" },
  "identity": {
    "cat": "black_cat",
    "source": "manual_tag",
    "confidence": 0.78
  },
  "metadata": {
    "duration_seconds": 42,
    "first_seen": "2026-06-06T19:40:00+02:00",
    "last_seen": "2026-06-06T19:40:42+02:00",
    "visit_number_today": 2
  }
}
```

### Visit session logic

- New visit if no `cat` detection for **5 minutes** at same zone
- `duration_seconds` = last_seen − first_seen within session
- Unknown cats: `identity.cat = "unknown"` until manually tagged

---

## Outputs

| Output | Description |
|---|---|
| Visit timeline | Chronological cat events |
| Top cats | Ranked by visit count (7/30 days) |
| Duration stats | Avg/median visit duration per cat |
| Zone heatmap | Backyard vs front vs driveway visits |
| Time-of-day chart | Hour-of-day distribution |
| Weekly report | "3 cat visits this week, mostly 19:00–21:00" |

---

## Dashboard Concepts

### Cat Timeline (subset of main timeline)

Filter: `type=cat` only.

### Cat Scoreboard

```
This week
  black_cat     4 visits · avg 38s
  tabby_cat     2 visits · avg 55s
  unknown       1 visit  · avg 12s
```

### Backyard Heatmap

Floorplan layer coloured by cat visit density.

---

## AI Insights (Phase 6)

- "Neighbour cat visits increased 40% this month"
- "Black cat prefers backyard between 19:00 and 21:00"
- Caption on snapshot: "Small black cat near patio, facing west"

---

## Implementation Phases

| Phase | Task |
|---|---|
| 1 | Enable Frigate `cat` detection on `backyard` |
| 2 | Normalize Frigate cat detections → events |
| 3 | Duration tracking via AOA/scene |
| 4 | Cat timeline filter in UI |
| 5 | Custom model for re-identification |
| 6 | Weekly AI cat report |
