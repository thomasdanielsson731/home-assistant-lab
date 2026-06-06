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
| Home | HA sensors + mini-graphs | Aggregates + outdoor env |
| Security | Frigate + AOA + scene | Event counts + timeline link |
| Cameras | Frigate feeds | Unchanged |
| Timeline (future) | — | Event projections |
| Floorplan (future) | — | Zone heatmap + pins |

See [../analytics/event-model.md](../analytics/event-model.md).
