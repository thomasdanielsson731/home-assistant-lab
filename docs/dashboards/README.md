# Dashboards

HA Lovelace dashboards are **secondary** — live ops and security. Primary insights UX is **Analytics** — YAML dashboard **`house-timeline`** in the HA sidebar (full-screen iframe → dev PC `:8765`). Direct: `http://localhost:8765/timeline`. Requires `.\scripts\open-timeline-firewall.ps1` (admin) for LAN clients. See [ADR-005](../decisions/005-home-intelligence-timeline.md).

| Dashboard | URL key | Purpose |
|---|---|---|
| Danielsson Home | `home-lab` | Ops, security, cameras, rooms |
| Analytics | `house-timeline` | Events, occupancy, metrics, zoom |
| Insights | `home-lab/intelligence` | Env graphs only (CO₂, AQI, SPL history) |

| File | Notes |
|---|---|
| Live config | `config/home-assistant/dashboards/home-lab.yaml` |
| Analytics iframe | `config/home-assistant/dashboards/house-timeline.yaml` |
