# AOA Occupancy Setup Runbook

Configure Axis Object Analytics (AOA) Person Occupancy on all 6 cameras and route events to Home Assistant via MQTT.

## Prerequisites

- MQTT add-on (Mosquitto) running on HA at `192.168.68.175:1883`
- AOA licence included on all Axis cameras (built-in from firmware 10.x on supported models)
- MQTT credentials: `!secret mqtt_username` / `!secret mqtt_password` (same as Frigate uses)

## MQTT Topic Convention

| Camera | Topic prefix set in camera | AOA event topic (full) |
|---|---|---|
| front | `axis/front` | `axis/front/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active` |
| driveway_wide | `axis/driveway_wide` | `axis/driveway_wide/event/...` |
| driveway_id | `axis/driveway_id` | `axis/driveway_id/event/...` |
| backyard | `axis/backyard` | `axis/backyard/event/...` |
| storage_ext | `axis/storage_ext` | `axis/storage_ext/event/...` |
| storage_int | `axis/storage_int` | `axis/storage_int/event/...` |

The scenario must be named **`PersonOccupancy`** on every camera so the HA sensor config matches without per-camera adjustments.

## Per-Camera Setup Steps

Repeat for each camera. Open the camera web UI at `http://<camera-ip>`.

### Step 1 — Configure MQTT client

1. **System → MQTT → MQTT client**
2. Set **Host**: `192.168.68.175`, **Port**: `1883`
3. Set **Username** / **Password** (same MQTT credentials used by Frigate)
4. Set **Topic prefix**: `axis/<zone_id>` (e.g. `axis/front`)
5. **Save and connect** — verify the client shows "Connected"

### Step 2 — Create AOA scenario

1. **Apps → Object Analytics**
2. Click **+ Add scenario**
3. Choose **Occupancy in area** (or "Presence in area" depending on firmware)
4. **Name the scenario exactly**: `PersonOccupancy`
5. Draw the area: select **Full frame** (or drag corners to cover the entire view)
6. Under **Object classes**: enable **Person**, disable Vehicle / Other
7. Set **Minimum size filter**: small (to catch persons at distance)
8. Save

### Step 3 — Enable MQTT publishing for the scenario

1. In the scenario settings, find **Trigger conditions / MQTT**
2. Enable **Send MQTT message on trigger**
3. Verify the topic shown matches: `axis/<zone_id>/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active`
4. Save

### Step 4 — Verify payload

Use MQTT Explorer (or `mosquitto_sub`) to observe the raw payload:

```bash
mosquitto_sub -h 192.168.68.175 -u <user> -P <pass> -t "axis/front/#" -v
```

Walk in front of the camera. You should see a message on:
`axis/front/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active`

Expected JSON payload:
```json
{"Source": {}, "Analytics": {}, "Key": {"scenario": "PersonOccupancy"}, "Data": {"active": true}}
```

If the `Data` key is lowercase (`data`) or `active` is a string (`"1"`) adjust the `value_template` in
`config/home-assistant/mqtt_binary_sensors/aoa_occupancy.yaml` to match.

## HA Entities Created

After syncing config and restarting HA, you will have:

| Entity ID | Description |
|---|---|
| `binary_sensor.front_aoa_person` | Person present at front entrance |
| `binary_sensor.driveway_wide_aoa_person` | Person in driveway wide view |
| `binary_sensor.driveway_id_aoa_person` | Person at driveway ID point |
| `binary_sensor.backyard_aoa_person` | Person in backyard |
| `binary_sensor.storage_ext_aoa_person` | Person at storage exterior |
| `binary_sensor.storage_int_aoa_person` | Person in storage interior |

## Sync and Restart

```bash
./scripts/sync-config.sh
# Then in HA: Developer Tools → YAML → Reload all YAML
# Or restart HA for a full reload
```
