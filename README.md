# Home Assistant Lab

Personal smart home infrastructure managed as code. Built on Home Assistant OS with a focus on local processing, professional camera coverage, and a clear path toward AI-driven automation.

---

## Architecture at a Glance

```
Axis Cameras (6)  ──RTSP──►  Frigate (NVR + detection)  ──MQTT──►  Home Assistant
                                     │
                              Double Take  ──►  Face Recognition (CompreFace, planned)
                                     │
                              AI Layer (planned: Ollama / Qwen)
```

---

## Production Environment

| Component | Detail |
|---|---|
| Host | Dell Latitude 3120 |
| OS | Home Assistant OS (HAOS) — x86-64 |
| Storage | External 1 TB SSD (Frigate recordings) |
| NVR | Frigate add-on |
| Face middleware | Double Take add-on |
| Face recognizer | CompreFace (planned) |

---

## Development Environment

| Component | Detail |
|---|---|
| Workstation | Windows PC |
| Editor | VS Code + Cursor |
| AI assistant | Claude Code |
| Local LLM | Ollama + Qwen |
| Config sync | `scripts/sync-config.sh` via SSH |

---

## Camera Inventory

| Zone ID | Model | Location | Purpose |
|---|---|---|---|
| `front` | Axis P3288 | Front entrance | Person / face detection |
| `driveway_wide` | Axis Q3558-LVE | Driveway — wide | Area overview, vehicle detection |
| `driveway_id` | Axis M2036 | Driveway — close | License plate / face identification |
| `backyard` | Axis Q1656 | Backyard | Perimeter coverage |
| `storage_ext` | Axis Q1656 | Storage building — exterior | Door / perimeter monitoring |
| `storage_int` | Axis M1055 | Storage building — interior | Interior presence detection |

### Environmental Sensor

| Zone ID | Model | Connected to | Purpose |
|---|---|---|---|
| `driveway_env` | Axis D6210 | M2036 (driveway_id) | Motion radar + environment |

---

## Software Stack

| Layer | Technology |
|---|---|
| Core platform | Home Assistant OS |
| NVR + detection | Frigate |
| Face middleware | Double Take |
| Face recognizer | CompreFace (planned) |
| MQTT broker | Mosquitto (built-in add-on) |
| Dashboards | Mushroom Cards + Sections layout |
| Config management | Git + SSH sync |
| Development AI | Ollama + Qwen (local LLM) |

---

## Repository Layout

```
config/                  All service configuration (no secrets committed)
  home-assistant/        HA configuration.yaml, automations, scripts, lovelace
  frigate/               Frigate config.yml + per-camera masks
  double-take/           Double Take config.yml
docs/
  architecture/          System design, data flows, network topology
  hardware/              Server, camera, and sensor reference docs
  decisions/             Architecture Decision Records (ADRs)
  runbooks/              Step-by-step operational procedures
integrations/            Design notes for planned integrations
  face-recognition/      CompreFace pipeline design
  axis-analytics/        Axis ACAP + MQTT analytics design
  ai/                    Ollama / Qwen automation assistant design
scripts/                 Config sync, backup, dev utilities
environments/            Production vs development environment notes
.github/                 Issue templates, PR template, CI workflow
```

---

## Roadmap Summary

| Phase | Focus | Status |
|---|---|---|
| 1 — Foundation | HAOS stable, SSH, MQTT, HA configured | In progress |
| 2 — Cameras | All 6 Axis cameras in Frigate, detection working | Planned |
| 3 — Dashboard | Mushroom Cards, Sections layout, mobile-first | Planned |
| 4 — Face Recognition | Double Take + CompreFace, known-person automations | Planned |
| 5 — Axis Analytics | ACAP apps, MQTT metadata into HA | Planned |
| 6 — AI Integration | Ollama/Qwen automation assistant, scene understanding | Planned |

---

## Future AI Ambitions

- **Local LLM automation assistant** — natural language commands via Ollama + Qwen, no cloud dependency
- **Custom object detection** — Axis ACAP custom models trained on lab footage
- **Scene understanding** — vision-language model captions on Frigate events
- **Anomaly detection** — statistical baseline over time-of-day event patterns
- **AI agent loop** — Claude Code + Cursor as the development co-pilot for all of the above

---

## Getting Started

1. Clone this repo on your Windows dev machine
2. Copy `.env.example` → `.env` and fill in `HA_HOST`
3. Follow [docs/runbooks/initial-setup.md](docs/runbooks/initial-setup.md)
4. Run `./scripts/sync-config.sh` to push config to the HAOS host

## Naming Conventions

All entity IDs, file names, and zone identifiers follow the conventions in [docs/naming-conventions.md](docs/naming-conventions.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch strategy and PR process.
