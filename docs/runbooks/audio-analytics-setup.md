# AXIS Audio Analytics SPL → Home Assistant

## Status on this lab

Audio Analytics runs as a **firmware plugin** (`audioanalytics.cgi`), not a separate ACAP in the applications list.

Verified on:

| Zone | Camera | IP | SoundPressureLevel |
|---|---|---|---|
| `front` | P3288-LVE | 192.168.68.200 | ✅ enabled |
| `driveway_wide` | Q3558-LVE | 192.168.68.203 | ✅ enabled |
| `backyard` | Q1656-LE | 192.168.68.202 | ✅ enabled |

Check from dev PC:

```powershell
python scripts/configure_audio_analytics.py
```

## Why SPL needs a bridge

SPL **Summary** events (MaxSPL / MinSPL every ~60 s) are *application data*. They are **not** exposed via:

- `analytics-mqtt` data sources (scene metadata only)
- Standard MQTT event filters (`configureEventPublication`)
- Reliable MQTT action-rule payloads over SOAP (`#MaxSPL` collides with `#M` MAC modifier)

## Recommended: `audio_bridge.py` (no camera UI step)

Add root credentials to `.env`:

```
AXIS_ROOT_USER=root
AXIS_ROOT_PASSWORD=<camera-root-password>
```

Start the bridge (included in Danielsson Insights add-on on HAOS):

```bash
ha apps info 25d01a20_danielsson_insights   # state: started
ha apps logs 25d01a20_danielsson_insights | grep audio
```

Legacy dev PC: `.\scripts\start-bridges.ps1`

The bridge uses the VAPIX WebSocket event API and publishes to:

```
axis/<zone>/audio/spl  {"max_spl": 55.3, "min_spl": 36.8, "spl": 55.3}
```

Expected: one message per camera every ~60 s.

## Alternative: camera MQTT action rule (manual payload)

If you prefer on-camera MQTT without the bridge:

```powershell
python scripts/configure_audio_spl_rules.py   # creates rule + action (SOAP)
```

Then edit **payload** once per camera in the web UI  
(System → Events → Actions → `ha_spl_mqtt_<zone>`):

```json
{"max_spl":#MaxSPL,"min_spl":#MinSPL,"spl":#MaxSPL}
```

Use **unquoted** modifiers in the UI field.

## Verify MQTT

Subscribe to `axis/+/audio/spl` — expect JSON with numeric `max_spl` every ~60 s.

## HA entities

Defined in `mqtt_sensors/audio_analytics.yaml`:

- `sensor.front_audio_spl`
- `sensor.driveway_wide_audio_spl`
- `sensor.backyard_audio_spl`

## Dashboard

**Insights → AUDIO ANALYTICS (SPL)** — live values + 7-day history graph.

## Scripts

| Script | Purpose |
|---|---|
| `configure_audio_analytics.py` | Verify plugin enabled on cameras |
| `audio_bridge.py` | **Preferred** — WebSocket SPL → MQTT (needs root in `.env`) |
| `configure_audio_spl_rules.py` | Optional on-camera MQTT rules (payload needs UI edit) |
