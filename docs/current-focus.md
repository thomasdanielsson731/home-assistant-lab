# Current Focus

Quick-start context for AI assistants. Read this + [CLAUDE.md](../CLAUDE.md) + [vision.md](vision.md) before touching anything.

---

## Project Identity

**Danielsson Insights** — Home Analytics Platform. Everything is an event. HA ingests; analytics docs define the model. See [vision/danielsson-insights.md](vision/danielsson-insights.md) and [analytics/event-model.md](analytics/event-model.md).

---

## Active Phases

| Phase | Focus | Status |
|---|---|---|
| **5** | Axis analytics — AOA, scene, air quality via MQTT | Bridges running, loitering manual step remains |
| **4** | Face recognition — CodeProject.AI + Double Take | Config done, CodeProject.AI install needed |

Phases 1–3 are done. **Phase 7 v0** (event normalizer + timeline) is live on dev PC. Phases 6–8 (AI, InfluxDB, digital twin) are next.

---

## Automated Maintenance

Scheduled tasks (after `.\scripts\install-scheduled-tasks.ps1`):

- **Every 6 h:** auto-commit + push + sync to HAOS
- **Daily 04:00:** above + HA YAML reload (via `HA_TOKEN`)
- **At logon:** `air_quality_bridge.py` + `aoa_bridge.py` + `event_normalizer.py` + `timeline_server.py`

Logs: `logs/maintenance.log` · Runbook: [maintenance.md](runbooks/maintenance.md)

**MQTT bridges on dev PC** (ADR-004): AOA events don't publish natively on FW 12.x without manual UI steps. `aoa_bridge.py` polls `getOccupancy` every 5 s.

---

## Immediate Next Tasks

### 1. Health check (automated)

```powershell
.\scripts\start-bridges.ps1
python scripts/health-check.py
```

Timeline: `http://localhost:8765` · Events: `events/timeline.jsonl`

### 2. Manual steps remaining

| Item | Action |
|---|---|
| AOA Loitering | Camera web UI — 3 cameras |
| Audio SPL | Rules deployed via script; edit MQTT payload per camera in UI (modifier quirk) — audio-analytics-setup.md |
| Yale Doorman | Integrate when hardware arrives |
| Unavailable lights | Re-pair HomeKit/Matter devices |
| Face recognition | **On hold** — see ADR-003 when ready |

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
