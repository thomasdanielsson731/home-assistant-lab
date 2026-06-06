# Dashboards

HA Lovelace dashboards are **views** on top of the event model — not the analytics platform itself.

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
