# Danielsson Insights

A personal **Home Analytics Platform** managed as code. Home Assistant ingests data; **events** are the core; timeline, floorplan, and dashboards are views on the same model.

```
Collect → Enrich → Analyze → Visualize → Understand
```

> Not a lamp-automation project — HomeKit handles that.

| Start here | Document |
|---|---|
| Vision + Cursor prompts | [docs/vision/danielsson-insights.md](docs/vision/danielsson-insights.md) |
| Event schema | [docs/analytics/event-model.md](docs/analytics/event-model.md) |
| Phase plan | [docs/roadmap.md](docs/roadmap.md) |
| AI assistant context | [docs/current-focus.md](docs/current-focus.md) |

---

## Architecture at a Glance

```
Axis Cameras (6)  ──RTSP──►  Frigate (NVR + detection)  ──MQTT──►  Home Assistant
        │                                                          ▲
        └──MQTT (AOA, scene)──────────────────────────────────────┘
                                     │
                              Double Take  ──►  CodeProject.AI (face context)
                                     │
                              event_normalizer → correlation_engine
                                     │
                              Timeline API (HAOS :8765) + HA sidebar Analytics
                                     │
                              InfluxDB bridge (Danielsson Insights add-on → :8086)
```

---

## Production Environment

| Component | Detail |
|---|---|
| Host | Dell Latitude 3120 (`192.168.68.175`) |
| OS | Home Assistant OS (HAOS) — x86-64 |
| Storage | External 1 TB SSD at `/media/frigate` |
| NVR | Frigate 0.17.1 add-on |
| Face middleware | Double Take 1.13.1 add-on |
| Face recognizer | CodeProject.AI on Windows dev PC (`192.168.68.136:32168`) |
| MQTT | Mosquitto add-on |

---

## Development Environment

| Component | Detail |
|---|---|
| Workstation | Windows PC at `192.168.68.136` |
| Editors | VS Code + Cursor |
| AI | Claude Code, Cursor agents (`agents/`) |
| Local LLM | Ollama + Qwen (planned) |
| Face AI | CodeProject.AI `:32168` — **only service on dev PC** |
| Config sync | `scripts/sync-config.ps1` / `.sh` via SSH |
| Legacy | `start-bridges.ps1` — **do not run** (platform on HAOS add-on) |

---

## Camera Inventory

| Zone ID | Model | Location | Purpose |
|---|---|---|---|
| `front` | Axis P3288-LVE | Front entrance | Person / face detection |
| `driveway_wide` | Axis Q3558-LVE | Driveway — wide | Area overview, vehicle detection |
| `driveway_id` | Axis M2036-LE | Driveway — close | Identification point |
| `backyard` | Axis Q1656-LE | Backyard | Perimeter coverage |
| `storage_ext` | Axis M1055-L | Storage — exterior | Door / perimeter |
| `storage_int` | Axis Q1656 | Storage — interior | Interior presence |
| `driveway_env` | Axis D6210 | Via M2036 proxy | Air quality (temp, CO₂, AQI, PM) |

---

## Roadmap Summary

| Phase | Focus | Status |
|---|---|---|
| 1 — Foundation | HAOS, MQTT, naming, backups | **Done** |
| 2 — Cameras | 6 cameras in Frigate, detection, recording | **Done** |
| 3 — Dashboard | 5 views, mobile-first | **Done** |
| 4 — Face Recognition | Double Take + CodeProject.AI | **In progress** |
| 5 — Axis Analytics | AOA, scene metadata, air quality | **Done** |
| 6 — AI Integration | Ollama/Qwen, scene understanding | Planned |
| 7 — Home Intelligence Timeline | Events, correlation, Timeline UI, HA sidebar | **Done** |
| 7b — Metrics retention | InfluxDB bridge in HAOS add-on | **Done** |
| 8 — Digital Twin | Unified house state, NL queries | Planned |

Full detail: [docs/roadmap.md](docs/roadmap.md) · Work queue: [docs/backlog.md](docs/backlog.md)

---

## Repository Layout

```
config/                  Service configuration (no secrets committed)
  home-assistant/        HA config, automations, MQTT sensors, dashboards
  frigate/               NVR config + per-camera masks
  double-take/           Face recognition middleware
docs/
  vision/
    danielsson-insights.md  Product vision + Cursor prompts
  vision.md              Lab vision and phase map
  analytics/             Event model, timeline, floorplan, analytics
  scope.md               In/out-of-scope boundaries
  current-focus.md       AI assistant quick-start (read this first)
  roadmap.md             Phase plan with done criteria
  backlog.md             Prioritized work queue
  architecture/          System design and data flows
  hardware/              Server and camera reference
  decisions/             Architecture Decision Records (ADRs)
  runbooks/              Operational procedures
events/                  Event store (person, vehicle, cat, …)
schemas/                 JSON Schema (danielsson-event.schema.json)
agents/                  Cursor agent role definitions
projects/                Sub-project briefs
integrations/            Integration design notes
scripts/                 Sync, camera setup, bridges
```

---

## Getting Started

**For AI assistants:** Read [docs/current-focus.md](docs/current-focus.md) and [CLAUDE.md](CLAUDE.md) first.

**For humans:**

1. Clone this repo on your Windows dev machine
2. Copy `.env.example` → `.env` and fill in `HA_HOST`, credentials
3. Follow [docs/runbooks/initial-setup.md](docs/runbooks/initial-setup.md)
4. Run `.\scripts\sync-config.ps1` to push config to HAOS

## Naming Conventions

[docs/naming-conventions.md](docs/naming-conventions.md) — authoritative reference for all entity IDs, files, and zones.

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) — branch strategy, commit format, PR process.
