# Dashboards

HA Lovelace dashboards are **secondary** — live ops and security.

**Primary insights UX** is **Analytics** — YAML dashboard **`house-timeline`** in the HA sidebar (iframe → HAOS `:8765/timeline`). Direct: `http://192.168.68.175:8765/timeline`.

See [ADR-005](../decisions/005-home-intelligence-timeline.md) · [ha-timeline-dashboard.md](../runbooks/ha-timeline-dashboard.md)

## Dashboards

| Dashboard | Path | Role |
|---|---|---|
| `home-lab.yaml` | `/lovelace/home-lab` | Home, Cameras, Security, Rooms, Operations |
| `house-timeline.yaml` | `/house-timeline` | Analytics iframe |
| `house-graphs.yaml` | `/house-graphs` | Environment iframe |

## Secrets (host)

```yaml
timeline_url: "http://192.168.68.175:8765/timeline"
environment_url: "http://192.168.68.175:8765/environment"
```

Set via `.\scripts\deploy-insights-to-ha.ps1 -UseDirectSecrets`
