# Danielsson Insights — HAOS Add-on

Runs the full analytics platform on the HA host (24/7):

- `timeline_server.py` — Analytics + Environment UI (Ingress on `:8765`)
- `event_normalizer.py` — MQTT → events
- `bridge_watchdog.py` — heartbeat metrics
- `air_quality_bridge.py`, `audio_bridge.py`, `aoa_bridge.py`

CodeProject.AI stays on the Windows dev PC.

## Deploy

From dev PC:

```powershell
.\scripts\deploy-insights-to-ha.ps1
```

Then in Supervisor: **Danielsson Home Lab** repository → install **Danielsson Insights** → configure MQTT/camera passwords → Start.

## Ingress URLs (set in HA secrets)

```yaml
timeline_url: "/api/hassio_ingress/local_danielsson_insights/timeline"
environment_url: "/api/hassio_ingress/local_danielsson_insights/environment"
```
