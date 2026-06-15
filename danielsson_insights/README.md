# Danielsson Insights — HAOS Add-on

Runs the full analytics platform on the HA host (24/7):

- `timeline_server.py` — Analytics + Environment UI (`:8765`)
- `event_normalizer.py` — MQTT → events
- `bridge_watchdog.py` — heartbeat metrics
- `air_quality_bridge.py`, `audio_bridge.py`, `aoa_bridge.py`
- `influx_metrics_bridge.py` — metrics → InfluxDB (when `influx_url` set)

**Version:** 0.2.4 — Supervisor watchdog, direct URL dashboard support, Influx in add-on.

## Install

1. **Settings → Add-ons → Add-on store → ⋮ → Repositories**
2. Add exactly:

   `https://github.com/thomasdanielsson731/home-assistant-lab`

3. Deploy scripts, then install add-on:

```powershell
.\scripts\deploy-insights-to-ha.ps1
.\scripts\deploy-insights-to-ha.ps1 -UseDirectSecrets
```

4. Configure passwords → Start → verify `http://192.168.68.175:8765/timeline`

See [docs/runbooks/timeline-addon.md](../docs/runbooks/timeline-addon.md).
