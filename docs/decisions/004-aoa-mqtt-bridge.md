---
id: ADR-004
title: Poll AOA occupancy via Python bridge when MQTT events unavailable
status: Accepted
date: 2026-06-06
---

# ADR-004 — AOA Occupancy MQTT Bridge

## Context

Phase 5 AOA binary sensors were `unavailable` in HA despite:
- MQTT client connected on all cameras
- AOA scenarios (PersonOccupancy, VehicleOcc) configured
- `eventFilterList` set via `getEventPublicationConfig`

Investigation showed:
- `setEventPublicationConfig` removed in firmware 12.11.37
- `configureEventPublication` succeeds but does not publish without per-scenario UI "Add condition"
- `sendAlarmEvent` does not produce MQTT messages with current config
- `getOccupancy` API works reliably on all cameras

## Decision

Run `scripts/aoa_bridge.py` on the **Danielsson Insights add-on** (HAOS). Poll `getOccupancy` every 5 s and publish retained MQTT messages to the topics HA sensors already expect.

**Legacy:** previously ran on Windows dev PC via `start-bridges.ps1`.

## Reasons

- Same proven pattern as `air_quality_bridge.py`
- No manual per-camera MQTT UI steps (6 cameras × 2 scenarios)
- Sub-10 s latency acceptable for presence context
- Reversible if native MQTT events are configured later

## Tradeoffs

- Requires HAOS add-on running (same as air quality bridge and timeline server)
- 5 s poll interval per camera — not event-driven
- Loitering still requires manual camera UI setup

## Implementation

- Bridge: `scripts/aoa_bridge.py`
- Scheduled: `HomeLab-AOABridge` via `install-scheduled-tasks.ps1`
- `configure_cameras.py` updated to use `configureEventPublication` (API 1.2)
