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
| `driveway_wide` | Axis Q3558-LVE | Driveway — wide overview | 192.168.68.203 |
| `driveway_id` | Axis M2036-LE | Driveway — identification point | 192.168.68.204 |
| `backyard` | Axis Q1656-LE | Backyard perimeter | 192.168.68.202 |
| `recorder` | Axis S3008 | Edge recorder (not a Frigate zone) | 192.168.68.201 |
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

**D6210 air quality entity IDs** (Phase 5 — MQTT bridge via `air_quality_bridge.py`, see `docs/runbooks/d6210-setup.md`): `sensor.driveway_env_temperature`, `sensor.driveway_env_humidity`, `sensor.driveway_env_co2`, `sensor.driveway_env_voc`, `sensor.driveway_env_nox`, `sensor.driveway_env_pm2_5`, `sensor.driveway_env_pm10`, `sensor.driveway_env_aqi`

**Audio SPL entity IDs** (Phase 5 — MQTT bridge via `audio_bridge.py`, see `docs/runbooks/audio-analytics-setup.md`): `sensor.front_audio_spl`, `sensor.driveway_wide_audio_spl`, `sensor.backyard_audio_spl`

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

### Config Sync and Maintenance

```bash
# Linux/macOS
./scripts/sync-config.sh               # sync only
./scripts/repo-maintenance.sh          # commit + push + sync
./scripts/repo-maintenance.sh --reload # + HA YAML reload

# Windows (PowerShell)
.\scripts\sync-config.ps1
.\scripts\repo-maintenance.ps1
.\scripts\repo-maintenance.ps1 -Reload

# Register scheduled tasks (run once)
.\scripts\install-scheduled-tasks.ps1
```

Scheduled: `HomeLab-Maintenance` every 6 h, `HomeLab-MaintenanceDaily` at 04:00 (+ reload). See `docs/runbooks/maintenance.md`.

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

# Required by audio_bridge.py (VAPIX WebSocket SPL stream):
AXIS_ROOT_USER=root
AXIS_ROOT_PASSWORD=change-me

# Required by energy_bridge.py (Kraftringen energy API — stub until credentials provided):
KRAFTRINGEN_USER=change-me
KRAFTRINGEN_PASS=change-me
KRAFTRINGEN_METERING_POINT=change-me

# Optional: InfluxDB long-retention metrics (influx_metrics_bridge.py):
INFLUX_URL=http://192.168.68.175:8086
INFLUX_TOKEN=change-me
INFLUX_ORG=home
INFLUX_BUCKET=homelab
```

The script excludes `secrets.yaml`, `.storage/`, `*.db`, and `*.log` from sync. It pushes HA config, Frigate config, and Double Take config in three passes. The bash script uses `rsync`; the PowerShell script uses `scp` (Windows has no rsync by default).

### YAML Lint

CI runs `yamllint` on all `config/**/*.yaml` and `config/**/*.yml` files on push to `main`/`dev`. To lint locally:

```bash
yamllint config/
```

CI config: `.github/workflows/validate-yaml.yml`. Rules: max line length 120 (warning), truthy values must be `true`/`false`.

### Camera VAPIX Setup (MQTT + AOA)

```bash
python scripts/configure_cameras.py
```

Requires: `pip install requests`

Connects to each camera via VAPIX, configures the MQTT client to publish to Mosquitto, and creates AOA scenarios (PersonOccupancy, VehicleOcc). Safe to re-run — skips scenarios that already exist. Camera IPs are hardcoded in the script; credentials (`CAM_USER`, `CAM_PASS`, `MQTT_USER`, `MQTT_PASS`) are read from `.env`.

**Loitering scenarios cannot be created via script** — the `loitering` AOA type is not supported in current firmware. Configure them manually in each camera's web UI as an "Object in area" scenario named exactly `Loitering` with a minimum time threshold (e.g. 10 s). See `docs/runbooks/aoa-setup.md`.

### D6210 Air Quality Bridge

```bash
python scripts/air_quality_bridge.py
```

Requires: `pip install requests paho-mqtt python-dotenv`

Polls the Axis D6210 air quality sensor every 60 s via the M2036 VAPIX proxy (`192.168.68.204`) and publishes readings to Mosquitto under `axis/driveway_env/air/<metric>`. Metrics published: TEMPERATURE, HUMIDITY, CO2, VOC, NOX, PM2.5, AQI. Reads `HA_HOST`, `MQTT_USER`, `MQTT_PASS` from `.env`. Run manually or schedule via Windows Task Scheduler.

### Audio SPL Bridge

```bash
python scripts/audio_bridge.py
```

Requires: `pip install requests paho-mqtt python-dotenv websocket-client`

Subscribes to SPL Summary events via VAPIX WebSocket (`wssession.cgi` + `ws-data-stream`) on `front`, `driveway_wide`, and `backyard`. Publishes to `axis/<zone>/audio/spl` as JSON `{"max_spl", "min_spl", "spl"}`. Needs `AXIS_ROOT_PASSWORD` in `.env`. Included in `.\scripts\start-bridges.ps1`.

### Event Platform (Danielsson Home Intelligence)

```bash
python scripts/event_normalizer.py   # Frigate, Axis AOA/scene/SPL, D6210 → events/
python scripts/timeline_server.py    # Timeline API + UI
```

- HA sidebar: **Timeline** dashboard (`house-timeline` → dev PC `:8765`)
- Direct: `http://localhost:8765/timeline` (dev PC) · `http://192.168.68.118:8765/timeline` (LAN)
- API: `/api/v1/events`, `/api/v1/metrics`, `/api/v1/occupancy`, `/api/v1/story/today`, `/api/v1/story/<date>`
- LAN access: run `.\scripts\open-timeline-firewall.ps1` as Administrator once

