# AXIS Audio Analytics SPL → Home Assistant

## Status on this lab

Audio Analytics runs as a **firmware plugin** (`audioanalytics.cgi`), not a separate ACAP in the applications list.

Verified on:

| Zone | Camera | IP | SoundPressureLevel |
|---|---|---|---|
| `front` | P3288-LVE | 192.168.68.200 | ✅ enabled |
| `driveway_wide` | Q3558-LVE | 192.168.68.201 | ✅ enabled |
| `backyard` | Q1656-LE | 192.168.68.203 | ✅ enabled |

Check from dev PC:

```powershell
python scripts/configure_audio_analytics.py
```

## Why SPL is not in HA yet

SPL **Summary** events (MaxSPL / MinSPL every ~60 s) are *application data*. They are **not** exposed via:

- `analytics-mqtt` data sources (scene metadata only)
- Standard MQTT event filters (`configureEventPublication`)

## Automated setup (preferred)

```powershell
python scripts/configure_audio_analytics.py   # verify plugin
python scripts/configure_audio_spl_rules.py   # create MQTT action + rule
```

The script creates the action rule on each camera. **Then edit the MQTT payload once per camera in the web UI** (System → Events → Actions → `ha_spl_mqtt_<zone>`) — SOAP cannot set SPL event modifiers reliably (`#MaxSPL` collides with `#M` MAC modifier).

Payload in UI:

```json
{"max_spl":#MaxSPL,"min_spl":#MinSPL,"spl":#MaxSPL}
```

(Unquoted modifiers in the UI field.)

## Manual setup per camera (web UI)

On each camera with Audio Analytics:

1. **System → Events → Rules → Add rule**
2. **Condition:** Audio analytics → Sound pressure level → **Summary**
3. **Action:** Send MQTT publish message
4. **Topic:** `axis/<zone_id>/audio/spl`  
   - front → `axis/front/audio/spl`  
   - driveway_wide → `axis/driveway_wide/audio/spl`  
   - backyard → `axis/backyard/audio/spl`
5. **Payload (JSON):** `{"max_spl":#MaxSPL,"min_spl":#MinSPL,"spl":#MaxSPL}`  
   Use **unquoted** modifiers (no `"#MaxSPL"` — `#M` is parsed as MAC address modifier).
6. **QoS:** 0 · **Retained:** Yes
7. Ensure MQTT client is connected (same broker as `configure_cameras.py`)

## Verify MQTT

```powershell
python scripts/mqtt-probe.py   # extend topics if needed
```

Or subscribe:

```
axis/+/audio/spl
```

Expected every ~60 s per camera.

## HA entities

Defined in `mqtt_sensors/audio_analytics.yaml`:

- `sensor.front_audio_spl`
- `sensor.driveway_wide_audio_spl`
- `sensor.backyard_audio_spl`

After MQTT flows: **Developer Tools → MQTT → Reload** or restart HA.

## Dashboard

**Insights → AUDIO ANALYTICS (SPL)** — live values + 7-day history graph.

## Scripts

| Script | Purpose |
|---|---|
| `configure_audio_analytics.py` | Verify plugin enabled on cameras |
| `configure_audio_spl_rules.py` | Create MQTT action rules via VAPIX SOAP (preferred) |
| `get_event_instances.py` | List SPL event topics on camera |
