# Event Model

**Core principle:** Everything is an event. Timeline, dashboards, floorplans, analytics, and AI insights must consume the same model.

Not separate silos (`camera_event`, `door_event`, `cat_event`) — one `Event` with a `type` field.

---

## Core Event Schema

```json
{
  "event_id": "evt_20260606_181245_driveway_id_bicycle",
  "timestamp": "2026-06-06T18:12:45+02:00",
  "type": "bicycle",
  "location": {
    "zone": "driveway",
    "camera": "driveway_id"
  },
  "snapshot": {
    "best_picture": "events/bicycle/2026/06/06/evt_...jpg",
    "thumbnail": "events/bicycle/2026/06/06/evt_..._thumb.jpg",
    "clip": "events/bicycle/2026/06/06/evt_...mp4"
  },
  "confidence": 0.94,
  "identity": {},
  "metadata": {},
  "source": "frigate",
  "enriched": false
}
```

| Field | Required | Description |
|---|---|---|
| `event_id` | yes | Unique ID. Pattern: `evt_{date}_{time}_{zone}_{type}` |
| `timestamp` | yes | ISO 8601 with timezone (`Europe/Stockholm`) |
| `type` | yes | See [event-taxonomy.md](event-taxonomy.md) |
| `location` | yes | `zone` + optional `camera` |
| `snapshot` | no | Best picture, thumbnail, clip paths |
| `confidence` | no | 0.0–1.0 detection or recognition confidence |
| `identity` | no | Person, cat, or vehicle identity when known |
| `metadata` | no | Type-specific attributes |
| `source` | no | `frigate`, `axis_aoa`, `axis_scene`, `yale`, `d6210`, `ha` |
| `enriched` | no | `true` after AI/metadata pipeline runs |

JSON Schema: [`schemas/danielsson-event.schema.json`](../../schemas/danielsson-event.schema.json)

---

## Type-Specific Examples

### Person

```json
{
  "type": "person",
  "location": { "zone": "front", "camera": "front" },
  "identity": {
    "type": "person",
    "name": "Thomas",
    "source": "double_take",
    "confidence": 0.97
  },
  "metadata": {
    "direction": "arriving",
    "frigate_label": "person"
  }
}
```

### Vehicle

```json
{
  "type": "vehicle",
  "location": { "zone": "driveway", "camera": "driveway_wide" },
  "metadata": {
    "sub_type": "car",
    "direction": "departing"
  }
}
```

### Bicycle

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
    "correlated_door_unlock": false
  }
}
```

### Cat

```json
{
  "type": "cat",
  "location": { "zone": "backyard", "camera": "backyard" },
  "identity": {
    "cat": "black_cat",
    "source": "custom_model",
    "confidence": 0.78
  },
  "metadata": {
    "duration_seconds": 42,
    "first_seen": "2026-06-06T19:40:00+02:00",
    "last_seen": "2026-06-06T19:40:42+02:00"
  }
}
```

### Delivery

```json
{
  "type": "delivery",
  "location": { "zone": "front", "camera": "front" },
  "metadata": {
    "carrier": "PostNord",
    "vehicle_detected": true,
    "person_detected": true,
    "package_visible": true
  }
}
```

### Environment

```json
{
  "type": "environment",
  "location": { "zone": "driveway_env", "camera": null },
  "metadata": {
    "temperature": 21.4,
    "humidity": 48,
    "co2": 430,
    "voc": 14,
    "aqi": 17,
    "pm25": 4.1
  },
  "source": "d6210"
}
```

### Door

```json
{
  "type": "door",
  "location": { "zone": "front", "camera": "front" },
  "identity": {
    "person": "Thomas",
    "source": "yale",
    "confidence": 1.0
  },
  "metadata": {
    "action": "unlock",
    "method": "pin"
  }
}
```

---

## Zone and Camera Registry

Canonical zone IDs — see [naming-conventions.md](../naming-conventions.md).

| Zone ID | Display name | Cameras |
|---|---|---|
| `front` | Front entrance | `front` (P3288) |
| `driveway` | Driveway | `driveway_wide` (Q3558), `driveway_id` (M2036) |
| `backyard` | Backyard | `backyard` (Q1656) |
| `storage_ext` | Storage exterior | `storage_ext` (M1055-L) |
| `storage_int` | Storage interior | `storage_int` (Q1656) |
| `driveway_env` | Outdoor environment | D6210 via M2036 proxy |

**Note:** Event `location.zone` uses logical zones (`driveway`, `front`). Event `location.camera` uses canonical camera zone IDs (`driveway_id`).

---

## Identity Model

```json
{
  "type": "person",
  "name": "Thomas",
  "source": "double_take",
  "confidence": 0.96
}
```

| Identity class | Known values (v1) | Source |
|---|---|---|
| Person | Thomas, Anna, Nils, Hugo | Double Take / CodeProject.AI |
| Cat | `black_cat`, `tabby_cat`, … | Custom model (future) |
| Vehicle | — | Type only, no plate (v1) |

---

## Snapshot Strategy

Every vision event should capture:

| Asset | Purpose |
|---|---|
| `best_picture` | Timeline, floorplan popup, AI caption input |
| `thumbnail` | List views, mobile |
| `clip` | Review, training data |

**Best picture selection:** Frigate snapshot with highest detection score for the tracked object. Store under `events/{type}/{yyyy}/{mm}/{dd}/`.

**Retention:** Clips 7 days (Frigate default). Event JSON + thumbnails 90 days. Best pictures 30 days.

---

## Dashboard Aggregates

Dashboards consume **aggregates**, not raw events.

```json
{
  "date": "2026-06-06",
  "zone": "driveway",
  "counts": {
    "person": 12,
    "vehicle": 18,
    "bicycle": 4,
    "cat": 3,
    "delivery": 1
  },
  "environment": {
    "temperature_avg": 16.2,
    "temperature_min": 12.1,
    "temperature_max": 21.4,
    "co2_avg": 428
  }
}
```

Produced nightly by an aggregate job (Phase 7). HA dashboards read aggregates; timeline reads raw events.

---

## Event Store Layout (planned)

```
events/
├── person/
├── vehicle/
├── bicycle/
├── cat/
├── delivery/
├── environment/
├── door/
└── smoke/
```

Each folder stores JSON event files and references to media assets. See [../../events/README.md](../../events/README.md).

---

## Mapping from Home Assistant (today)

| HA source | Event type | Normalizer |
|---|---|---|
| Frigate MQTT `person` | `person` | Frigate webhook → event |
| Frigate MQTT `car` | `vehicle` | Frigate webhook → event |
| `binary_sensor.*_aoa_person` | `person` | AOA bridge → event (future) |
| `sensor.driveway_env_*` | `environment` | air_quality_bridge → event (future) |
| Double Take match | enriches `person` identity | DT MQTT → identity attach |
| Yale lock | `door` | HA integration → event (future) |
| Scene delivery automation | `delivery` | Automation → event (future) |

**v0 implemented:** `scripts/event_normalizer.py` logs events as JSONL on dev PC. `scripts/timeline_server.py` serves Timeline UI on `:8765`. Phase 2: InfluxDB or SQLite.