See `docs/decisions/005-home-intelligence-timeline.md` and `docs/runbooks/correlation-engine.md`. Start all bridges: `.\scripts\start-bridges.ps1`.

### Lab health check

```powershell
.\scripts\start-bridges.ps1
python scripts/health-check.py
```

### HA sidebar (automated)

```bash
python scripts/configure_ha_sidebar.py   # hide extra panels, default = Home Lab
```

Insights env graphs: built-in `history-graph` / `statistics-graph` — see `docs/runbooks/hacs-frontend-cards.md`.

### Python Tests

```bash
pip install -r requirements-dev.txt
python -m pytest                              # all tests + 85% coverage gate
pytest tests/test_event_store.py             # single module
pytest tests/test_correlation_engine.py -v   # verbose
pytest --cov-report=html                     # HTML coverage report in htmlcov/
```

Coverage is enforced on: `event_store`, `event_normalizer`, `correlation_engine`, `timeline_api`, `timeline_server`. Test path is configured in `pytest.ini` with `pythonpath = scripts`.

### SSH to Host

```bash
ssh root@192.168.68.175 -p 22222
```

## Event Platform Architecture

The Python event platform in `scripts/` forms a pipeline that normalizes, stores, enriches, and serves all home events.

```
MQTT sources
  Frigate (person/vehicle) ──┐
  Double Take (identity)  ──┤
  Axis AOA/scene/audio    ──┼──► event_normalizer.py ──► event_store.py ──► events/timeline.jsonl
  D6210 air quality       ──┤                                            ──► events/metrics.jsonl
  Yale door lock          ──┤
  energy_bridge.py (stub) ──┘  (Kraftringen electricity + heating → MQTT danielsson/energy/*)
                                        ▼
                             correlation_engine.py  (arrival / delivery / bicycle rules)
                                        ▼ (writes enriched=true events back to timeline.jsonl)
                             story_engine.py  (groups events into 5-min beats → events/stories/<date>.json)
                                        ▼
                             timeline_server.py :8765
                               /api/v1/events · /api/v1/metrics · /api/v1/occupancy
                               /api/v1/story/today · /api/v1/story/<date> · /timeline UI
```

**Key scripts and their roles:**

| Script | Role |
|---|---|
| `event_normalizer.py` | MQTT subscriber → canonical Event schema → EventStore; classifies `behavior` from `scene/track` |
| `event_store.py` | Library: write/dedup/summarize events; reads for API queries |
| `correlation_engine.py` | Derives `arrival`, `delivery`, `bicycle` from raw event combinations |
| `timeline_server.py` | HTTP server on :8765 — REST API + Timeline HTML UI |
| `timeline_api.py` | Query helpers shared between timeline_server and tests |
| `story_engine.py` | Converts timeline events into human-readable daily narratives; writes `events/stories/<date>.json` |
| `influx_metrics_bridge.py` | Tails `metrics.jsonl` → InfluxDB (optional, only if INFLUX_URL set) |
| `air_quality_bridge.py` | D6210 REST API → MQTT `axis/driveway_env/air/{metric}` |
| `audio_bridge.py` | VAPIX WebSocket SPL → MQTT `axis/{zone}/audio/spl` |
| `aoa_bridge.py` | AOA getOccupancy poll → MQTT (firmware workaround) |
| `energy_bridge.py` | Kraftringen energy API → MQTT `danielsson/energy/{electricity,heating}/*` (stub — credentials pending) |

**Event storage** (gitignored, generated at runtime):
- `events/timeline.jsonl` — all raw + enriched events, deduplicated by `event_id`
- `events/metrics.jsonl` — continuous samples (temperature, SPL, CO₂)
- `events/stories/<date>.json` — daily narrative generated by `story_engine.py` (beats + summary)
- `events/aggregates/` — daily rollups per zone

Enriched events set `enriched=true` and `parent_event_ids` pointing to the raw events that triggered them — same file, no schema change.

