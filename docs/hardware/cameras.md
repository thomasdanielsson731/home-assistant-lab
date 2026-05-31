# Camera Inventory

Six Axis cameras covering all zones of the property, plus one environmental sensor.

---

## Zone Map

```
                    ┌──────────────────────────────┐
                    │          PROPERTY            │
                    │                              │
  [front]           │  ┌────────┐                  │
  Axis P3288  ──────┼──► HOUSE  │                  │
                    │  └────────┘                  │
                    │                              │
  [driveway_wide]   │  DRIVEWAY                    │
  Q3558-LVE  ───────┼──► (wide angle overview)     │
                    │                              │
  [driveway_id]     │  ┌──────────┐                │
  M2036 + D6210 ────┼──► (ID cam + radar sensor)  │
                    │  └──────────┘                │
                    │                              │
  [backyard]        │  BACKYARD                    │
  Q1656  ───────────┼──► (perimeter)               │
                    │                              │
  [storage_ext]     │  ┌──────────────────┐        │
  Q1656  ───────────┼──► STORAGE BUILDING │        │
  [storage_int]     │  │                  │        │
  M1055  ───────────┼──► (interior)       │        │
                    │  └──────────────────┘        │
                    └──────────────────────────────┘
```

---

## Front Entrance

### Axis P3288 — `front`

| Attribute | Value |
|---|---|
| Model | Axis P3288-V (or P3288-LVE outdoor) |
| Zone ID | `front` |
| Location | Front entrance — facing the door / gate |
| Mount | Wall or ceiling at entrance |
| IP | TBD |

**Purpose:** Primary person detection and face recognition at the main entry point. High-resolution capture optimized for facial identification of approaching persons.

**Current status:** Active in Frigate, recording.

**HA entities (live):**
- `camera.front` — live feed
- `binary_sensor.front_person_occupancy` — person detected
- `binary_sensor.front_motion` — motion
- `sensor.front_person_count` — detection count (24h)

**Planned Frigate role:**
- Dual-stream: full-res record + 640×360 detect
- Detect objects: `person`
- Snapshots enabled for Double Take face matching
- Zone: `front_door_zone` for targeted alerts

**Face recognition role:**
- Primary Double Take watcher for known-person identification
- Snapshot sent to CompreFace on every `person` detection event

---

## Driveway

### Axis Q3558-LVE — `driveway_wide`

| Attribute | Value |
|---|---|
| Model | Axis Q3558-LVE |
| Zone ID | `driveway_wide` |
| Location | Driveway — elevated, wide-angle overview |
| Mount | Pole or building wall, high position |
| IP | TBD |

**Purpose:** Full driveway area situational awareness. Vehicle detection, general presence, and overview context for other driveway events.

**Current status:** Not yet added to Frigate or HA.

**Planned HA role:**
- `camera.frigate_driveway_wide` — overview feed
- `binary_sensor.frigate_driveway_wide_car` — vehicle arrival trigger
- `binary_sensor.frigate_driveway_wide_person` — person in driveway

**Planned Frigate role:**
- Detect objects: `person`, `car`
- Record: continuous during motion
- Zone: `driveway_entry` for vehicle-specific alerts
- Lower detect FPS acceptable (5 fps) — area overview, not ID

**Future Axis analytics role:**
- ACAP application for vehicle counting or loitering detection
- MQTT metadata published directly to HA MQTT broker

---

### Axis M2036 — `driveway_id`

| Attribute | Value |
|---|---|
| Model | Axis M2036-LE |
| Zone ID | `driveway_id` |
| Location | Driveway — fixed point, optimized for identification |
| Mount | Aimed at gate / entry point for face and plate |
| IP | TBD |

**Purpose:** Identification-grade capture of persons and vehicles entering the driveway. Higher FPS and tighter field of view than the overview camera. Hosts the D6210 radar sensor on its I/O port.

**Current status:** Not yet added to Frigate or HA.

**Planned HA role:**
- `camera.frigate_driveway_id` — identification feed
- `binary_sensor.frigate_driveway_id_person` — identification trigger
- `sensor.driveway_env_*` — environmental data via D6210

**Planned Frigate role:**
- Detect objects: `person`, `car`, `face` (if model supports)
- Higher detect FPS: 10 fps
- Snapshots: enabled, sent to Double Take
- Zone: `gate_zone` — tight bounding box at entry

**Face recognition role:**
- Second Double Take watcher (after `front`)
- License plate recognition potential (future ALPR integration)

---

## Backyard

### Axis Q1656 — `backyard`

