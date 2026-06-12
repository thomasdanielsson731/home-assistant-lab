# Current Focus

Quick-start context for AI assistants. Read this + [CLAUDE.md](../CLAUDE.md) + [vision.md](vision.md) before touching anything.

---

## Project Identity

**Danielsson Home Intelligence Platform** — event-driven situational awareness.

| UX | Role |
|---|---|
| **Analytics** (HA sidebar) | Primary — events, occupancy, metrics (`http://192.168.68.175:8765/timeline`) |
| **Environment** (HA sidebar) | Env + SPL charts (`http://192.168.68.175:8765/environment`) |
| **Danielsson Home** (`home-lab`) | Secondary — ops, security, cameras, rooms |

**HA:** `192.168.68.175` · **Dev PC:** `192.168.68.136` (CodeProject.AI only)

See [ADR-005](decisions/005-home-intelligence-timeline.md) · [event-model.md](analytics/event-model.md)

---

## Active Phases

| Phase | Focus | Status |
|---|---|---|
| **4** | Face recognition — CodeProject.AI + Double Take | **In progress** |
| **5** | Axis analytics — MQTT to HA + events | Done |
| **6** | Energy bridge + narratives | Partial (Kraftringen pending) |
| **7** | Analytics platform — API + UI + correlation | Done |
| **7b** | InfluxDB long retention | Done (bridge in add-on) |

Phases 1–3 done. Phase 8 (digital twin) follows.

---

## Architecture (production)

```
MQTT sources → Danielsson Insights add-on on HAOS
  event_normalizer → events/timeline.jsonl + metrics.jsonl
  correlation_engine (enriched events)
  influx_metrics_bridge → InfluxDB :8086
  timeline_server :8765 → /timeline, /environment, /story

Double Take (HA) → CodeProject.AI on dev PC :32168
```

Event files on HA: `/share/danielsson-insights/events/`

---

## Automated Maintenance

- **Every 6 h:** `repo-maintenance.ps1` — commit + push + sync HA config
- **Daily 04:00:** above + HA YAML reload
- **HAOS add-on:** Danielsson Insights v0.2.4 — auto-start, Supervisor watchdog on `/timeline`
- **Dev PC:** keep CodeProject.AI running; do **not** run `start-bridges.ps1` (legacy)

---

## Immediate Commands

```powershell
python scripts/health-check.py          # probes HA :8765 + entities + Influx
python scripts/verify-influxdb.py       # Influx auth + write probe
.\scripts\verify-insights-ha.ps1        # add-on smoke test
.\scripts\deploy-insights-to-ha.ps1     # sync scripts to /share
.\scripts\deploy-insights-to-ha.ps1 -UseDirectSecrets   # fix dashboard URLs
.\scripts\stop-bridges.ps1              # ensure dev PC bridges are off
```

On HA (SSH):

```bash
ha apps info 25d01a20_danielsson_insights
ha apps logs 25d01a20_danielsson_insights
```

- Analytics: HA sidebar **Analytics** or `http://192.168.68.175:8765/timeline`
- Environment: HA sidebar **Environment** or `http://192.168.68.175:8765/environment`
- API: `/api/v1/events`, `/api/v1/metrics`, `/api/v1/occupancy`

---

## Manual steps remaining

| Item | Action |
|---|---|
| **Phase 4 — verify match** | Walk `front` → check DT Matches + `dt_thomas_*` |
| Training photos | Thomas ✅ trained; Nils, Hugo, Anna ⬜ |
| **Kök smoke detector** | Pairing button → `configure_smoke_detectors.py --reconfigure` |
| Yale Doorman | Hardware + HA lock entity |
| Kraftringen energy | API credentials for `energy_bridge.py` |
| Companion apps | Nils/Hugo/Anna phones → fix "Unknown" presence |

---

## Key Files

| File | Purpose |
|---|---|
| `danielsson_insights/` | HAOS add-on (v0.2.4) — runs all bridges + timeline |
| `scripts/deploy-insights-to-ha.ps1` | Sync scripts/events to `/share/danielsson-insights/` |
| `scripts/verify-insights-ha.ps1` | Smoke test add-on + secrets |
| `scripts/timeline_server.py` | Analytics UI + REST API |
| `scripts/influx_metrics_bridge.py` | metrics.jsonl → InfluxDB |
| `scripts/install-codeproject-ai.ps1` | Phase 4 CodeProject.AI installer |
| `config/home-assistant/dashboards/house-timeline.yaml` | HA Analytics iframe |
| `config/home-assistant/secrets.yaml` (host) | `timeline_url` / `environment_url` → direct `:8765` |

---

## Documentation Map

| Doc | When to read |
|---|---|
| [backlog.md](backlog.md) | Work queue |
| [roadmap.md](roadmap.md) | Phase tasks |
| [runbooks/timeline-addon.md](runbooks/timeline-addon.md) | HAOS add-on ops |
| [runbooks/codeproject-ai-setup.md](runbooks/codeproject-ai-setup.md) | Phase 4 face recognition |
| [runbooks/influxdb-setup.md](runbooks/influxdb-setup.md) | InfluxDB + add-on bridge |
| [decisions/005-home-intelligence-timeline.md](decisions/005-home-intelligence-timeline.md) | Why API-first timeline |
