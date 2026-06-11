# Current Focus

Quick-start context for AI assistants. Read this + [CLAUDE.md](../CLAUDE.md) + [vision.md](vision.md) before touching anything.

---

## Project Identity

**Danielsson Home Intelligence Platform** — event-driven situational awareness.

| UX | Role |
|---|---|
| **Analytics** (HA sidebar) | Primary — events, occupancy, metrics (`:8765/timeline`) |
| **Environment** (HA sidebar) | Env + SPL charts — shared time range (`:8765/environment`) |
| **Danielsson Home** (`home-lab`) | Secondary — ops, security, cameras, rooms |

Dev PC: `DEV_PC_HOST` in `.env` (currently `192.168.68.136`). HA: `192.168.68.175`.

See [ADR-005](decisions/005-home-intelligence-timeline.md) · [event-model.md](analytics/event-model.md)

---

## Active Phases

| Phase | Focus | Status |
|---|---|---|
| **4** | Face recognition — CodeProject.AI + Double Take | **In progress** |
| **5** | Axis analytics — MQTT to HA + events | Done |
| **7** | Analytics platform — API + UI + correlation | Done |

Phases 1–3 done. Phase 6 (energy/AI narratives) and 8 (digital twin) follow.

---

## Architecture

```
Sources → event_normalizer.py → Event Store → correlation_engine.py → Timeline API → /timeline
```

---

## Automated Maintenance

- **Every 6 h:** `repo-maintenance.ps1` — commit + push + sync
- **Daily 04:00:** above + HA YAML + MQTT reload
- **At logon / Startup:** `start-bridges.ps1` (bridges + normalizer + Analytics server + `bridge_watchdog.py`)

---

## Immediate Commands

```powershell
.\scripts\start-bridges.ps1
python scripts/health-check.py
python scripts/verify-influxdb.py   # Influx auth + write probe
.\scripts\install-codeproject-ai.ps1  # Phase 4 — first-time setup
```

- Analytics UI: HA sidebar **Analytics** or `http://localhost:8765/timeline`
- Event list: `http://localhost:8765/`
- API: `/api/v1/events`, `/api/v1/metrics`, `/api/v1/occupancy`

---

## Manual steps remaining

| Item | Action |
|---|---|
| AOA PersonOccupancy | ✅ All 6 cameras |
| AOA Loitering | ✅ All 6 cameras |
| Storage scene + door AOA zones | ✅ 2026-06-07 |
| Occupancy debounce (60 s) | ✅ |
| **Phase 4 — verify match** | Restart CPAI if needed → walk `front` → check DT Matches + `dt_thomas_*` |
| Training photos | Thomas ✅ trained; Nils, Hugo, Anna ⬜ |
| **InfluxDB writes** | ✅ `home_lab` DB + `influx_metrics_bridge.py` |
| Yale Doorman | Hardware + HA lock entity |
| Kraftringen energy | API credentials for `energy_bridge.py` |
| **Zigbee smoke detectors** | ⏸ Paused — ZHA live, HEIMAN pairing deferred |
| **Timeline on HAOS** | `.\scripts\deploy-insights-to-ha.ps1 -UseIngressSecrets` — [timeline-addon.md](runbooks/timeline-addon.md) |
| **Presence fusion** | ✅ `sensor.house_occupancy_summary` + `sensor.*_presence_fused` |

---

## Key Files

| File | Purpose |
|---|---|
| `scripts/event_normalizer.py` | MQTT → canonical events + metrics |
| `scripts/timeline_server.py` | Analytics UI + REST API |
| `scripts/configure_cameras.py` | MQTT + AOA + scene publishers |
| `scripts/influx_metrics_bridge.py` | metrics.jsonl → InfluxDB |
| `scripts/install-codeproject-ai.ps1` | Phase 4 CodeProject.AI installer |
| `config/double-take/config.yml` | Double Take → CodeProject.AI URL |
| `config/home-assistant/dashboards/house-timeline.yaml` | HA Analytics iframe |
| `config/home-assistant/dashboards/house-graphs.yaml` | HA Environment iframe |
| `scripts/environment_page.py` | Multi-series env charts UI |

---

## Documentation Map

| Doc | When to read |
|---|---|
| [backlog.md](backlog.md) | Work queue |
| [roadmap.md](roadmap.md) | Phase tasks |
| [runbooks/codeproject-ai-setup.md](runbooks/codeproject-ai-setup.md) | Phase 4 face recognition |
| [runbooks/influxdb-setup.md](runbooks/influxdb-setup.md) | InfluxDB auth + bridge |
| [decisions/003-face-recognizer.md](decisions/003-face-recognizer.md) | Why CodeProject.AI |
