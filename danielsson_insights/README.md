# Danielsson Insights — HAOS Add-on

Runs the full analytics platform on the HA host (24/7):

- `timeline_server.py` — Analytics + Environment UI (Ingress on `:8765`)
- `event_normalizer.py` — MQTT → events
- `bridge_watchdog.py` — heartbeat metrics
- `air_quality_bridge.py`, `audio_bridge.py`, `aoa_bridge.py`

CodeProject.AI stays on the Windows dev PC.

## Install

1. **Settings → Add-ons → Add-on store → ⋮ → Repositories**
2. Add exactly (no spaces, no trailing text):

   `https://github.com/thomasdanielsson731/home-assistant-lab`

3. Install **Danielsson Insights** → configure passwords → Start.

Scripts must be on the host share first:

```powershell
.\scripts\deploy-insights-to-ha.ps1 -SkipAddon -UseIngressSecrets
```

See [docs/runbooks/timeline-addon.md](../docs/runbooks/timeline-addon.md).
