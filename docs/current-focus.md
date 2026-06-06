# Current Focus

Quick-start context for AI assistants. Read this + [CLAUDE.md](../CLAUDE.md) + [vision.md](vision.md) before touching anything.

---

## Project Identity

**Personal Data Insights Lab** — not a lamp-automation project. Home Assistant is the event hub; the goal is context and insight from sensor/camera data.

---

## Active Phases

| Phase | Focus | Status |
|---|---|---|
| **5** | Axis analytics — AOA, scene, air quality via MQTT | Bridges running, loitering manual step remains |
| **4** | Face recognition — CodeProject.AI + Double Take | Config done, CodeProject.AI install needed |

Phases 1–3 are done. Phases 6–8 (AI, data platform, digital twin) are future.

---

## Automated Maintenance

Scheduled tasks (after `.\scripts\install-scheduled-tasks.ps1`):

- **Every 6 h:** auto-commit + push + sync to HAOS
- **Daily 04:00:** above + HA YAML reload (via `HA_TOKEN`)
- **At logon:** `air_quality_bridge.py` + `aoa_bridge.py`

Logs: `logs/maintenance.log` · Runbook: [maintenance.md](runbooks/maintenance.md)

**MQTT bridges on dev PC** (ADR-004): AOA events don't publish natively on FW 12.x without manual UI steps. `aoa_bridge.py` polls `getOccupancy` every 5 s.

---

## Immediate Next Tasks

### 1. Reload YAML in HA (sync already done)

**Developer Tools → YAML → Reload all YAML configuration**.

Config synced 2026-06-06. Bridge and cameras verified.

### 2. Verify D6210 sensors in HA States

Bridge is publishing live data (temp 16°C, CO₂ 431 ppm, AQI 17). Check `sensor.driveway_env_*` appear after YAML reload.

### 3. Verify scene + AOA sensors in HA

All 6 cameras: MQTT connected, AOA PersonOccupancy OK. Walk in front of `front` camera → check `binary_sensor.front_aoa_person` and `binary_sensor.front_scene_object_present`.

Loitering scenarios still need manual web UI setup on front + driveway cameras.

### 4. Phase 4 — CodeProject.AI

1. Install on Windows dev PC: https://www.codeproject.com/AI/
2. Enable Face Recognition module (port 32168)
3. Restart Double Take add-on
4. Upload training photos at `http://192.168.68.175:3000`

See [ADR-003](decisions/003-face-recognizer.md).

---

## Key Config Files (Phase 5)

| File | Purpose |
|---|---|
| `mqtt_binary_sensors/aoa_occupancy.yaml` | Person occupancy — 6 cameras |
| `mqtt_binary_sensors/aoa_vehicle.yaml` | Vehicle — front, driveway_wide, driveway_id |
| `mqtt_binary_sensors/aoa_loitering.yaml` | Loitering — 3 cameras (manual setup) |
| `mqtt_binary_sensors/scene_presence.yaml` | Fast presence from scene/frame + track |
| `mqtt_sensors/scene_metadata.yaml` | Person/vehicle counts |
| `mqtt_sensors/air_quality.yaml` | D6210 environmental metrics |
| `mqtt_images/scene_snapshots.yaml` | Latest detection snapshots |
| `scripts/configure_cameras.py` | VAPIX: MQTT + AOA scenarios |
| `scripts/air_quality_bridge.py` | D6210 polling → MQTT |

---

## Key Technical Decisions

| Decision | Rationale |
|---|---|
| D6210 via MQTT bridge | REST sensors can't easily POST with dynamic timestamps |
| D6210 via M2036 VAPIX proxy | D6210 has no direct network connection |
| `scene/track` for backyard/storage, `scene/frame` for front/driveway | Different analytics APIs per camera |
| AOA loitering manual only | Firmware VAPIX API doesn't expose loitering type |
| CodeProject.AI for face recognition | Already configured; no Docker/VT-x needed |
| Bridge on Windows dev PC | HAOS has no persistent process manager |

---

## Documentation Map

| Doc | When to read |
|---|---|
| [vision.md](vision.md) | Understanding project direction |
| [scope.md](scope.md) | What's in/out of scope |
| [roadmap.md](roadmap.md) | Phase tasks and done criteria |
| [backlog.md](backlog.md) | Prioritized work queue |
| [agents/](../agents/) | Cursor agent roles |
| [projects/](../projects/) | Sub-project briefs |
