# Current Focus

Quick-start context for AI assistants. Read this + [CLAUDE.md](../CLAUDE.md) + [vision.md](vision.md) before touching anything.

---

## Project Identity

**Danielsson Home Intelligence Platform** — event-driven situational awareness.

| UX | Role |
|---|---|
| **Analytics** (HA sidebar) | Primary — events, occupancy, metrics (`https://insights.danielsson.cloud/timeline`) |
| **Environment** (HA sidebar) | Env + SPL charts (`https://insights.danielsson.cloud/environment`) |
| **Händelser** (HA sidebar) | Event list with thumbnails (`https://insights.danielsson.cloud/`) |
| **Hem / Kameror / Säkerhet / Rum** | Family panels — one sidebar item per view |
| **Teknik** (`home-tech`, admin) | Live (nu-läge) · Historik (grafer) · Drift (system) |

**HA:** `https://ha.danielsson.cloud` (remote) · `http://192.168.68.175:8123` (LAN)  
**Dev PC:** `192.168.68.136` (Ollama experiments only — no face rec stack)

See [ADR-005](decisions/005-home-intelligence-timeline.md) · [ADR-006](decisions/006-no-face-no-companion-presence.md) · [event-model.md](analytics/event-model.md)

---

## Active Phases

| Phase | Focus | Status |
|---|---|---|
| **4** | ~~Face recognition~~ | **Removed** — [ADR-006](decisions/006-no-face-no-companion-presence.md) |
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
  timeline_server :8765 → /timeline, /environment, /story, /
```

Event files on HA: `/share/danielsson-insights/events/`

**Not in pipeline:** Double Take, CodeProject.AI, Companion-based household presence.

---

## Automated Maintenance

- **Every 6 h:** `repo-maintenance.ps1` — commit + push + sync HA config
- **Daily 04:00:** above + HA YAML reload
- **HAOS add-on:** Danielsson Insights v0.2.4 — auto-start, Supervisor watchdog on `/timeline`
- **Dev PC:** do **not** run `start-bridges.ps1` (legacy); stop CodeProject.AI if still installed

---

## Immediate Commands

```powershell
python scripts/health-check.py          # probes HA :8765 + entities + Influx
python scripts/verify-influxdb.py       # Influx auth + write probe
.\scripts\verify-insights-ha.ps1        # add-on smoke test
.\scripts\deploy-insights-to-ha.ps1     # sync scripts to /share
.\scripts\set-ha-timeline-secret.ps1 -UseCloudflareUrls   # remote iframe URLs (default in deploy)
.\scripts\stop-bridges.ps1              # ensure dev PC bridges are off
python scripts/configure_ha_sidebar.py    # panel order + hide legacy Overview
```

On HA (SSH):

```bash
ha apps info 25d01a20_danielsson_insights
ha apps logs 25d01a20_danielsson_insights
```

- Analytics: HA sidebar **Analytics** or `https://insights.danielsson.cloud/timeline`
- Environment: HA sidebar **Environment** or `https://insights.danielsson.cloud/environment`
- Händelser: sidebar **Händelser** or `https://insights.danielsson.cloud/`
- API: `/api/v1/events`, `/api/v1/metrics`, `/api/v1/occupancy`

---

## Manual steps remaining

| Item | Action |
|---|---|
| **Kök smoke detector** | Pairing button → `configure_smoke_detectors.py --reconfigure` |
| Yale Doorman | Hardware + HA lock entity |
| Kraftringen energy | API credentials for `energy_bridge.py` |
| Cloudflare Access on Insights | Optional — `insights.danielsson.cloud` is currently unauthenticated |

---

## Key Files

| File | Purpose |
|---|---|
| `danielsson_insights/` | HAOS add-on (v0.2.4) — runs all bridges + timeline |
| `scripts/deploy-insights-to-ha.ps1` | Sync scripts/events to `/share/danielsson-insights/` |
| `scripts/set-ha-timeline-secret.ps1` | Write Insights iframe URLs to host `secrets.yaml` |
| `scripts/configure-cloudflared-insights.sh` | Add `insights.danielsson.cloud` → `:8765` in Cloudflared |
| `scripts/timeline_server.py` | Analytics UI + REST API + event list HTML |
| `config/home-assistant/dashboards/home-tech.yaml` | Teknik — Live / Historik / Drift |
| `config/home-assistant/dashboards/home-events.yaml` | Händelser iframe |
| `config/home-assistant/rest/insights.yaml` | REST counters → `sensor.insights_*_24h` |
| `config/home-assistant/secrets.yaml` (host) | `timeline_url`, `environment_url`, `events_url`, `story_url` |

---

## Documentation Map

| Doc | When to read |
|---|---|
| [backlog.md](backlog.md) | Work queue |
| [roadmap.md](roadmap.md) | Phase tasks |
| [runbooks/remote-access-cloudflare.md](runbooks/remote-access-cloudflare.md) | HA + Insights remote access |
| [runbooks/timeline-addon.md](runbooks/timeline-addon.md) | HAOS add-on ops |
| [decisions/006-no-face-no-companion-presence.md](decisions/006-no-face-no-companion-presence.md) | Why face rec + family Companion are out |
| [runbooks/influxdb-setup.md](runbooks/influxdb-setup.md) | InfluxDB + add-on bridge |
| [decisions/005-home-intelligence-timeline.md](decisions/005-home-intelligence-timeline.md) | Why API-first timeline |
