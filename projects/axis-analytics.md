# Project: Axis Analytics

**Phase:** 5 · **Status:** In progress

## Goal

All Axis camera analytics (AOA, scene metadata, D6210 air quality) verified live in Home Assistant via MQTT.

## Done Criteria

- [x] MQTT messages confirmed for all 6 cameras (AOA person)
- [x] Scene frame sensors live on front, driveway_wide, driveway_id, backyard
- [x] D6210 air quality: 8 sensors with live values in HA
- [x] Audio SPL on front, driveway_wide, backyard
- [x] Analytics visible in Security and Operations dashboard views
- [ ] Loitering scenarios created on 3 driveway/front cameras (manual camera UI)
- [ ] Stable for 1 week without manual intervention

## Tasks

| # | Task | Status |
|---|---|---|
| 1 | Sync config to HAOS | ✅ |
| 2 | Run `configure_cameras.py` | ✅ all 6 cameras MQTT+AOA OK |
| 3 | Start `air_quality_bridge.py` (schedule via Task Scheduler) | ✅ running; schedule for 24/7 |
| 4 | Verify MQTT with `mosquitto_sub` per camera | ✅ |
| 5 | Manual Loitering scenarios (web UI) | ⬜ |
| 6 | Enable scene/frame MQTT on front + driveway cameras | ✅ |
| 7 | Add dashboard cards for analytics sensors | ✅ |
| 8 | `aoa_bridge.py` + `audio_bridge.py` on dev PC | ✅ |

## Key Files

- `scripts/configure_cameras.py`
- `scripts/air_quality_bridge.py`
- `config/home-assistant/mqtt_binary_sensors/aoa_*.yaml`
- `config/home-assistant/mqtt_binary_sensors/scene_presence.yaml`
- `config/home-assistant/mqtt_sensors/scene_metadata.yaml`
- `config/home-assistant/mqtt_sensors/air_quality.yaml`

## References

- [integrations/axis-analytics/README.md](../integrations/axis-analytics/README.md)
- [docs/runbooks/aoa-setup.md](../docs/runbooks/aoa-setup.md)
- [docs/runbooks/d6210-setup.md](../docs/runbooks/d6210-setup.md)