| Attribute | Value |
|---|---|
| Model | Axis Q1656-LE |
| Zone ID | `backyard` |
| Location | Backyard — perimeter coverage |
| Mount | Building wall, elevated |
| IP | TBD |

**Purpose:** Backyard perimeter monitoring. Person detection for after-hours alerts. Garden / outdoor activity context.

**Current status:** Not yet added to Frigate or HA.

**Planned HA role:**
- `camera.frigate_backyard` — backyard feed
- `binary_sensor.frigate_backyard_person` — perimeter breach alert

**Planned Frigate role:**
- Detect objects: `person`
- Motion-triggered recording
- Zone: `backyard_perimeter` — exclude known animal paths if needed
- Mask: exclude sky / road if in frame

---

## Storage Building

### Axis Q1656 — `storage_ext`

| Attribute | Value |
|---|---|
| Model | Axis Q1656-LE |
| Zone ID | `storage_ext` |
| Location | Storage building — exterior, facing the door |
| Mount | Under eave or wall-mounted |
| IP | TBD |

**Purpose:** Storage building exterior door monitoring. Detect approach and access events.

**Current status:** Not yet added to Frigate or HA.

**Planned HA role:**
- `camera.frigate_storage_ext` — exterior feed
- `binary_sensor.frigate_storage_ext_person` — approach detection

**Planned Frigate role:**
- Detect objects: `person`
- Zone: `storage_door_zone`
- Snapshots: enabled

---

### Axis M1055 — `storage_int`

| Attribute | Value |
|---|---|
| Model | Axis M1055-L |
| Zone ID | `storage_int` |
| Location | Storage building — interior |
| Mount | Ceiling or wall inside building |
| IP | TBD |

**Purpose:** Interior presence detection. Confirm whether someone entered after an exterior door event. Useful for intrusion confirmation.

**Current status:** Not yet added to Frigate or HA.

**Planned HA role:**
- `camera.frigate_storage_int` — interior feed
- `binary_sensor.frigate_storage_int_person` — interior presence

**Planned Frigate role:**
- Detect objects: `person`
- Lower FPS (3–5) acceptable — supplementary camera
- Recording: motion-triggered only

---

## Environmental Sensor

### Axis D6210 — `driveway_env`

| Attribute | Value |
|---|---|
| Model | Axis D6210 Network Radar Detector |
| Zone ID | `driveway_env` |
| Location | Driveway — physically connected to M2036 |
| Connection | I/O port on Axis M2036 |
| IP | Shared with M2036 or independent (model-dependent) |

**Purpose:** Radar-based motion detection with lower false-positive rate than optical detection. Provides environmental presence data that complements M2036's visual detection. Can detect objects through rain, fog, and darkness where cameras struggle.

**Current status:** Not yet integrated.

**Planned HA role:**
- `binary_sensor.driveway_env_motion` — radar motion trigger
- `sensor.driveway_env_distance` — detected object distance (if available)
- Used as a pre-trigger to wake up Frigate detection on `driveway_id`

**Integration path:**
- Option A: Axis VAPIX API → HA REST sensor polling
- Option B: Axis MQTT (if firmware supports) → Mosquitto → HA
- Option C: ONVIF event → HA ONVIF integration

---

## Naming Quick Reference

| Zone ID | Model | HA Camera Entity | Motion Sensor | Person Sensor |
|---|---|---|---|---|
| `front` | P3288 | `camera.front` | `binary_sensor.front_motion` | `binary_sensor.front_person_occupancy` |
| `driveway_wide` | Q3558-LVE | `camera.driveway_wide` | `binary_sensor.driveway_wide_motion` | `binary_sensor.driveway_wide_person_occupancy` |
| `driveway_id` | M2036 | `camera.driveway_id` | `binary_sensor.driveway_id_motion` | `binary_sensor.driveway_id_person_occupancy` |
| `backyard` | Q1656 | `camera.backyard` | `binary_sensor.backyard_motion` | `binary_sensor.backyard_person_occupancy` |
| `storage_ext` | Q1656 | `camera.storage_ext` | `binary_sensor.storage_ext_motion` | `binary_sensor.storage_ext_person_occupancy` |
| `storage_int` | M1055 | `camera.storage_int` | `binary_sensor.storage_int_motion` | `binary_sensor.storage_int_person_occupancy` |
| `driveway_env` | D6210 | — | `binary_sensor.driveway_env_motion` | — |

> **Note:** Frigate HACS integration (v0.17) names entities after the camera name directly, without a `frigate_` prefix.
