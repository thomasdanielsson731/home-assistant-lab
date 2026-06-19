# Project Backlog

Prioritized work items. Effort: S (< 2h), M (half-day), L (full day), XL (multiple days).

Vision: [vision.md](vision.md) · Active phase: **6 (Energy + narratives)**

**Runtime (2026-06-14):** Analytics platform on **Danielsson Insights add-on v0.2.4** on HAOS. Remote access via **Cloudflare** (`ha.danielsson.cloud`, `insights.danielsson.cloud`). Face recognition and family Companion presence **removed** — [ADR-006](decisions/006-no-face-no-companion-presence.md).

---

## Done — Phase 5 Axis Analytics

Complete the Axis analytics pipeline end-to-end.

| # | Item | Effort | Status |
|---|---|---|---|
| P5-1 | Commit + sync pending config changes | S | ✅ |
| P5-2 | Start `air_quality_bridge.py`, verify `sensor.driveway_env_*` | S | ✅ |
| P5-3 | Run `configure_cameras.py` — MQTT + AOA on all cameras | M | ✅ |
| P5-3b | PersonOccupancy verified live on all 6 cameras | S | ✅ verified 2026-06-06 |
| P5-4 | Verify scene/frame on `front` via MQTT subscribe | S | ✅ |
| P5-5 | AOA via `aoa_bridge.py` — poll getOccupancy → MQTT | M | ✅ HAOS add-on |
| P5-5b | Audio SPL via `audio_bridge.py` — WebSocket → MQTT | M | ✅ HAOS add-on |
| P5-6 | Loitering scenarios on all 6 cameras (manual UI) | M | ✅ verified 2026-06-07 |
| P5-7 | Add analytics cards to Security + Operations dashboard views | M | ✅ |
| P5-9 | Insights graphs — built-in history/statistics cards | S | ✅ |
| P5-10 | `scripts/health-check.py` — automated lab status | S | ✅ HAOS mode |
| P5-8 | House context template sensors | S | ✅ |
| P5-8 | Update stale docs (d6210 runbook ✅, backlog ✅, README ✅) | S | ✅ |

| P7-panel | Dashboard panel review fixes (scripts, multisensor notify, Anna copy) | ✅ 2026-06-14 |
| P7-17 | Sidebar split — Hem, Kameror, Säkerhet, Händelser, Rum (replace `home-lab`) | ✅ 2026-06-14 |
| P7-18 | Cloudflare remote (`ha.danielsson.cloud`) + Insights tunnel (`insights.danielsson.cloud`) | ✅ 2026-06-14 |
| P7-19 | Händelser panel — iframe event list with thumbnails (`home-events.yaml`) | ✅ 2026-06-14 |
| P7-20 | Teknik UX — Live / Historik / Drift views, perimeter fusion, Insights REST counters | ✅ 2026-06-14 |
| P7-21 | Notification deep links → Händelser / Säkerhet / Teknik Drift | ✅ 2026-06-14 |
| P7-22 | Panel review batch 1 — MQTT counters, loitering bridge, timeline UX | ✅ 2026-06-14 |
| P7-23 | Panel review batches 2–8 — coalesce display sensors, nav chips, alerts | ✅ 2026-06-14 |

---

## Removed — Phase 4 Face Recognition (ADR-006)

| # | Item | Status |
|---|---|---|
| — | Double Take, CodeProject.AI, CompreFace, `dt_*`, presence fusion | ❌ Removed 2026-06-14 |
| — | Family Companion presence / "who is home" dashboard | ❌ Out of scope |
| — | Thomas security push (`notify.mobile_app_thomas_iphone_15`) | ✅ Kept in automations (disabled by default) |

---

## Done — Phase 7 Analytics Platform

| # | Item | Effort | Status |
|---|---|---|---|
| P7-1 | Event normalizer — Frigate + Axis + D6210 → JSON | M | ✅ |
| P7-2 | Timeline list UI (`:8765`) | S | ✅ |
| P7-3 | Verify person events from live Frigate tracks | S | ✅ health-check |
| P7-4 | Bridge startup on HAOS add-on (24/7) | S | ✅ add-on v0.2.4 |
| P7-5 | ADR-005 + scope/vision docs | S | ✅ |
| P7-6 | Normalizer — AOA occupancy, scene, SPL metrics | M | ✅ |
| P7-7 | Timeline API v1 + `/timeline` UI | M | ✅ |
| P7-8 | Correlation engine (`arrival`, `delivery`, `bicycle`, door) | L | ✅ |
| P7-9 | Timeline zoom + custom time range | M | ✅ |
| P7-10 | InfluxDB metrics retention | M | ✅ bridge in add-on + `home_lab` DB |
| P7-11 | HA Timeline dashboard (`house-timeline`) | S | ✅ direct `:8765` URLs |
| P7-12 | Bridge heartbeat metrics + `bridge_watchdog.py` | S | ✅ |
| P7-13 | HAOS Insights add-on + deploy script | M | ✅ v0.2.4, watchdog, Ingress-safe URLs |
| P7-14 | Outdoor presence template + house context sensors | M | ✅ |
| P7-15 | Ingress 401 fix — Cloudflare Insights URLs + regression tests | M | ✅ 2026-06-14 |
| P7-16 | Dashboard polish — smoke section, panel warning, camera grid | S | ✅ 2026-06-11 |

