# Roadmap

From stable platform to AI-driven Data Insights Lab. Phases are sequential; each must reach its done criteria before the next begins.

Vision: [vision.md](vision.md) · Scope: [scope.md](scope.md) · Work queue: [backlog.md](backlog.md)

---

## Phase 1 — Foundation `[Done]`

**Goal:** Stable HAOS installation with naming, areas, backups, and MQTT.

| Task | Status |
|---|---|
| HAOS on Dell Latitude 3120 | ✅ |
| External 1 TB SSD at `/media/frigate` | ✅ |
| SSH (port 22222) | ✅ |
| Mosquitto MQTT | ✅ |
| Automatic backups | ✅ |
| Naming conventions applied | ✅ |
| 14 areas + person entities | ✅ |
| HACS + Mushroom Cards, Frigate Card | ✅ |
| Config sync from repo | ✅ |
| Presence via TP-Link Deco + Companion | ⬜ |

---

## Phase 2 — Cameras and Frigate `[Done]`

**Goal:** All 6 Axis cameras in Frigate. Detection producing HA entities.

| Task | Status |
|---|---|
| Frigate 0.17.1 add-on | ✅ |
| All 6 cameras — dual stream | ✅ |
| Frigate HA integration (99 entities) | ✅ |
| Person + vehicle detection automations | ✅ |
| Recording to 1 TB SSD, 7-day retention | ✅ |

---

## Phase 3 — Dashboard `[Done]`

**Goal:** Mobile-first dashboard per [dashboard-design.md](dashboard-design.md).

| Task | Status |
|---|---|
| 5 views live at `/lovelace/home-lab` | ✅ |
| Home, Cameras, Rooms, Security, Operations | ✅ |
| Frigate Card + Mushroom Cards | ✅ |

---

## Phase 4 — Face Recognition `[In Progress]`

**Goal:** Known persons identified at `front` and `driveway_id`. Unknown person alerts.

**Decision:** CodeProject.AI on Windows dev PC — see [ADR-003](decisions/003-face-recognizer.md).

| Task | Status |
|---|---|
| Double Take 1.13.1 installed and configured | ✅ |
| Frigate → Double Take webhook | ✅ |
| CodeProject.AI installed on dev PC | ✅ |
| Face module enabled in CodeProject.AI | ✅ |
| Training images for Thomas, Nils, Hugo, Anna | 🔄 Thomas ✅; others ⬜ |
| Recognition at `front` (>85% confidence) | ⬜ |
| Unknown person alert automation | ⬜ |
| Known person context in Security dashboard | ⬜ |

**Done when:** All household members reliably identified. Unknown persons trigger push notification with snapshot.

---

## Phase 5 — Axis Analytics `[Done]`

**Goal:** Axis analytics (AOA, scene metadata, air quality) flowing into HA via MQTT.

| Task | Status |
|---|---|
| HA MQTT entity config (AOA, scene, air quality) | ✅ |
| `configure_cameras.py` — MQTT + AOA scenarios | ✅ |
| `air_quality_bridge.py` — D6210 → MQTT | ✅ |
| `audio_bridge.py` — SPL WebSocket → MQTT (3 cameras) | ✅ |
| Audio SPL sensors verified in HA | ✅ |
| Axis MQTT client enabled on all cameras | ✅ |
| AOA Person Occupancy on all 6 cameras | ✅ verified live 2026-06-06 |
| AOA Vehicle on driveway cameras | ✅ |
| AOA Loitering (manual web UI setup) | ✅ all 6 cameras 2026-06-07 |
| Scene frame/track sensors verified in HA | ✅ health-check |
| D6210 air quality bridge publishing to MQTT | ✅ |
| D6210 air quality sensors verified in HA | ✅ |
| AOA bridge (`aoa_bridge.py`) publishing to MQTT | ✅ |
| AOA sensors verified in HA | ✅ |
| House context template sensors | ✅ |
| End-to-end MQTT pipeline validated | ✅ |
| Audit installed ACAP apps per camera | ⬜ |
| Custom ACAP model on lab footage | ⬜ |

