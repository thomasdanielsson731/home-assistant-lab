# Event Taxonomy

Classification, lifecycle, and retention for Danielsson Insights events.

---

## Event Types

| Type | Description | Primary sources | Phase |
|---|---|---|---|
| `person` | Human detected or identified | Frigate, AOA, Double Take | Live |
| `vehicle` | Car, truck, bus, motorcycle | Frigate, AOA | Live |
| `bicycle` | Bicycle with optional rider attribution | Frigate + person correlation | Planned |
| `cat` | Cat detected (neighbour cats) | Frigate / custom ACAP model | Planned |
| `delivery` | Package or courier visit | Scene metadata + person + vehicle | Prototype |
| `environment` | Air quality, temp, humidity | D6210 bridge | Live |
| `door` | Lock/unlock, open/close | Yale Doorman V3 | Planned |
| `smoke` | Smoke detector alert | Zigbee (future) | Future |

---

## Event Lifecycle

```
Detect → Normalize → Store → Enrich → Aggregate → Visualize
```

| Stage | What happens | Owner |
|---|---|---|
| **Detect** | Camera, sensor, or lock produces raw signal | Frigate, Axis, HA |
| **Normalize** | Raw signal → canonical Event JSON | Event normalizer (planned) |
| **Store** | Event persisted with snapshot refs | Event store (Phase 7) |
| **Enrich** | AI caption, identity attach, correlation | Enrichment pipeline (Phase 6) |
| **Aggregate** | Daily/weekly rollups per zone | Aggregate job (Phase 7) |
| **Visualize** | Timeline, floorplan, dashboard | UI layers |

### Deduplication

Multiple sources may fire for the same physical event (Frigate person + AOA person at `front`). Normalizer should:

1. Group events within **10 s** window at same `zone` with same `type`
2. Merge: highest `confidence`, best `snapshot`, union `metadata`
3. Set `metadata.sources: ["frigate", "axis_aoa"]`

### Correlation

Cross-type links stored in `metadata.correlations`:

```json
{
  "metadata": {
    "correlations": [
      { "event_id": "evt_..._person", "type": "person", "offset_seconds": -8 },
      { "event_id": "evt_..._door", "type": "door", "offset_seconds": 12 }
    ]
  }
}
```

Example: bicycle event correlates with person event (Nils) + door unlock within 60 s.

---

## Retention Policy

| Data | Retention | Storage |
|---|---|---|
| Event JSON | 90 days | Event store |
| Thumbnails | 90 days | `events/` + SSD |
| Best pictures | 30 days | `events/` |
| Video clips | 7 days | Frigate SSD (existing) |
| Daily aggregates | 2 years | InfluxDB / SQLite |
| AI enrichments | Same as parent event | Event store |

---

## Zone Hierarchy

```
Property
├── front          (entrance)
├── driveway       (driveway_wide + driveway_id + driveway_env)
├── backyard
├── storage_ext
└── storage_int
```

Indoor zones (future floorplan layer):

```
House
├── Ground Floor: Kitchen/Living, Hall, Bedroom, Bathroom
└── Upper Floor: TV Room, Nils' Room, Hugo's Room, Office, …
```

Outdoor events use property zones. Indoor events (door, smoke, Zigbee) use room areas when available.

---

## Confidence Thresholds

| Type | Min confidence to store | Min confidence to show identity |
|---|---|---|
| `person` (detected) | 0.50 | — |
| `person` (identified) | — | 0.85 |
| `vehicle` | 0.55 | — |
| `bicycle` | 0.60 | — |
| `cat` | 0.70 | 0.75 |
| `delivery` | 0.50 (rule-based) | — |

---

## Source Priority (conflict resolution)

When sources disagree on the same event:

1. **Identity:** Double Take > Frigate label
2. **Presence speed:** AOA > Frigate (lower latency)
3. **Snapshot quality:** Frigate > Axis scene snapshot
4. **Counts:** Axis scene metadata > Frigate count sensor
