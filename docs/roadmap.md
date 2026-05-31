# Roadmap

Long-term vision for the Home Assistant Lab — from stable platform to AI-driven smart home. Phases are sequential; each phase must reach "Done Criteria" before starting the next.

---

## Phase 1 — Foundation `[In Progress]`

**Goal:** Stable, maintainable HAOS installation with correct naming, areas, backups, and MQTT.

| Task | Status |
|---|---|
| HAOS installed on Dell Latitude 3120 | ✅ |
| External 1 TB SSD mounted | ⬜ |
| SSH access configured | ⬜ |
| Mosquitto MQTT running and tested | ⬜ |
| Automatic backups enabled | ⬜ |
| Naming conventions applied | ⬜ |
| Areas created and devices assigned | ⬜ |
| Person entities + presence detection | ⬜ |
| HACS + card packages installed | ⬜ |
| Config syncing from this repo | ⬜ |

**Done when:** [Cleanup plan](cleanup-plan.md) checklist is fully complete.

---

## Phase 2 — Cameras and Frigate `[Planned]`

**Goal:** All 6 Axis cameras streaming reliably into Frigate. Object detection producing HA entities.

| Task | Status |
|---|---|
| Frigate add-on installed | ⬜ |
| `front` (P3288) — dual stream in Frigate | ⬜ |
| `driveway_wide` (Q3558-LVE) — dual stream | ⬜ |
| `driveway_id` (M2036) — dual stream | ⬜ |
| `backyard` (Q1656) — dual stream | ⬜ |
| `storage_ext` (Q1656) — dual stream | ⬜ |
| `storage_int` (M1055) — dual stream | ⬜ |
| D6210 radar sensor — integrated as binary_sensor | ⬜ |
| Frigate HA integration installed | ⬜ |
| Person detection events flowing to automations | ⬜ |
| Vehicle detection on driveway cameras | ⬜ |
| Recording verified to 1 TB SSD | ⬜ |
| Retention policy configured (7 days default) | ⬜ |

**Done when:** All 6 camera feeds visible in HA, detection events trigger automations, recordings going to SSD.

---

## Phase 3 — Dashboard `[Planned]`

**Goal:** Clean, mobile-first dashboard following the [dashboard design](dashboard-design.md).

| Task | Status |
|---|---|
| Sections layout enabled | ⬜ |
| Mushroom Cards configured | ⬜ |
| View: Home — presence, quick status, recent events | ⬜ |
| View: Cameras — all 6 feeds in zone layout | ⬜ |
| View: Rooms — ground floor + upper floor + outdoor | ⬜ |
| View: Security — detections, alarms, event log | ⬜ |
| View: Operations — system health, add-on status, storage | ⬜ |
| Mobile layout tested on phone | ⬜ |
| Frigate Card installed and working in Cameras view | ⬜ |

**Done when:** All 5 views functional on both desktop and mobile.

---

## Phase 4 — Face Recognition `[Planned]`

**Goal:** Known persons identified at `front` and `driveway_id` cameras. Unknown person alerts working.

| Task | Status |
|---|---|
| Double Take add-on installed | ⬜ |
| CompreFace deployed (separate host or VM) | ⬜ |
| Double Take → CompreFace connection verified | ⬜ |
| Frigate → Double Take webhook configured | ⬜ |
| Training images collected for household members | ⬜ |
| Thomas — recognized at `front` (>85% confidence) | ⬜ |
| Nils — recognized at `front` | ⬜ |
| Hugo — recognized at `front` | ⬜ |
| Unknown person alert automation | ⬜ |
| Known person welcome automation (lights, door unlock) | ⬜ |
| Face match events visible in Security dashboard | ⬜ |

**Done when:** All household members reliably identified. Unknown persons trigger push notification with snapshot.

---

## Phase 5 — Axis Analytics `[Planned]`

**Goal:** Leverage Axis ACAP platform for custom detection models and rich MQTT metadata directly from camera firmware.

| Task | Status |
|---|---|
| Audit installed ACAP apps on each camera | ⬜ |
| Enable Axis MQTT on cameras (firmware 10.12+) | ⬜ |
| Axis MQTT → Mosquitto → HA pipeline validated | ⬜ |
| D6210 metadata schema documented | ⬜ |
| Vehicle classification (car / truck / bike) via ACAP | ⬜ |
| Loitering detection on driveway cameras | ⬜ |
| Custom object model trained on lab footage | ⬜ |
| ACAP metadata enriching Frigate event context | ⬜ |
| Axis Object Analytics → HA automation (without Frigate) | ⬜ |

**Notes (Axis context):**
- ARTPEC-8 cameras (Q3558-LVE, Q1656) support on-chip inference — no server needed
- Use AXIS ACAP SDK for custom models; deploy to camera via AXIS Device Manager
- Axis MQTT schema reference: [developer.axis.com](https://developer.axis.com)

**Done when:** At least one custom ACAP model running on a production camera, events flowing to HA automations.

---

## Phase 6 — AI Integration `[Future]`

**Goal:** Local LLM as automation assistant. Vision model for scene understanding. No cloud dependency.

| Task | Status |
|---|---|
| Ollama running stably on Windows dev machine | ⬜ |
| Qwen model benchmarked for HA intent parsing | ⬜ |
| HA Assist pipeline connected to Ollama via REST | ⬜ |
| Natural language automation commands working | ⬜ |
| Qwen-VL (vision model) receiving Frigate snapshots | ⬜ |
| Scene description automation (event → caption → notify) | ⬜ |
| Anomaly detection baseline established | ⬜ |
| AI agent loop: event → context → decision → HA action | ⬜ |
| Wyoming STT/TTS for voice interface (optional) | ⬜ |

**Done when:** At least one end-to-end AI automation loop running without cloud API calls.

---

## Principles

- **Local first** — no cloud processing for security-relevant data
- **One phase at a time** — don't start Phase N+1 until Phase N is stable for 2 weeks
- **Config as code** — every change in HA is reflected in this repo before closing the PR
- **Backward compatible** — new integrations must not break existing automations