**Start all services (Windows):**
```powershell
.\scripts\start-bridges.ps1
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
      scene_presence.yaml # Binary presence from scene/frame (faster than AOA)
    mqtt_sensors/        → merged via !include_dir_merge_list mqtt_sensors/
      scene_metadata.yaml # Axis scene metadata
      air_quality.yaml    # D6210 environmental metrics (temperature, humidity, CO2, VOC, NOX, PM2.5, AQI)
      audio_analytics.yaml # Audio SPL (front, driveway_wide, backyard)
    mqtt_images/         → merged via !include_dir_merge_list mqtt_images/
      scene_snapshots.yaml # Axis snapshot images — declared under top-level image: key, NOT under mqtt:
    scripts/             → merged via !include_dir_merge_named scripts/
    themes/              → merged via !include_dir_merge_named themes
    lovelace/            # legacy dashboard YAML
    dashboards/
      home-lab.yaml        # 5 views: Home, Cameras, Security, Rooms, Operations
      house-timeline.yaml  # House Intelligence Timeline (full-screen iframe)
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
axis/<zone_id>/scene/track   # JSON {track_id, event:"NEW"|"LOST", type:"Human"|"Car"|..., duration_sec}
axis/<zone_id>/scene/snapshot # JPEG binary — latest detected object image

# Audio SPL (front, driveway_wide, backyard — via audio_bridge.py):
axis/<zone_id>/audio/spl      # JSON {"max_spl": 55.3, "min_spl": 36.8, "spl": 55.3}
```

All AOA payloads are JSON `{Data: {active: bool}}` — use `value_template: "{{ 'on' if value_json.Data.active else 'off' }}"` in HA sensors.

## Git Workflow

- Never commit directly to `main` — use PRs from `dev` or a feature branch
- Branch naming: `feature/<name>`, `fix/<name>`, `docs/<name>`
- Commit format: `<type>: <short summary>` — types: `feat`, `fix`, `docs`, `config`, `refactor`, `chore`
- See `CONTRIBUTING.md` for PR process and self-review checklist

## Phase Status

| Phase | Focus | Status |
|---|---|---|
| 1 | Foundation — naming, areas, MQTT, backups | Done |
| 2 | Cameras + Frigate — 6 cameras, recording, HA integration (99 entities) | Done |
| 3 | Dashboard — 5 views live at `/lovelace/home-lab` | Done |
| 4 | Face recognition (Double Take + CodeProject.AI) | In Progress — config done, CodeProject.AI install needed |
| 5 | Axis analytics (ACAP + MQTT) | In Progress — AOA, scene, air quality, audio SPL live; loitering manual step remains |
| 6 | AI integration / narratives | In Progress — `story_engine.py` ready (daily story API); `energy_bridge.py` stub awaiting Kraftringen credentials |
| 7 | Home Intelligence Timeline (events, correlation, HA sidebar) | Done |
| 7b | InfluxDB metrics retention (bridge ready; add-on optional) | In progress |
| 8 | Digital twin (unified house state) | Future |

### Phase 4: Face Recognizer

**Decision:** CodeProject.AI on Windows dev PC — see `docs/decisions/003-face-recognizer.md`.

Double Take config already points to `http://192.168.68.118:32168`. Next steps:

1. Install CodeProject.AI on dev PC, enable Face Recognition module
2. Restart Double Take add-on
3. Upload training photos via Double Take UI at `http://192.168.68.175:3000`

Fallback: CompreFace via `docker/compreface/` if accuracy is insufficient.

## Key Docs

- `docs/vision/danielsson-insights.md` — Danielsson Insights product vision + Cursor prompts
- `docs/analytics/event-model.md` — canonical event schema (read before building features)
- `docs/vision.md` — lab vision and phase map
- `docs/scope.md` — in/out-of-scope boundaries
- `docs/current-focus.md` — AI assistant quick-start (read first)
- `docs/naming-conventions.md` — authoritative naming reference
- `docs/roadmap.md` — 8-phase roadmap with current status
- `docs/backlog.md` — prioritized work items
- `agents/` — Cursor agent role definitions
- `projects/` — sub-project briefs
- `docs/architecture/overview.md` — system diagrams with Mermaid
- `docs/architecture-review.md` — known risks and revised v1 design
- `docs/hardware/cameras.md` — per-camera specs, HA roles, Frigate roles
- `docs/dashboard-design.md` — visual layout for all 5 dashboard views
- `docs/decisions/` — Architecture Decision Records (ADRs)
- `docs/runbooks/` — step-by-step operational procedures (initial-setup, frigate-setup, aoa-setup, d6210-setup, audio-analytics-setup, double-take-setup)
- `docs/cleanup-plan.md` — known cleanup tasks and tech debt

## User Context

Thomas works at Axis and has access to Axis ACAP development toolchain, ARTPEC on-camera inference, and Axis MQTT firmware features. This is highly relevant to Phase 5. Suggestions involving Axis-specific features (ACAP apps, custom models, Axis Object Analytics) are welcome.
