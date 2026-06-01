# Roadmap

Long-term vision for the Home Assistant Lab — from stable platform to AI-driven smart home. Phases are sequential; each phase must reach "Done Criteria" before starting the next.

---

## Phase 1 — Foundation `[Done]`

**Goal:** Stable, maintainable HAOS installation with correct naming, areas, backups, and MQTT.

| Task | Status |
|---|---|
| HAOS installed on Dell Latitude 3120 | ✅ |
| External 1 TB SSD mounted at `/media/frigate` | ✅ |
| SSH access configured (port 22222) | ✅ |
| Mosquitto MQTT running and tested | ✅ |
| Automatic backups enabled | ✅ |
| Naming conventions applied | ✅ |
| Areas created and devices assigned (14 areas) | ✅ |
| Person entities created (Thomas, Nils, Hugo, Anna) | ✅ |
| HACS + Mushroom Cards, Frigate Card installed | ✅ |
| Config syncing from this repo | ✅ |
| Presence detection via TP-Link Deco + Companion | ⬜ |

**Done when:** All tasks above complete including presence detection.

---

## Phase 2 — Cameras and Frigate `[Done]`

**Goal:** All 6 Axis cameras streaming reliably into Frigate. Object detection producing HA entities.

| Task | Status |
|---|---|
| Frigate 0.17.1 add-on installed | ✅ |
| `front` (P3288) — dual stream in Frigate | ✅ |
| `driveway_wide` (Q3558-LVE) — dual stream | ✅ |
| `driveway_id` (M2036) — dual stream | ✅ |
| `backyard` (Q1656) — dual stream | ✅ |
| `storage_ext` (Q1656) — dual stream | ✅ |
| `storage_int` (M1055) — dual stream | ✅ |
| Frigate HA integration installed (99 entities) | ✅ |
| Person detection events flowing to automations | ✅ |
| Vehicle detection on driveway cameras | ✅ |
| Recording verified to 1 TB SSD | ✅ |
| Retention policy configured (7 days default) | ✅ |
| D6210 radar sensor — integrated as binary_sensor | ⬜ |

**Done when:** D6210 radar integrated and producing HA entities.

---

## Phase 3 — Dashboard `[Done]`

**Goal:** Clean, mobile-first dashboard following the [dashboard design](dashboard-design.md).

| Task | Status |
|---|---|
| Sections layout enabled | ✅ |
| Mushroom Cards configured | ✅ |
| View: Home — presence, quick status, recent events | ✅ |
| View: Cameras — all 6 feeds in zone layout | ✅ |
| View: Rooms — ground floor + upper floor + outdoor | ✅ |
| View: Security — detections, alarms, event log | ✅ |
| View: Operations — system health, add-on status, storage | ✅ |
| Mobile layout tested on phone | ✅ |
| Frigate Card installed and working in Cameras view | ✅ |

---

## Phase 4 — Face Recognition `[Blocked]`

**Goal:** Known persons identified at `front` and `driveway_id` cameras. Unknown person alerts working.

**Blocker:** Face recognizer backend not yet chosen. See CLAUDE.md Phase 4 section for options.

| Task | Status |
|---|---|
| Double Take 1.13.1 add-on installed and configured | ✅ |
| Frigate → Double Take webhook configured | ✅ |
| CompreFace or CodeProject.AI deployed and connected | ⬜ |
| Training images collected for Thomas, Nils, Hugo, Anna | ⬜ |
| Thomas — recognized at `front` (>85% confidence) | ⬜ |
| Nils — recognized at `front` | ⬜ |
| Hugo — recognized at `front` | ⬜ |
| Anna — recognized at `front` | ⬜ |
| Unknown person alert automation | ⬜ |
| Known person welcome automation (lights, door unlock) | ⬜ |
| Face match events visible in Security dashboard | ⬜ |

**Done when:** All household members reliably identified. Unknown persons trigger push notification with snapshot.

---

## Phase 5 — Axis Analytics `[In Progress]`

**Goal:** Leverage Axis ACAP platform for custom detection models and rich MQTT metadata directly from camera firmware.

| Task | Status |
|---|---|
| Axis MQTT client enabled on all cameras | ⬜ |
| AOA Person Occupancy scenario on all 6 cameras | ⬜ |
| Axis MQTT → Mosquitto → HA pipeline validated | ⬜ |
| AOA Vehicle classification on driveway cameras | ⬜ |
| AOA Loitering detection on driveway cameras | ⬜ |
| D6210 radar metadata schema documented | ⬜ |
| D6210 MQTT events → HA binary_sensor | ⬜ |
| Audit installed ACAP apps on each camera | ⬜ |
| Custom object model trained on lab footage | ⬜ |
| ACAP metadata enriching Frigate event context | ⬜ |

**Notes (Axis context):**
- ARTPEC-8 cameras (Q3558-LVE, Q1656) support on-chip inference — no server needed
- Use AXIS ACAP SDK for custom models; deploy to camera via AXIS Device Manager
- Axis MQTT schema reference: [developer.axis.com](https://developer.axis.com)
- HA config files: `config/home-assistant/mqtt_binary_sensors/`
- Runbook: `docs/runbooks/aoa-setup.md`

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
