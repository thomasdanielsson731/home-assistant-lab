# D6210 Radar Integration Runbook

Integrate the Axis D6210 radar (connected to M2036 via I/O port) into Home Assistant via MQTT.

## Hardware connection

The D6210 is wired to the M2036's digital I/O port. When the radar detects motion/presence,
it asserts the M2036 input, which triggers an M2036 firmware event.

## Option A — M2036 I/O event → MQTT rule (simplest)

Configure the M2036 to publish an MQTT message when its digital input changes state.

1. Open M2036 web UI at `http://<driveway_id_camera_ip>`
2. **System → Events → Add rule**
3. Trigger: **Digital Input** → Input 1 → Active
4. Action: **Send MQTT message**
   - Topic: `axis/driveway_env/radar/motion`
   - Payload: `1`
5. Add a second rule for the deactivation:
   - Trigger: Digital Input → Input 1 → Inactive
   - Payload: `0`
6. Verify MQTT client is connected (System → MQTT should show "Connected")

HA entity: `binary_sensor.driveway_env_radar_motion` (device_class: motion)

## Option B — AOA Virtual Input / ACAP event

If the D6210 exposes itself as a virtual I/O source in AOA or via ACAP:

1. In M2036 AOA, the radar may appear as an external trigger source
2. Configure an AOA scenario triggered by the radar input
3. The MQTT topic will be: `axis/driveway_env/event/IOPort/VirtualInput/Active`
4. Payload: `{"Data": {"active": true}}`

HA entity: `binary_sensor.driveway_env_radar_presence` (device_class: presence)

## Which entity to use

Start with **Option A** (simpler, pure firmware rules). Once working:
- Use `binary_sensor.driveway_env_radar_motion` as a **pre-trigger** for driveway cameras
- Combine with Frigate: radar motion → start Frigate recording before the car reaches the ID camera
- Reduces false negatives from Frigate's frame-based detection at low FPS

## Automation example (add to automations/security/)

```yaml
- id: "radar_driveway_pretrigger"
  alias: "Radar — driveway pre-trigger"
  trigger:
    - platform: state
      entity_id: binary_sensor.driveway_env_radar_motion
      to: "on"
  action:
    - service: camera.record
      target:
        entity_id: camera.driveway_id
      data:
        duration: 30
        lookback: 5
```

## Verify

```bash
mosquitto_sub -h 192.168.68.175 -u frigate -P <mqtt_pass> -t "axis/driveway_env/#" -v
```
Drive a car past the radar and confirm messages appear.
