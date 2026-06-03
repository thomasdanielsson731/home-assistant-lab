# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Production Environment

| Detail | Value |
|---|---|
| Host | Dell Latitude 3120 (x86-64) |
| OS | Home Assistant OS (HAOS) — not Container mode |
| Storage | External 1 TB SSD at `/media/frigate` (Frigate recordings) |
| HA URL | `http://192.168.68.175:8123` |
| SSH | `root@192.168.68.175 -p 22222` (SSH add-on) |

## Development Environment

| Detail | Value |
|---|---|
| Workstation | Windows PC at 192.168.68.118 |
| Editors | VS Code, Cursor |
| AI | Claude Code (you), Ollama + Qwen (local LLM) |

## Add-ons

| Add-on | Port | Status |
|---|---|---|
| Frigate 0.17.1 | 5000 (UI), 8554 (RTSP re-stream) | Running |
| Double Take 1.13.1 | 3000 | Running |
| Mosquitto | 1883 | Running |
| SSH & Web Terminal | 22222 | Running |

## Camera Zone IDs

These are canonical — use them verbatim in all config, entities, and filenames.

| Zone ID | Model | Location |
|---|---|---|
| `front` | Axis P3288-LVE | Front entrance | 192.168.68.200 |
| `driveway_wide` | Axis Q3558-LVE | Driveway — wide overview | 192.168.68.201 |
| `driveway_id` | Axis M2036-LE | Driveway — identification point | 192.168.68.204 |
| `backyard` | Axis Q1656-LE | Backyard perimeter | 192.168.68.203 |
| `storage_ext` | Axis M1055-L | Storage building exterior | 192.168.68.205 |
| `storage_int` | Axis Q1656 | Storage building interior | 192.168.68.206 |
| `driveway_env` | Axis D6210 | Driveway air quality sensor (accessed via M2036 VAPIX proxy at 192.168.68.204) | — |

## House Areas

**Ground Floor:** Kitchen / Living Room · Hall (Ground Floor) · Bedroom · Bathroom (Ground Floor)
**Upper Floor:** TV Room · Nils' Room · Hugo's Room · Hall (Upper Floor) · Office · Bathroom (Upper Floor)
**Outdoor:** Front · Driveway · Backyard · Storage Building

**Persons:** Thomas · Nils · Hugo · Anna

## Naming Conventions

- See `docs/naming-conventions.md` — follow it for every entity, file, and script
- Zone-first, snake_case for YAML/entities, kebab-case for doc files

**Live Frigate entity IDs** (Frigate HA integration names entities after the camera name in `config.yml`):

| Zone | Camera | Motion sensor | Person sensor |
|---|---|---|---|
| `front` | `camera.front` | `binary_sensor.front_motion` | `binary_sensor.front_person_occupancy` |
| `driveway_wide` | `camera.driveway_wide` | `binary_sensor.driveway_wide_motion` | `binary_sensor.driveway_wide_person_occupancy` |
| `driveway_id` | `camera.driveway_id` | `binary_sensor.driveway_id_motion` | `binary_sensor.driveway_id_person_occupancy` |
| `backyard` | `camera.backyard` | `binary_sensor.backyard_motion` | `binary_sensor.backyard_person_occupancy` |
| `storage_ext` | `camera.storage_ext` | `binary_sensor.storage_ext_motion` | `binary_sensor.storage_ext_person_occupancy` |
| `storage_int` | `camera.storage_int` | `binary_sensor.storage_int_motion` | `binary_sensor.storage_int_person_occupancy` |

Note: `docs/naming-conventions.md` specifies `camera.frigate_<zone_id>` as the intended pattern, but the Frigate integration creates entities directly from the camera name in `config.yml`. Current entities omit the `frigate_` prefix.

**AOA entity IDs** (Phase 5 — live in `config/home-assistant/mqtt_binary_sensors/`):

| Zone | Person occupancy | Vehicle occupancy | Loitering |
|---|---|---|---|
| `front` | `binary_sensor.front_aoa_person` | `binary_sensor.front_aoa_vehicle` | `binary_sensor.front_aoa_loitering` |
| `driveway_wide` | `binary_sensor.driveway_wide_aoa_person` | `binary_sensor.driveway_wide_aoa_vehicle` | `binary_sensor.driveway_wide_aoa_loitering` |
| `driveway_id` | `binary_sensor.driveway_id_aoa_person` | `binary_sensor.driveway_id_aoa_vehicle` | `binary_sensor.driveway_id_aoa_loitering` |
| `backyard` | `binary_sensor.backyard_aoa_person` | — | — |
| `storage_ext` | `binary_sensor.storage_ext_aoa_person` | — | — |
| `storage_int` | `binary_sensor.storage_int_aoa_person` | — | — |

**D6210 air quality entity IDs** (Phase 5 — REST polling via M2036, see `docs/runbooks/d6210-setup.md`): `sensor.driveway_env_temperature`, `sensor.driveway_env_humidity`, `sensor.driveway_env_co2`, `sensor.driveway_env_voc`, `sensor.driveway_env_nox`, `sensor.driveway_env_pm25`, `sensor.driveway_env_aqi` — pending curl output to confirm JSON structure.

