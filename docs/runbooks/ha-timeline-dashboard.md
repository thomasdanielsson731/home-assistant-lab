# HA Analytics / Environment / Händelser Dashboard

How the HA sidebar **Analytics**, **Environment**, and **Händelser** views embed the timeline server.

## Files

| File | Purpose |
|---|---|
| `config/home-assistant/dashboards/house-timeline.yaml` | Panel view + iframe → `/timeline` |
| `config/home-assistant/dashboards/house-graphs.yaml` | Panel view + iframe → `/environment` |
| `config/home-assistant/dashboards/home-events.yaml` | Panel view + iframe → `/` (event list) |
| `/config/secrets.yaml` (host) | `timeline_url`, `environment_url`, `events_url`, `story_url` |

## Recommended URLs (production)

Use **Cloudflare HTTPS URLs** for LAN + remote — Ingress in Lovelace iframe returns **401 Unauthorized**:

```yaml
timeline_url: "https://insights.danielsson.cloud/timeline"
environment_url: "https://insights.danielsson.cloud/environment"
events_url: "https://insights.danielsson.cloud/"
story_url: "https://insights.danielsson.cloud/story"
```

Setup:

```powershell
# On HAOS (SSH) — add insights.danielsson.cloud → :8765
scp scripts/configure-cloudflared-insights.sh root@192.168.68.175:/tmp/
ssh root@192.168.68.175 -p 22222 sh /tmp/configure-cloudflared-insights.sh

.\scripts\set-ha-timeline-secret.ps1 -UseCloudflareUrls
# or full deploy (defaults to Cloudflare URLs):
.\scripts\deploy-insights-to-ha.ps1
```

**LAN-only (home WiFi):**

```powershell
.\scripts\set-ha-timeline-secret.ps1 -UseDirectUrls
```

→ `http://192.168.68.175:8765/...` — breaks remote iframe access.

## Prerequisites

1. **Danielsson Insights add-on** state = `started` (v0.2.4+)
2. Supervisor **watchdog** enabled (`watchdog: true`)
3. Scripts deployed: `.\scripts\deploy-insights-to-ha.ps1`
4. Cloudflared tunnel includes Insights host (see [remote-access-cloudflare.md](remote-access-cloudflare.md))

## Verify

```powershell
.\scripts\verify-insights-ha.ps1
python scripts/health-check.py
```

Direct in browser:

- Analytics: `https://insights.danielsson.cloud/timeline`
- Environment: `https://insights.danielsson.cloud/environment`
- Händelser: `https://insights.danielsson.cloud/`

## Troubleshooting

| Symptom | Fix |
|---|---|
| **401 Unauthorized** in iframe | Use Cloudflare or direct `:8765` URLs — not Ingress |
| Blank iframe remotely | Run `configure-cloudflared-insights.sh`; check `-UseCloudflareUrls` secrets |
| Blank iframe on LAN only | `-UseDirectUrls` or verify add-on on `:8765` |
| Panel warning "more than one card" | Fixed — single `vertical-stack` wrapper in YAML |
| Charts empty | Check add-on bridges; `ha apps logs 25d01a20_danielsson_insights` |
| Mobile/iPad | Button card opens URL in Safari/Chrome (iframe blocked on some HTTPS setups) |

## Layout

Analytics, Environment, and Händelser dashboards use a single `vertical-stack` with conditional cards:

- Desktop (≥1025px): full iframe
- Mobile (≤1024px): markdown + "Öppna …" button

## Related

- [timeline-addon.md](timeline-addon.md) — add-on install and ops
- [remote-access-cloudflare.md](remote-access-cloudflare.md) — HA + Insights tunnels
- [ADR-005](../decisions/005-home-intelligence-timeline.md)
