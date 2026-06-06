# Project: Family Context

**Phase:** 4 + 8 · **Status:** Planned

## Goal

Unified answer to "who is home?" and "who just arrived?" — combining phone presence, face recognition, and camera analytics.

## Context Sources

| Source | Signal | Entity |
|---|---|---|
| Phone presence | Home / away | Person entities (Thomas, Nils, Hugo, Anna) |
| Face recognition | Identified at door | `sensor.dt_<name>_confidence` |
| Camera analytics | Person at zone | `binary_sensor.<zone>_aoa_person` |
| Scene metadata | Person count | `sensor.<zone>_scene_persons` |

## Done Criteria

- [ ] Person entities reliably track home/away
- [ ] Face recognition identifies arrivals at `front`
- [ ] Template sensor: `sensor.house_occupancy_summary` (who's home, count)
- [ ] Dashboard card: "Who's home" with last-arrival timestamps
- [ ] (Phase 8) NL query: "Is anyone home?"

## Tasks

| # | Task | Dependencies |
|---|---|---|
| 1 | Verify person entity presence tracking | Phase 1 |
| 2 | Complete face recognition project | Phase 4 |
| 3 | Create occupancy summary template sensor | Phase 5 |
| 4 | Add "Who's home" card to Home dashboard | Phase 3 |
| 5 | Arrival notification automation (face + presence) | Phase 4 |
| 6 | Digital twin state aggregation | Phase 8 |

## References

- [docs/vision.md](../docs/vision.md) — Digital Twin section
- [projects/face-recognition.md](face-recognition.md)