**Scene frame entity IDs** (Phase 5 — from `axis/<zone>/scene/frame` analytics stream):

| Zone | Presence | Person count | Vehicle count |
|---|---|---|---|
| `front` | `binary_sensor.front_scene_object_present` | `sensor.front_scene_persons` | `sensor.front_scene_vehicles` |
| `driveway_wide` | `binary_sensor.driveway_wide_scene_object_present` | `sensor.driveway_wide_scene_persons` | `sensor.driveway_wide_scene_vehicles` |
| `driveway_id` | `binary_sensor.driveway_id_scene_object_present` | `sensor.driveway_id_scene_persons` | — |

Scene entities expire after 10 s if no MQTT message received. Image entities (`image.front_latest_detection` etc.) update on `axis/<zone>/scene/snapshot`.

**Double Take entity pattern** (Phase 4): `sensor.dt_<person_name>_confidence`, `binary_sensor.dt_<person_name>_present`

**Automation IDs**: `<domain>_<trigger>_<action>` (e.g. `security_person_detected_notify`). File placement: `automations/<domain>/<action>.yaml`. Domains: `security`, `presence`, `camera`, `notification`.

**Notification service**: `notify.mobile_app_thomas_iphone_15` — used in all alert automations.

## Commands

### Config Sync

```bash
# Linux/macOS
./scripts/sync-config.sh             # sync to HAOS host
./scripts/sync-config.sh --dry-run   # preview only

# Windows (PowerShell)
.\scripts\sync-config.ps1
.\scripts\sync-config.ps1 -DryRun
```

Requires a `.env` file (copy `.env.example` and fill in values):

```
HA_HOST=192.168.68.175
HA_USER=root
HA_SSH_PORT=22222
HA_CONFIG_PATH=/config

# Also needed by configure_cameras.py:
CAM_USER=homeassistant
CAM_PASS=change-me
MQTT_USER=frigate
MQTT_PASS=change-me
```

The script excludes `secrets.yaml`, `.storage/`, `*.db`, and `*.log` from sync. It pushes HA config, Frigate config, and Double Take config in three separate rsync passes.

### YAML Lint

CI runs `yamllint` on all `config/**/*.yaml` and `config/**/*.yml` files on push to `main`/`dev`. To lint locally:

```bash
yamllint config/
```

The CI rule: max line length 120 (warning), truthy values must be `true`/`false`.

### Camera VAPIX Setup (MQTT + AOA)

```bash
python scripts/configure_cameras.py
```

Connects to each camera via VAPIX, configures the MQTT client to publish to Mosquitto, and creates AOA scenarios (PersonOccupancy, VehicleOcc). Safe to re-run — skips scenarios that already exist. Camera IPs are hardcoded in the script; credentials (`CAM_USER`, `CAM_PASS`, `MQTT_USER`, `MQTT_PASS`) are read from `.env`.

**Loitering scenarios cannot be created via script** — the `loitering` AOA type is not supported in current firmware. Configure them manually in each camera's web UI as an "Object in area" scenario named exactly `Loitering` with a minimum time threshold (e.g. 10 s). See `docs/runbooks/aoa-setup.md`.

### SSH to Host

```bash
ssh root@192.168.68.175 -p 22222
```

## Config Directory Layout

```
config/
  home-assistant/       → rsync'd to HAOS /config/
    configuration.yaml
    automations/        → merged via !include_dir_merge_list automations/
      frigate_person_alert.yaml  # root-level (legacy placement)
      security/         # aoa_person_present.yaml, aoa_vehicle_alert.yaml, aoa_loitering_alert.yaml
      notifications/
      presence/
    mqtt_binary_sensors/ → merged via !include_dir_merge_list mqtt_binary_sensors/
      aoa_occupancy.yaml  # AOA Person Occupancy (all 6 cameras)
      aoa_vehicle.yaml    # AOA Vehicle Occupancy (front, driveway_wide, driveway_id)
      aoa_loitering.yaml  # AOA Loitering (front, driveway_wide, driveway_id)
      d6210_radar.yaml    # D6210 radar motion + presence
      scene_presence.yaml # Binary presence from scene/frame (faster than AOA)
    mqtt_sensors/        → merged via !include_dir_merge_list mqtt_sensors/
      scene_metadata.yaml # Axis scene metadata
    mqtt_images/         → merged via !include_dir_merge_list mqtt_images/
      scene_snapshots.yaml # Axis snapshot images — declared under top-level image: key, NOT under mqtt:
    scripts/             → merged via !include_dir_merge_named scripts/
    themes/              → merged via !include_dir_merge_named themes
    lovelace/            # legacy dashboard YAML
    dashboards/
      home-lab.yaml     # 5 views: Home, Cameras, Security, Rooms, Operations
    secrets.yaml.example  # shape only — real secrets.yaml lives on host, never committed
  frigate/
    config.yml          → rsync'd to HAOS /config/frigate/config.yml
  double-take/
    config.yml          → rsync'd to HAOS /config/double-take/config.yml
docker/
  compreface/
    docker-compose.yml  # CompreFace face recognition (Phase 4 Option B)
integrations/            # Design notes for planned integrations (not synced to host)
  axis-analytics/
  face-recognition/
  ai/
```

