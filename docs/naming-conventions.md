# Naming Conventions

Consistent naming across all layers — HA entities, Frigate cameras, files, automations, and scripts. Follow these conventions everywhere. Deviations require a note in the relevant file.

---

## Principles

1. **Zone-first** — the physical location is the primary identifier, not the hardware model
2. **Snake case** for all HA entity IDs, YAML keys, and file names in `config/`
3. **Kebab case** for documentation file names in `docs/`
4. **No abbreviations** unless listed in the table below
5. **No model numbers in entity IDs** — models change; zones do not

---

## Approved Abbreviations

| Abbreviation | Meaning |
|---|---|
| `ext` | exterior |
| `int` | interior |
| `id` | identification (not "ID number") |
| `env` | environmental |
| `wide` | wide-angle overview |
| `dt` | Double Take |

---

## Zone IDs

These are the canonical identifiers for every physical camera or sensor zone. Use them verbatim in Frigate, HA entities, MQTT topics, and file names.

| Zone ID | Location | Hardware |
|---|---|---|
| `front` | Front entrance | Axis P3288 |
| `driveway_wide` | Driveway — overview | Axis Q3558-LVE |
| `driveway_id` | Driveway — identification point | Axis M2036 |
| `backyard` | Backyard perimeter | Axis Q1656 |
| `storage_ext` | Storage building exterior | Axis Q1656 |
| `storage_int` | Storage building interior | Axis M1055 |
| `driveway_env` | Driveway — environmental sensor | Axis D6210 |

---

## Home Assistant Entity IDs

Pattern: `<domain>.<integration>_<zone_id>[_<attribute>]`

### Camera entities (via Frigate integration)

```
camera.frigate_front
camera.frigate_driveway_wide
camera.frigate_driveway_id
camera.frigate_backyard
camera.frigate_storage_ext
camera.frigate_storage_int
```

### Binary sensors (Frigate detections)

```
binary_sensor.frigate_<zone_id>_<object>

Examples:
  binary_sensor.frigate_front_person
  binary_sensor.frigate_front_motion
  binary_sensor.frigate_driveway_wide_car
  binary_sensor.frigate_driveway_id_person
  binary_sensor.frigate_backyard_person
  binary_sensor.frigate_storage_ext_person
  binary_sensor.frigate_storage_int_person
```

### Environmental sensors (D6210 via M2036)

```
binary_sensor.driveway_env_motion
sensor.driveway_env_<metric>
```

### Audio analytics (SPL via `audio_bridge.py`)

```
sensor.<zone_id>_audio_spl
```

MQTT topic: `axis/<zone_id>/audio/spl` — JSON `{"max_spl", "min_spl", "spl"}`.

Live zones: `front`, `driveway_wide`, `backyard`.

### Double Take sensors (face recognition)

```
sensor.dt_<person_name>_confidence
binary_sensor.dt_<person_name>_present
```

### Area-based entities (lights, switches, etc.)

```
light.<room_snake_case>_<fixture>
switch.<room_snake_case>_<device>
sensor.<room_snake_case>_<metric>

Examples:
  light.kitchen_ceiling
  light.bedroom_main
  switch.storage_ext_door_lock
  sensor.backyard_temperature
```

---

## Frigate Camera Names

Frigate camera names map 1:1 to zone IDs. These appear in `config/frigate/config.yml` and in all MQTT topics.

```yaml
cameras:
  front: ...
  driveway_wide: ...
  driveway_id: ...
  backyard: ...
  storage_ext: ...
  storage_int: ...
```

MQTT topics follow Frigate's default pattern:
```
frigate/<zone_id>/<object_type>
frigate/<zone_id>/events
```

---

## Automation IDs and Aliases

Pattern: `<domain>_<trigger>_<action>`

| Domain | Examples |
|---|---|
| `security` | `security_person_detected_notify`, `security_unknown_face_alert` |
| `presence` | `presence_person_home_lights_on`, `presence_away_mode_set` |
| `camera` | `camera_driveway_motion_record`, `camera_storage_night_mode` |
| `notification` | `notification_front_person_push`, `notification_face_match_log` |

File placement: `config/home-assistant/automations/<domain>/<action>.yaml`

---

## Script IDs

Pattern: `script_<verb>_<subject>`

```
script_arm_security
script_send_snapshot_notification
script_sync_frigate_zones
```

---

## File Naming

| Context | Convention | Example |
|---|---|---|
| HA YAML config files | snake_case | `frigate_person_alert.yaml` |
| Documentation | kebab-case | `camera-onboarding.md` |
| Shell scripts | kebab-case | `sync-config.sh` |
| ADR files | `NNN-kebab-title.md` | `001-haos-platform.md` |
| Frigate mask files | `<zone_id>_mask.png` | `front_mask.png` |

---

## Lovelace Dashboard and View IDs

Pattern: `<view_name>` in snake_case, human-readable title in Title Case

| View ID | Title | Purpose |
|---|---|---|
| `home` | Home | Main overview |
| `cameras` | Cameras | All camera feeds |
| `rooms` | Rooms | Per-room controls |
| `security` | Security | Events + alerts |
| `ops` | Operations | System health + admin |

---

## Area Names in Home Assistant

Use these exact names when creating Areas in HA settings. They map to automation conditions and dashboard sections.

**Indoor — Ground Floor:**
- Kitchen / Living Room
- Hall (Ground Floor)
- Bedroom
- Bathroom (Ground Floor)

**Indoor — Upper Floor:**
- TV Room
- Nils' Room
- Hugo's Room
- Hall (Upper Floor)
- Office
- Bathroom (Upper Floor)

**Outdoor:**
- Front
- Driveway
- Backyard
- Storage Building

---

## Git Branch Names

| Pattern | Use case |
|---|---|
| `main` | Production config — protected |
| `dev` | Development / staging |
| `feature/<short-name>` | New feature or integration |
| `fix/<short-name>` | Bug fix |
| `docs/<short-name>` | Documentation only |

---

## Secrets Naming (secrets.yaml)

Pattern: `<zone_id>_<attribute>` or `<service>_<attribute>`

```yaml
front_camera_ip: ...
front_camera_user: ...
front_camera_password: ...
driveway_wide_camera_ip: ...
mqtt_password: ...
compreface_api_key: ...
```
