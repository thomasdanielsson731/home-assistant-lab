# Project: Outdoor Activity Context

**Phase:** 5 + 8 · **Status:** Partial (camera analytics live)

Formerly `family-context.md` — renamed 2026-06-14 when face recognition and family Companion presence were removed ([ADR-006](../docs/decisions/006-no-face-no-companion-presence.md)).

## Goal

Situational awareness for outdoor and entry activity — **not** named household presence. Answers "is there activity outside?" and supports arrival/delivery correlation from cameras and door events.

## Context Sources

| Source | Signal | Entity |
|---|---|---|
| Outdoor analytics | Person/vehicle at entry zones | `binary_sensor.house_outdoor_presence` |
| Zone counts | Active entry detections | `sensor.house_outdoor_activity_summary` |
| AOA | Person at zone | `binary_sensor.<zone>_aoa_person` |
| Scene metadata | Person/vehicle counts | `sensor.<zone>_scene_persons`, `*_scene_vehicles` |
| Frigate | Person/vehicle detection | `binary_sensor.<zone>_person_occupancy` |
| Door lock | Arrival/delivery boost | Yale (when integrated) |

**Out of scope:** Companion app presence, face recognition (`dt_*`), `sensor.house_occupancy_summary`.

## Config

- Templates: `config/home-assistant/templates/house_context.yaml`
- Dashboard: outdoor chip in `config/home-assistant/dashboards/home-hem.yaml`

## Done Criteria

- [x] Outdoor presence template from camera analytics
- [x] Outdoor activity summary sensor
- [x] Arrival/delivery correlation from cameras + door (no identity)
- [ ] Yale lock events in timeline
- [ ] (Phase 8) NL query: "what happened at the front today?"

## References

- [docs/vision.md](../docs/vision.md) — Digital Twin section
- [ADR-006](../docs/decisions/006-no-face-no-companion-presence.md)
