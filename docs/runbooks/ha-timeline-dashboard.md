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

## Troubleshooting

| Symptom | Fix |
|---|---|
| No Timeline in sidebar | Re-run `configure_ha_sidebar.py`; check `house-timeline` in `configuration.yaml` |
| Blank iframe | Run `open-timeline-firewall.ps1`; confirm `timeline_server.py` running |
| Timeline hangs | Restart bridges — server uses `ThreadingHTTPServer` |
| `panel_iframe` error in logs | Remove any `panel_iframe:` block from `configuration.yaml` |

## Related

- [ADR-005](../decisions/005-home-intelligence-timeline.md)
- [dashboards/README.md](../dashboards/README.md)
