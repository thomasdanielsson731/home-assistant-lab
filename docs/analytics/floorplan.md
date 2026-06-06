# Floorplan Design

Visualize activity on a property map and house floorplan — not for automation control.

---

## Purpose

Answer: **"Where is activity happening?"** and **"What zones are hot this week?"**

---

## Layers

| Layer | Content | Data source |
|---|---|---|
| 1. Property map | Outdoor zones: front, driveway, backyard, storage | Zone registry |
| 2. House floorplan | Indoor rooms (ground + upper floor) | HA areas |
| 3. Camera coverage | FOV cones per camera | Camera positions (manual config) |
| 4. Event layer | Recent event pins with thumbnails | Event store |
| 5. Heatmap layer | Activity density per zone, time-filtered | Daily aggregates |

Toggle layers independently. Default: property map + event layer.

---

## Property Map (outdoor)

```
                    ┌──────────────────────────┐
                    │         PROPERTY         │
                    │                          │
    [front] ●───────┤  ┌────────┐              │
                    │  │ HOUSE  │              │
    [driveway] ●────┤  └────────┘              │
      wide + id     │                          │
    [driveway_env] ○  │  D6210 sensor           │
                    │                          │
    [backyard] ●────┤                          │
                    │  ┌──────────────┐        │
    [storage] ●─────┤  │   STORAGE    │        │
                    │  └──────────────┘        │
                    └──────────────────────────┘
```

- **●** = camera position (click → live feed)
- **○** = environmental sensor
- **Pin** = recent event (colour by type: person=red, vehicle=amber, cat=purple)

---

## Event Pin Model

```json
{
  "zone": "backyard",
  "position": { "x": 0.72, "y": 0.45 },
  "events_last_24h": 3,
  "last_event": {
    "type": "cat",
    "timestamp": "2026-06-06T19:42:00+02:00",
    "thumbnail": "..."
  }
}
```

Positions are normalized 0–1 on the property SVG.

---

## Heatmap

Aggregate `counts` per zone per day → colour intensity:

| Activity level | Colour |
|---|---|
| 0 events | grey |
| 1–5 | light blue |
| 6–15 | blue |
| 16+ | deep blue |

Separate heatmaps per type: persons, vehicles, cats.

---

## House Floorplan (indoor — future)

Uses HA areas. Shows:

- Door events (Yale)
- Smoke events (Zigbee)
- Room temperature (if sensors added)
- Last person presence per room (phone + face correlation)

Indoor layer activates when Yale + room sensors are integrated.

---

## Implementation Options

| Option | Fit |
|---|---|
| Picture Elements on HA dashboard | Quick v0 with static SVG background |
| Custom Lovelace card (`floorplan-card`) | Medium effort, stays in HA |
| React + SVG on dev PC | Best UX, reads event API |
| Grafana geomap | Poor fit for custom property layout |

**v0:** Static property SVG in HA with Mushroom template pins driven by zone event counts (template sensors).

**v1:** Interactive floorplan reading event store.

---

## Camera Coverage Layer

| Camera | Zone | Approximate coverage |
|---|---|---|
| `front` | front | Entrance, path to door |
| `driveway_wide` | driveway | Full driveway overview |
| `driveway_id` | driveway | ID point, gate area |
| `backyard` | backyard | Full backyard perimeter |
| `storage_ext` | storage_ext | Storage building exterior |
| `storage_int` | storage_int | Storage interior |

FOV polygons defined in `config/floorplan/cameras.json` (future).
