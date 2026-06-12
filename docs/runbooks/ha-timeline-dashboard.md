# HA Analytics / Environment Dashboard

How the HA sidebar **Analytics** and **Environment** views embed the timeline server.

## Files

| File | Purpose |
|---|---|
| `config/home-assistant/dashboards/house-timeline.yaml` | Panel view + iframe → `:8765/timeline` |
| `config/home-assistant/dashboards/house-graphs.yaml` | Panel view + iframe → `:8765/environment` |
| `/config/secrets.yaml` (host) | `timeline_url`, `environment_url` |

## Recommended URLs (production)

Use **direct HA host URLs** — Ingress in Lovelace iframe often returns **401 Unauthorized**:

```yaml
timeline_url: "http://192.168.68.175:8765/timeline"
environment_url: "http://192.168.68.175:8765/environment"
```

Set via:

```powershell
.\scripts\deploy-insights-to-ha.ps1 -UseDirectSecrets
# or
.\scripts\verify-insights-ha.ps1 -FixDirectUrls
```

## Prerequisites

1. **Danielsson Insights add-on** state = `started` (v0.2.4+)
2. Supervisor **watchdog** enabled (`watchdog: true`)
3. Scripts deployed: `.\scripts\deploy-insights-to-ha.ps1`

## Verify

```powershell
.\scripts\verify-insights-ha.ps1
python scripts/health-check.py
```

Direct in browser:

- Analytics: `http://192.168.68.175:8765/timeline`
- Environment: `http://192.168.68.175:8765/environment`

## Troubleshooting

| Symptom | Fix |
|---|---|
| **401 Unauthorized** in iframe | Use direct `:8765` URLs, not Ingress — `-UseDirectSecrets` |
| Blank iframe | Hard refresh (Ctrl+F5); check add-on logs |
| Panel warning "more than one card" | Fixed — single `vertical-stack` wrapper in YAML |
| Charts empty | Check add-on bridges; `ha apps logs 25d01a20_danielsson_insights` |
| Mobile/iPad | Button card opens URL in Safari/Chrome (iframe blocked on some HTTPS setups) |

## Layout

Both dashboards use a single `vertical-stack` with conditional cards:

- Desktop (≥1025px): full iframe
- Mobile (≤1024px): markdown + "Öppna …" button

## Related

- [timeline-addon.md](timeline-addon.md) — add-on install and ops
- [ADR-005](../decisions/005-home-intelligence-timeline.md)