Automations are split by domain directory under `automations/`. `configuration.yaml` picks them all up with `!include_dir_merge_list automations/`.

**MQTT broker** is configured via the HA UI (Settings → Integrations), stored in `.storage/core.config_entries` — not in `configuration.yaml`. The `mqtt:` key in `configuration.yaml` only declares the sensor entities; the broker connection itself is UI-managed.

**Frigate MQTT host** is `core-mosquitto` (add-on internal DNS name), not the HA IP address. This is set in `config/frigate/config.yml` and must stay as `core-mosquitto` for add-on-to-add-on communication inside HAOS.

## Secrets Pattern

```yaml
# In config YAML:
password: !secret front_camera_password

# In /config/secrets.yaml on host (never committed):
front_camera_password: "the-actual-value"
```

Secret key pattern: `<zone_id>_camera_ip`, `<zone_id>_camera_user`, `<zone_id>_camera_password`, `mqtt_password`, `compreface_api_key`.

## Axis Camera Streams

```
Main (record):   rtsp://<user>:<pass>@<ip>/axis-media/media.amp
Sub (detect):    rtsp://<user>:<pass>@<ip>/axis-media/media.amp?videocodec=h264&resolution=640x360
```

## Axis MQTT Topic Schema

All cameras publish under `axis/<zone_id>/` (set as `deviceTopicPrefix` in VAPIX). Topic patterns for the HA `mqtt_binary_sensors/` definitions:

```
# AOA Person Occupancy (all 6 cameras):
axis/<zone_id>/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active

# AOA Vehicle Occupancy (front, driveway_wide, driveway_id):
axis/<zone_id>/event/ObjectAnalytics/ScenarioOccupancy/VehicleOcc/Active

# AOA Loitering (front, driveway_wide, driveway_id):
axis/<zone_id>/event/ObjectAnalytics/ScenarioLoitering/Loitering/Active

# Scene frame metadata (com.axis.scene.frame.v1 analytics API, ~5 fps when objects present):
axis/<zone_id>/scene/frame   # JSON {detections:[{type:"Human"|"Car"|..., score:0.xx, ...}]}
axis/<zone_id>/scene/track   # used by backyard/storage zones (object track events)
axis/<zone_id>/scene/snapshot # JPEG binary — latest detected object image
```

All AOA payloads are JSON `{Data: {active: bool}}` — use `value_template: "{{ 'on' if value_json.Data.active else 'off' }}"` in HA sensors.

## Git Workflow

- Never commit directly to `main` — use PRs from `dev` or a feature branch
- Branch naming: `feature/<name>`, `fix/<name>`, `docs/<name>`
- Commit format: `<type>: <short summary>` — types: `feat`, `fix`, `docs`, `config`, `refactor`, `chore`

## Phase Status

| Phase | Focus | Status |
|---|---|---|
| 1 | Foundation — naming, areas, MQTT, backups | Done |
| 2 | Cameras + Frigate — 6 cameras, recording, HA integration (99 entities) | Done |
| 3 | Dashboard — 5 views live at `/lovelace/home-lab` | Done |
| 4 | Face recognition (Double Take + recognizer) | Blocked — see below |
| 5 | Axis analytics (ACAP + MQTT) | In Progress — AOA entities defined; MQTT publication from cameras not yet verified |
| 6 | AI integration (Ollama + Qwen) | Future |

### Phase 4 Blocker: Face Recognizer Selection

Double Take is running and configured. Needs a recognizer backend:

**Option A — CodeProject.AI** (easier): Native Windows installer, no Docker, port 32168. Double Take config already points to `192.168.68.118:32168`. Install from codeproject.ai, then restart Double Take.

**Option B — CompreFace** (better accuracy): Requires enabling Intel VT-x in BIOS → Docker Desktop → `docker compose up -d` in `docker/compreface/` → update `config/double-take/config.yml` with the CompreFace API key.

After either option: upload training photos for Thomas/Nils/Hugo/Anna via the Double Take UI at `http://192.168.68.175:3000`.

## Key Docs

- `docs/naming-conventions.md` — authoritative naming reference
- `docs/backlog.md` — prioritized work items (Now/Next/Later/Future)
- `docs/architecture/overview.md` — system diagrams with Mermaid
- `docs/architecture-review.md` — known risks and revised v1 design
- `docs/hardware/cameras.md` — per-camera specs, HA roles, Frigate roles
- `docs/dashboard-design.md` — visual layout for all 5 dashboard views
- `docs/decisions/` — Architecture Decision Records (ADRs)
- `docs/runbooks/` — step-by-step operational procedures (initial-setup, frigate-setup, aoa-setup, d6210-setup, double-take-setup)

## User Context

Thomas works at Axis and has access to Axis ACAP development toolchain, ARTPEC on-camera inference, and Axis MQTT firmware features. This is highly relevant to Phase 5. Suggestions involving Axis-specific features (ACAP apps, custom models, Axis Object Analytics) are welcome.
