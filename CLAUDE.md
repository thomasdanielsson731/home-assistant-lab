# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Production Environment

| Detail | Value |
|---|---|
| Host | Dell Latitude 3120 (x86-64) |
| OS | Home Assistant OS (HAOS) — not Container mode |
| Storage | External 1 TB SSD at `/media/frigate` (Frigate recordings) |
| SSH | `root@<HA_HOST> -p 22222` (SSH add-on) |

## Development Environment

| Detail | Value |
|---|---|
| Workstation | Windows PC |
| Editors | VS Code, Cursor |
| AI | Claude Code (you), Ollama + Qwen (local LLM) |

## Add-ons

| Add-on | Port | Status |
|---|---|---|
| Frigate | 5000 (UI), 8554 (RTSP re-stream) | Planned |
| Double Take | 3000 | Planned |
| Mosquitto | 1883 | Planned |
| SSH & Web Terminal | 22222 | In use |

## Camera Zone IDs

These are canonical — use them verbatim in all config, entities, and filenames.

| Zone ID | Model | Location |
|---|---|---|
| `front` | Axis P3288 | Front entrance |
| `driveway_wide` | Axis Q3558-LVE | Driveway — wide overview |
| `driveway_id` | Axis M2036 | Driveway — identification point |
| `backyard` | Axis Q1656 | Backyard perimeter |
| `storage_ext` | Axis Q1656 | Storage building exterior |
| `storage_int` | Axis M1055 | Storage building interior |
| `driveway_env` | Axis D6210 | Driveway radar (via M2036 I/O port) |

## House Areas

**Ground Floor:** Kitchen / Living Room · Hall (Ground Floor) · Bedroom · Bathroom (Ground Floor)
**Upper Floor:** TV Room · Nils' Room · Hugo's Room · Hall (Upper Floor) · Office · Bathroom (Upper Floor)
**Outdoor:** Front · Driveway · Backyard · Storage Building

**Persons:** Thomas · Nils · Hugo

## Naming Conventions

- See `docs/naming-conventions.md` — follow it for every entity, file, and script
- Zone-first, snake_case for YAML/entities, kebab-case for doc files
- HA entities: `camera.frigate_<zone_id>`, `binary_sensor.frigate_<zone_id>_<object>`

## Commands

### Config Sync

```bash
./scripts/sync-config.sh             # sync to HAOS host
./scripts/sync-config.sh --dry-run   # preview only
```

Requires a `.env` file (copy `.env.example` and set `HA_HOST`). The script excludes `secrets.yaml`, `.storage/`, `*.db`, and `*.log` from sync. It pushes HA config, Frigate config, and Double Take config in three separate rsync passes.

### YAML Lint

CI runs `yamllint` on all `config/**/*.yaml` and `config/**/*.yml` files on push to `main`/`dev`. To lint locally:

```bash
yamllint config/
```

The CI rule: max line length 120 (warning), truthy values must be `true`/`false`.

### SSH to Host

```bash
ssh root@<HA_HOST> -p 22222
```

## Config Directory Layout

```
config/
  home-assistant/       → rsync'd to HAOS /config/
    configuration.yaml
    automations/        → merged via !include_dir_merge_list automations/
      <domain>/
        <action>.yaml   # e.g. security/frigate_person_alert.yaml
    dashboards/
      home-lab.yaml
    secrets.yaml.example  # shape only — real secrets.yaml lives on host, never committed
  frigate/
    config.yml          → rsync'd to HAOS /config/frigate/config.yml
  double-take/
    config.yml          → rsync'd to HAOS /config/double-take/config.yml
```

Automations are split by domain directory under `automations/`. `configuration.yaml` picks them all up with `!include_dir_merge_list automations/`.

## Secrets Pattern

```yaml
# In config YAML:
password: !secret front_camera_password

# In /config/secrets.yaml on host (never committed):
front_camera_password: "the-actual-value"
```

Secret key pattern: `<zone_id>_camera_ip`, `<zone_id>_camera_user`, `<zone_id>_camera_password`, `mqtt_password`, `compreface_api_key`.

## Axis Camera Streams

```
Main (record):   rtsp://<user>:<pass>@<ip>/axis-media/media.amp
Sub (detect):    rtsp://<user>:<pass>@<ip>/axis-media/media.amp?videocodec=h264&resolution=640x360
```

## Current Dashboard Entity IDs (Phase 1)

`config/home-assistant/dashboards/home-lab.yaml` currently references Axis native integration entity IDs (e.g. `camera.q3558_lve_0`, `binary_sensor.0_object_analytics_uppfart_in`). These will be replaced with `camera.frigate_<zone_id>` and `binary_sensor.frigate_<zone_id>_<object>` entity IDs in Phase 2. Inline `# Phase 2:` comments in the dashboard file mark each replacement point.

## Known Config Issues

- `config/frigate/config.yml` uses camera name `front_door` — must be renamed to `front` before Phase 2 to match naming conventions and HA entity ID patterns.

## Git Workflow

- Never commit directly to `main` — use PRs from `dev` or a feature branch
- Commit format: `<type>: <short summary>` — types: `feat`, `fix`, `docs`, `config`, `refactor`, `chore`

## Phase Status

| Phase | Focus | Status |
|---|---|---|
| 1 | Foundation — naming, areas, MQTT, backups | In progress |
| 2 | Cameras + Frigate | Planned |
| 3 | Dashboard | Planned |
| 4 | Face recognition (Double Take + CompreFace) | Planned |
| 5 | Axis analytics (ACAP + MQTT) | Planned |
| 6 | AI integration (Ollama + Qwen) | Future |

## Key Docs

- `docs/naming-conventions.md` — authoritative naming reference
- `docs/roadmap.md` — phase milestones with checkboxes
- `docs/backlog.md` — prioritized work items (Now/Next/Later/Future)
- `docs/cleanup-plan.md` — Phase 1 step-by-step checklist
- `docs/architecture/overview.md` — system diagrams with Mermaid
- `docs/architecture-review.md` — known risks and revised v1 design
- `docs/hardware/cameras.md` — per-camera specs, HA roles, Frigate roles
- `docs/dashboard-design.md` — visual layout for all 5 dashboard views
- `docs/decisions/` — Architecture Decision Records (ADRs)

## User Context

Thomas works at Axis and has access to Axis ACAP development toolchain, ARTPEC on-camera inference, and Axis MQTT firmware features. This is highly relevant to Phase 5. Suggestions involving Axis-specific features (ACAP apps, custom models, Axis Object Analytics) are welcome.
