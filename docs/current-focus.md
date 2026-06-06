# Current Focus

Quick-start context for AI assistants. Read this + [CLAUDE.md](../CLAUDE.md) + [vision.md](vision.md) before touching anything.

---

## Project Identity

**Danielsson Home Intelligence Platform** — event-driven situational awareness. Primary UX: **House Intelligence Timeline** at `http://localhost:8765/timeline`. HA dashboard = secondary (ops/security).

See [ADR-005](decisions/005-home-intelligence-timeline.md) · [event-model.md](analytics/event-model.md)

---

## Active Phases

| Phase | Focus | Status |
|---|---|---|
| **7** | Home Intelligence Timeline — API + UI v1 | In progress |
| **5** | Axis analytics — MQTT to HA + events | Bridges running; loitering manual |
| **4** | Face recognition — CodeProject.AI + Double Take | On hold |

Phases 1–3 done. Phase 6 (AI) and 8 (digital twin) follow Phase 7 correlation.

---

## Architecture (target)

```
Sources → event_normalizer.py → Event Store → Correlation (future) → Timeline API → /timeline
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

- Timeline v1: `http://localhost:8765/timeline`
- Event list: `http://localhost:8765/`
- API: `/api/v1/events`, `/api/v1/metrics`, `/api/v1/occupancy`

---

## Manual steps remaining

| Item | Action |
|---|---|
| AOA Loitering | Camera web UI — 3 cameras |
| Yale Doorman | Integrate when hardware arrives |
| Face recognition | CodeProject.AI + training photos |
| Correlation rules | `arrival`, `delivery` live — see correlation-engine.md |

---

## Key Files

| File | Purpose |
|---|---|
| `scripts/event_normalizer.py` | MQTT → canonical events + metrics |
| `scripts/event_store.py` | Persist events, dedup, aggregates |
| `scripts/timeline_api.py` | Query helpers for API v1 |
| `scripts/timeline_server.py` | Timeline UI + REST API |
| `scripts/correlation_engine.py` | Raw → enriched events (`arrival`, `delivery`) |
| `scripts/configure_ha_sidebar.py` | Hide HA panels, default Home Lab |
| `events/timeline.jsonl` | Event stream |
| `events/metrics.jsonl` | Continuous metrics (env, SPL) |

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
