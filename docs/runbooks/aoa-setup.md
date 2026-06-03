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

## Loitering Scenarios (Manual — Cannot Be Scripted)

The `loitering` AOA scenario type is not supported via VAPIX API in current firmware (12.x). Configure manually in each camera's web UI.

**Cameras needing loitering:** `front`, `driveway_wide`, `driveway_id`

**Steps per camera:**

1. Open camera web UI at `http://<camera-ip>`
2. Go to **Apps → Object Analytics**
3. Click **+ Add scenario**
4. Choose **Object in area** (NOT "Occupancy" — loitering needs a dwell-time threshold)
5. Name the scenario **exactly**: `Loitering` (case-sensitive — must match HA sensor config)
6. Draw the detection area to cover the relevant zone
7. Under **Object classes**: enable **Person**, disable Vehicle / Other
8. Set **Minimum time in area**: `10 s` (adjust to reduce false positives)
9. Under **Trigger conditions**: enable **Send MQTT message**
10. Verify MQTT topic shown: `axis/<zone_id>/event/ObjectAnalytics/ScenarioLoitering/Loitering/Active`
11. Save

**Verify:**
```bash
mosquitto_sub -h 192.168.68.175 -u frigate -P <pass> -t "axis/front/event/#" -v
```
Stand in front of the camera for >10 s — expect a message on `.../Loitering/Active` with `{"Data": {"active": true}}`.

**HA entities** (already configured in `mqtt_binary_sensors/aoa_loitering.yaml`):

| Entity | Camera |
|---|---|
| `binary_sensor.front_aoa_loitering` | front |
| `binary_sensor.driveway_wide_aoa_loitering` | driveway_wide |
| `binary_sensor.driveway_id_aoa_loitering` | driveway_id |

## Sync and Restart

```bash
./scripts/sync-config.sh
# Then in HA: Developer Tools → YAML → Reload all YAML
# Or restart HA for a full reload
```

## Scene Frame Metadata (Phase 5 extension)

In addition to AOA binary events, cameras can publish rich frame metadata via the `com.axis.scene.frame.v1` analytics MQTT API. This enables per-frame person/vehicle counts and snapshot images in HA.

**Topics:**
```
axis/<zone_id>/scene/frame     # JSON with detections array (~5 fps when objects present)
axis/<zone_id>/scene/snapshot  # JPEG binary of latest detected object
```

**Enable on camera:**
1. In the camera web UI: **Apps → Object Analytics → [scenario] → Advanced**
2. Enable **MQTT frame publishing** (exact label varies by firmware)
3. Verify by subscribing:
   ```bash
   mosquitto_sub -h 192.168.68.175 -u <user> -P <pass> -t "axis/front/scene/#" -v
   ```
4. Walk in front of the camera — expect messages on `axis/front/scene/frame` with payload:
   ```json
   {"channel_id": 1, "timestamp": "...", "detections": [
     {"bounding_box": {...}, "object_track_id": "uuid", "type": "Human", "score": 0.95}
   ]}
   ```

**HA entities created** (from `mqtt_sensors/scene_metadata.yaml` and `mqtt_binary_sensors/scene_presence.yaml`):

| Entity | Description |
|---|---|
| `binary_sensor.front_scene_object_present` | Any object at front (expires 10 s) |
| `sensor.front_scene_persons` | Person count at front |
| `sensor.front_scene_vehicles` | Vehicle count at front |
| `image.front_latest_detection` | Latest snapshot JPEG |
