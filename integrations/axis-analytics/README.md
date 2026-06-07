# Axis Analytics Integration

Axis camera analytics flowing into Home Assistant via MQTT. Core of Phase 5.

## Data Streams

| Stream | Cameras | MQTT topic | HA entities |
|---|---|---|---|
| AOA Person Occupancy | All 6 | `axis/<zone>/event/.../PersonOccupancy/Active` | `binary_sensor.<zone>_aoa_person` |
| AOA Vehicle | front, driveway_wide, driveway_id | `axis/<zone>/event/.../VehicleOcc/Active` | `binary_sensor.<zone>_aoa_vehicle` |
| AOA Loitering | front, driveway_wide, driveway_id | `axis/<zone>/event/.../Loitering/Active` | `binary_sensor.<zone>_aoa_loitering` |
| Scene frame | all 6 | `axis/<zone>/scene/frame` | presence + person/vehicle counts |
| Scene track | optional | `axis/<zone>/scene/track` | used by `event_normalizer` behavior classification |
| Scene snapshot | All with scene analytics | `axis/<zone>/scene/snapshot` | `image.<zone>_latest_detection` |

## Setup

1. Run `python scripts/configure_cameras.py` — configures MQTT client + AOA scenarios
2. Manually create Loitering scenarios in camera web UI (script can't do this)
3. Enable scene/frame MQTT publishing in camera Apps settings
4. Sync config: `.\scripts\sync-config.ps1`
5. Verify with `mosquitto_sub -t "axis/#" -v`

Runbook: [docs/runbooks/aoa-setup.md](../../docs/runbooks/aoa-setup.md)

## AOA vs Frigate

| | Frigate | AOA |
|---|---|---|
| Latency | Higher (server-side ML) | Lower (on-camera) |
| Objects | person, car (generic) | person, vehicle (Axis classes) |
| Recording | Yes | No |
| Loitering | No | Yes (manual scenario) |
| Scene metadata | Bounding boxes only | Rich JSON (type, score, track) |

Both coexist. Use AOA for fast presence triggers; Frigate for recording and snapshots.

## Future: Custom ACAP Models

ARTPEC-8 cameras (Q3558-LVE, Q1656) support on-chip inference. Potential custom models:

- Package detection at `front`
- Specific vehicle types at `driveway_wide`
- Custom object classes trained on lab footage

Requires AXIS ACAP SDK and deployment via AXIS Device Manager.

## Config Files

```
config/home-assistant/
  mqtt_binary_sensors/
    aoa_occupancy.yaml
    aoa_vehicle.yaml
    aoa_loitering.yaml
    scene_presence.yaml
  mqtt_sensors/
    scene_metadata.yaml
  mqtt_images/
    scene_snapshots.yaml
```
