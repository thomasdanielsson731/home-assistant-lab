# Dashboards

HA Lovelace dashboards are **secondary** — live ops and security.

**Primary insights UX** is **Analytics** — YAML dashboard **`house-timeline`** in the HA sidebar (iframe → Insights timeline). Remote: `https://insights.danielsson.cloud/timeline`.

See [ADR-005](../decisions/005-home-intelligence-timeline.md) · [ha-timeline-dashboard.md](../runbooks/ha-timeline-dashboard.md) · [remote-access-cloudflare.md](../runbooks/remote-access-cloudflare.md)

## Sidebar panels (2026-06-14)

| Dashboard file | Sidebar title | Path | Role |
|---|---|---|---|
| `home-hem.yaml` | Hem | `/lovelace/home-hem/home` | At-a-glance — outdoor activity, lights |
| `home-cameras.yaml` | Kameror | `/lovelace/home-cameras/cameras` | Frigate feeds |
| `home-security.yaml` | Säkerhet | `/lovelace/home-security/security` | Detections, smoke, alerts |
| `home-events.yaml` | Händelser | `/lovelace/home-events/events` | Insights event list + thumbnails |
| `home-rooms.yaml` | Rum | `/lovelace/home-rooms/rooms` | Room controls |
| `home-tech.yaml` | Teknik (admin) | `/lovelace/home-tech/live` | Live · Historik · Drift |
| `house-timeline.yaml` | Analytics | `/house-timeline` | Timeline iframe |
| `house-graphs.yaml` | Environment | `/house-graphs` | Environment charts iframe |

Legacy **`home-lab`** / **`home-anna.yaml`** removed — use sidebar panels above. Default panel: **Hem** (`configure_ha_sidebar.py`).

## Teknik views (`home-tech.yaml`, admin only)

| View | Path | Content |
|---|---|---|
| **Live** | `/lovelace/home-tech/live` | Perimeter nu (F/A/S/M), D6210 chips, korrelationer, senaste bilder |
| **Historik** | `/lovelace/home-tech/historik` | Innetemp, ute 7d/90d, SPL — HA recorder graphs |
| **Drift** | `/lovelace/home-tech/ops` | Kameror, inspelning, Insights health, system, backup |

## Secrets (host)

**Remote (recommended):**

```yaml
timeline_url: "https://insights.danielsson.cloud/timeline"
environment_url: "https://insights.danielsson.cloud/environment"
events_url: "https://insights.danielsson.cloud/"
story_url: "https://insights.danielsson.cloud/story"
```

Set via `.\scripts\set-ha-timeline-secret.ps1 -UseCloudflareUrls` (default in `deploy-insights-to-ha.ps1`).

**LAN-only fallback:** `-UseDirectUrls` → `http://192.168.68.175:8765/...`

Do **not** use Ingress URLs in iframes — returns 401 remotely.

## Insights counters (Teknik + Händelser)

MQTT via `insights_counters_bridge.py` in Danielsson Insights add-on (`danielsson/insights/*_24h`):

- `sensor.insights_events_24h` (+ `sensor.insights_*_24h_display` template coalesce)
- `sensor.insights_arrivals_24h`
- `sensor.insights_deliveries_24h`
- `sensor.insights_persons_24h`
- `sensor.insights_bicycles_24h`

Used on Teknik **Live**, **Händelser** chips, and **Drift** (data health).
