# Dashboards

HA Lovelace dashboards are **secondary** — live ops and security. Primary insights UX is **House Intelligence Timeline** — YAML dashboard **`house-timeline`** in the HA sidebar (full-screen iframe → dev PC `:8765`). Direct: `http://localhost:8765/timeline`. Requires `.\scripts\open-timeline-firewall.ps1` (admin) for LAN clients. See [ADR-005](../decisions/005-home-intelligence-timeline.md).

| Dashboard | Path | Purpose |
|---|---|---|
| Home Lab | `home-lab` | Ops, security, cameras, rooms |
| Timeline | `house-timeline` | House Intelligence Timeline (events, zoom, correlation) |
| Insights | `home-lab/insights` | Env graphs only (CO₂, AQI, SPL history) |

| Document | Purpose |
|---|---|
| [dashboard-design.md](../dashboard-design.md) | Mushroom Cards layout (5 views) |
| Live config | `config/home-assistant/dashboards/home-lab.yaml` |

## Principle

Dashboards should eventually consume **aggregates** from the event store, not raw HA entity sprawl.

| View | Current data | Target data |
|---|---|---|
| Home | Family — presence, lights, vacuum, quick status | Aggregates + outdoor chips |
| Insights | Env graphs, AOA, counts, timeline, SPL | Event projections + aggregates |
| Security | Live detections + Frigate snapshots | Alerts only |
| Cameras | Frigate feeds | Unchanged |
| Rooms | Lights + vacuum controls | Unchanged |
| Operations | System health | Unchanged |
| Floorplan (future) | — | Zone heatmap + pins |

See [../analytics/event-model.md](../analytics/event-model.md).