**Config files:**
- `mqtt_binary_sensors/aoa_*.yaml`, `scene_presence.yaml`
- `mqtt_sensors/scene_metadata.yaml`, `air_quality.yaml`, `audio_analytics.yaml`
- `mqtt_images/scene_snapshots.yaml`

**Runbooks:** [aoa-setup.md](runbooks/aoa-setup.md) · [d6210-setup.md](runbooks/d6210-setup.md) · [audio-analytics-setup.md](runbooks/audio-analytics-setup.md)

**Done when:** AOA + scene + air quality sensors verified live in HA for at least one week. ✅ Met 2026-06-07.

---

## Phase 6 — AI Integration `[Future]`

**Goal:** Local LLM for automation assistant and scene understanding. No cloud.

| Task | Status |
|---|---|
| Ollama + Qwen stable on dev PC | ⬜ |
| HA Assist pipeline → Ollama REST | ⬜ |
| Natural language automation commands | ⬜ |
| Vision model (Qwen-VL) on Frigate snapshots | ⬜ |
| Scene description automation (event → caption → notify) | ⬜ |
| Anomaly detection baseline | ⬜ |
| AI agent loop: event → context → decision → action | ⬜ |

**Done when:** One end-to-end AI loop running without cloud API calls.

---

## Phase 7 — Home Intelligence Timeline `[Done — optional InfluxDB/Grafana]`

**Goal:** API-first timeline platform — *what happened?* not entity state.

**Decision:** [ADR-005](decisions/005-home-intelligence-timeline.md)

| Task | Status |
|---|---|
| Event normalizer v0 (Frigate, D6210, Double Take) | ✅ |
| Event normalizer — AOA occupancy, scene, SPL metrics | ✅ |
| Event store (`timeline.jsonl`, `metrics.jsonl`) | ✅ |
| Timeline API v1 (`/api/v1/events`, `metrics`, `occupancy`) | ✅ |
| Timeline UI v1 — horizontal scale, occupancy blocks | ✅ `/timeline` |
| Correlation engine (`arrival`, `delivery`, `bicycle`, door boost) | ✅ |
| Timeline zoom + custom time range | ✅ |
| Door events (HA MQTT) + Yale-ready | ✅ |
| HA sidebar Timeline dashboard (`house-timeline`) | ✅ |
| InfluxDB bridge (`influx_metrics_bridge.py`) | ✅ in HAOS add-on v0.2.4 |
| InfluxDB add-on deployed on HAOS | ✅ `home_lab` DB, auth working |
| Grafana / 7-day trend dashboards | ⬜ |

**Done when:** Timeline shows detections, occupancy blocks, and env metrics for 24 h without opening HA.

---

## Phase 7b — Data Platform (metrics retention) `[Done — Grafana optional]`

**Goal:** Long-term metrics storage and baselines.

| Task | Status |
|---|---|
| `influx_metrics_bridge.py` (metrics.jsonl → InfluxDB) | ✅ |
| InfluxDB add-on deployed on HAOS | ✅ |
| Bridge runs in Danielsson Insights add-on | ✅ v0.2.4 (`influx_url` option) |
| HA sensor → InfluxDB integration | ⬜ optional |
| Event rate baselines per zone/time-of-day | ⬜ |

**Design:** [integrations/data-platform/README.md](../integrations/data-platform/README.md)

---

## Phase 8 — Digital Twin `[Future]`

**Goal:** Unified live state model of the house. Natural-language queries over context.

| Task | Status |
|---|---|
| House state template (who, env, activity, energy) | ⬜ |
| State aggregation from all Phase 5–7 sources | ⬜ |
| "Who is home?" unified answer | ⬜ |
| NL query interface (LLM over stored events) | ⬜ |
| Weekly insight report (automated or agent-generated) | ⬜ |

**Done when:** Can answer "what happened today?" and "why was energy high this week?" from stored data.

---

## Principles

- **Local first** — no cloud processing for security-relevant data
- **Insights over automation** — learn from data, don't just react to it
- **One phase at a time** — stabilise for 2 weeks before expanding
- **Config as code** — every HA change in this repo
- **Document decisions** — ADRs for architecture, runbooks for operations
