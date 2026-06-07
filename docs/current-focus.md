# Current Focus

Quick-start context for AI assistants. Read this + [CLAUDE.md](../CLAUDE.md) + [vision.md](vision.md) before touching anything.

---

## Project Identity

**Danielsson Home Intelligence Platform** — event-driven situational awareness. Primary UX: **House Intelligence Timeline** — HA sidebar dashboard **Timeline** (`house-timeline` → `http://192.168.68.118:8765/timeline` on dev PC). HA Home Lab = secondary (ops/security).

See [ADR-005](decisions/005-home-intelligence-timeline.md) · [event-model.md](analytics/event-model.md)

---

## Active Phases

| Phase | Focus | Status |
|---|---|---|
| **7** | Home Intelligence Timeline — API + UI + correlation + HA sidebar | Done (InfluxDB add-on optional) |
| **5** | Axis analytics — MQTT to HA + events | PersonOccupancy verified all 6 cameras (2026-06-06); loitering manual only |
| **4** | Face recognition — CodeProject.AI + Double Take | On hold |

Phases 1–3 done. Phase 6 (AI) and 8 (digital twin) follow Phase 7 correlation.

---

## Architecture (target)

```
Sources → event_normalizer.py → Event Store → correlation_engine.py → Timeline API → /timeline
```

---

## Automated Maintenance

- **Every 6 h:** `repo-maintenance.ps1` — commit + push + sync
- **Daily 04:00:** above + HA YAML + MQTT reload
- **At logon / Startup:** `start-bridges.ps1` (bridges + normalizer + timeline)

---

## Immediate Commands

```powershell
.\scripts\start-bridges.ps1
python scripts/health-check.py
```

- Timeline v1: HA sidebar **Timeline** or `http://localhost:8765/timeline`
- Event list: `http://localhost:8765/`
- API: `/api/v1/events`, `/api/v1/metrics`, `/api/v1/occupancy`

---

## Manual steps remaining

| Item | Action |
|---|---|
| AOA PersonOccupancy | ✅ Verified all 6 cameras (2026-06-06) |
| AOA Loitering | Camera web UI — front, driveway_wide, driveway_id |
| Yale Doorman | Hardware + HA lock entity — door MQTT ingestion ready |
| Face recognition | CodeProject.AI + training photos |
| Correlation rules | `arrival`, `delivery`, `bicycle` + door boost — see correlation-engine.md |
| InfluxDB add-on | Install on HAOS + `INFLUX_URL` in `.env` — see influxdb-setup.md |

---

## Key Files

| File | Purpose |
|---|---|
| `scripts/event_normalizer.py` | MQTT → canonical events + metrics |
| `scripts/event_store.py` | Persist events, dedup, aggregates |
| `scripts/timeline_api.py` | Query helpers for API v1 |
| `scripts/timeline_server.py` | Timeline UI + REST API |
| `scripts/correlation_engine.py` | Raw → enriched (`arrival`, `delivery`, `bicycle`) |
| `scripts/configure_ha_sidebar.py` | Hide HA panels, default Home Lab |
| `events/timeline.jsonl` | Event stream |
| `events/metrics.jsonl` | Continuous metrics (env, SPL) |
| `scripts/influx_metrics_bridge.py` | metrics.jsonl → InfluxDB (optional) |
| `config/home-assistant/dashboards/house-timeline.yaml` | HA full-screen Timeline (replaces deprecated `panel_iframe`) |
| `scripts/open-timeline-firewall.ps1` | Windows firewall for LAN access to `:8765` |

---

## Documentation Map

| Doc | When to read |
|---|---|
| [vision.md](vision.md) | Product direction |
| [scope.md](scope.md) | In/out of scope |
| [roadmap.md](roadmap.md) | Phase tasks |
| [backlog.md](backlog.md) | Work queue |
| [analytics/event-model.md](analytics/event-model.md) | Event schema |
| [decisions/005-home-intelligence-timeline.md](decisions/005-home-intelligence-timeline.md) | Timeline architecture |
| [runbooks/ha-timeline-dashboard.md](runbooks/ha-timeline-dashboard.md) | HA sidebar Timeline setup |
