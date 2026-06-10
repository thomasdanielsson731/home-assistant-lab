# HA Analytics Dashboard Runbook

Embed Analytics (timeline UI) in Home Assistant sidebar.

## Background

`panel_iframe` was **removed** from Home Assistant (2024.4+). Replacement: YAML Lovelace dashboard with full-screen iframe card.

## Config (in repo)

| File | Purpose |
|---|---|
| `config/home-assistant/dashboards/house-timeline.yaml` | Panel view + iframe → dev PC |
| `config/home-assistant/configuration.yaml` | Registers `house-timeline` dashboard |
| `/config/secrets.yaml` (host) | `timeline_url` — legacy; dashboard uses hardcoded LAN URL |

## Prerequisites

1. Dev PC bridges running: `.\scripts\start-bridges.ps1`
2. Timeline URL matches dev PC LAN IP (not always `.118`):

```powershell
.\scripts\update-timeline-url.ps1   # auto-detect IP → HA secrets.yaml
```
3. Windows firewall (once, as Administrator):

```powershell
.\scripts\open-timeline-firewall.ps1
```

## Deploy

```powershell
.\scripts\sync-config.ps1
ssh root@192.168.68.175 -p 22222 "ha core restart"
python scripts/configure_ha_sidebar.py
```

## Verify

- HA sidebar shows **Analytics** next to **Danielsson Home**
- Click Analytics → full-screen timeline UI loads
- If blank: test URL in browser on the same device; check firewall on dev PC

## Mobile and iPad

Embedded iframes to `http://192.168.68.x:8765` often **fail on phone and iPad** even when desktop works.

| Cause | What to do |
|---|---|
| **Mixed content** | HA Companion or Nabu Casa uses **HTTPS**; browsers block HTTP iframes. On LAN, open HA as `http://192.168.68.175:8123` (not HTTPS). |
| **Iframe limits** | Safari on iOS/iPadOS is stricter than desktop. Use the dashboard **Öppna i Safari** button (shown on screens ≤1024px) or open the URL directly. |
| **CDN / offline** | Environment charts load Chart.js from the dev PC (`/static/…`), not jsdelivr — no internet required on the client. |
| **Dev PC asleep** | Run `.\scripts\start-bridges.ps1` or ensure the `HomeLab-Bridges` scheduled task runs at logon. |

Direct URLs (replace IP if `update-timeline-url.ps1` changed it):

- Analytics: `http://192.168.68.136:8765/timeline`
- Environment: `http://192.168.68.136:8765/environment`

After changing dashboard YAML, sync config and reload Lovelace (or restart HA core).

## Troubleshooting

| Symptom | Fix |
|---|---|
| No Timeline in sidebar | Re-run `configure_ha_sidebar.py`; check `house-timeline` in `configuration.yaml` |
| Blank iframe | Run `open-timeline-firewall.ps1`; confirm `timeline_server.py` running |
| Works on PC, not iPad | Use Safari button on dashboard or open `:8765` URL directly; avoid HTTPS HA |
| Charts empty, text OK | Restart bridges; check `/api/v1/metrics` in browser |
| Timeline hangs | Restart bridges — server uses `ThreadingHTTPServer` |
| `panel_iframe` error in logs | Remove any `panel_iframe:` block from `configuration.yaml` |

## Related

- [ADR-005](../decisions/005-home-intelligence-timeline.md)
- [dashboards/README.md](../dashboards/README.md)