---

## Now — Phase 6 AI / Narratives

| # | Item | Effort | Status |
|---|---|---|---|
| P6-1 | `story_engine.py` — daily narrative beats | M | ✅ |
| P6-2 | `/api/v1/story/today` + `/story` HTML page | S | ✅ |
| P6-3 | `energy_bridge.py` stub (Kraftringen API) | M | ✅ stub ready — credentials pending |
| P6-4 | Scene track behavior classification (`behavior` event type) | M | ✅ |
| P6-5 | Environment sidebar + Analytics/Story links | S | ✅ `house-graphs` iframe + `/environment` charts |
| P6-8 | Ollama `ai_summary` in story_engine (optional) | S | ✅ `OLLAMA_URL` |
| P6-9 | Baseline + anomaly engine | M | ✅ `baseline_engine.py` |
| P6-6 | Implement Kraftringen API calls in `energy_bridge.py` | M | ⬜ awaiting credentials |
| P6-7 | Energy events in timeline + story beats | S | ⬜ depends on P6-6 |

## Later — Phase 6 Extended + Phase 7 Data Platform

| # | Item | Effort | Dependencies |
|---|---|---|---|
| L1 | Ollama + Qwen stable API on dev PC | S | None |
| L2 | InfluxDB add-on on HAOS | M | ✅ deployed |
| L3 | HA → InfluxDB for energy + env + detection metrics | M | L2 ✅, P7-10 ✅ |
| L4 | HA Assist → Ollama REST integration | M | L1 |
| L5 | Vision model on Frigate snapshots | L | L1, Phase 2 |
| L6 | Scene description automation | M | L5 |
| L7 | Event rate baselines (zone × hour × object) | L | ✅ `baseline_engine.py` |
| L8 | Grafana dashboard or HA history trends | M | ✅ `home-metrics-7d` via `deploy-grafana.ps1` |
| L9 | Custom ACAP model on lab footage | XL | P5-8, Axis dev access |

---

## Future — Phase 8 Digital Twin

| # | Item | Effort | Dependencies |
|---|---|---|---|
| F1 | House state template sensor (outdoor activity, env, energy) | M | P5 |
| F2 | NL query over stored events (LLM + context) | L | L1, L3 |
| F3 | Weekly insight report (agent-generated) | M | F1, L7 |
| F4 | Wyoming STT/TTS for local voice (optional) | M | L4 |

---

## Completed (archive)

<details>
<summary>Foundation, Frigate, Dashboard (Phases 1–3)</summary>

| # | Item | Status |
|---|---|---|
| — | HAOS, SSH, MQTT, backups, naming, areas | ✅ |
| — | 6 cameras in Frigate, 99 HA entities | ✅ |
| — | Sidebar panels (Hem, Kameror, Säkerhet, Händelser, Rum) + Teknik admin (`/lovelace/home-tech/live`) | ✅ |
| — | Person detection → push notification | ✅ |
| F2 | Axis MQTT config via `configure_cameras.py` | ✅ |
| F3 | HA sensors from Axis MQTT metadata | ✅ |

</details>

---

## Zigbee smoke detectors

3× HEIMAN paired in ZHA (2026-06-11). Timeline + Security dashboard + push alert wired.

| # | Item | Effort | Status |
|---|---|---|---|
| Z1 | Pair 3× HEIMAN smoke detectors | M | ✅ ZHA network |
| Z2 | Areas + `SMOKE_ENTITIES` + entity names | S | ✅ 3/3 live |
| Z3 | Smoke alert automation + timeline | S | ✅ |

**Next:** Water sensor (SNZB-05P) — re-pair if `unavailable`; see [zigbee-setup.md](runbooks/zigbee-setup.md)

---

## Dropped / On Hold

| Item | Reason |
|---|---|
| Double Take / CodeProject.AI / CompreFace | Removed — ADR-006 |
| Family Companion presence | Household declined HA app |
| Nabu Casa remote access | Superseded by Cloudflare Tunnel — see [remote-access-cloudflare.md](runbooks/remote-access-cloudflare.md) |
| Ingress URLs in Lovelace iframe | 401 unreliable — use `https://insights.danielsson.cloud/...` (or LAN `:8765` at home only) |
| Legacy `home-lab` / `home-anna.yaml` | Replaced by sidebar panels 2026-06-14 |
| ALPR | No current automation need |
| HA REST sensors for D6210 | Replaced by MQTT bridge |
| HA REST sensors for Insights counters | Replaced by MQTT (`mqtt_sensors/insights_counters.yaml` + bridge) |
| Meross MS100F + MSH300 hub | Hub suspected dead |
| Dev PC bridges (`start-bridges.ps1`) | Replaced by HAOS add-on 2026-06-11 |
