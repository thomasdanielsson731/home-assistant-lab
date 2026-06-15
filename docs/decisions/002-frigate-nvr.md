---
id: ADR-002
title: Use Frigate as NVR and object detection layer
status: Accepted
date: 2026-05-30
---

# ADR-002 — Use Frigate as NVR and Object Detection Layer

> **Note:** References to Double Take below are historical context only. Face recognition removed — [ADR-006](006-no-face-no-companion-presence.md).

## Context

Object detection for cameras can be handled at multiple layers: on the camera itself (Axis ACAP), in a standalone NVR (Frigate, Scrypted), or via cloud APIs. The choice affects latency, cost, privacy, and integration depth with Home Assistant.

## Decision

Use **Frigate** as the primary NVR and object detection layer for all six Axis cameras.

## Reasons

- **Deep HA integration**: The official Frigate HA integration creates `camera`, `binary_sensor`, and `sensor` entities automatically — zero manual entity configuration.
- **MQTT events**: Frigate publishes structured events to MQTT, making it trivial to build automations on detection.
- **Double Take integration**: Frigate has a native webhook to Double Take for face recognition — the two are designed to work together.
- **Local processing**: All inference runs on the HAOS host. No cloud API calls, no data leaving the network.
- **Recording**: Built-in segmented recording with configurable retention — satisfies NVR requirements without a separate system.

## Tradeoffs Accepted

- Frigate runs on CPU only (no GPU on Dell Latitude 3120) — detection latency is higher and fewer cameras can run at high FPS simultaneously
- Axis ACAP analytics and Frigate detection are parallel systems — events from Axis MQTT and Frigate MQTT will coexist in Phase 5
- Frigate does not use Axis-specific features (ARTPEC on-chip inference) — evaluated in Phase 5

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Axis Object Analytics only | No recording, no Double Take webhook, no HA entity auto-generation |
| Scrypted | Less mature Frigate-equivalent; Double Take integration less established |
| Blue Iris | Windows-only, not viable on HAOS |
| Cloud detection (AWS Rekognition Video) | Privacy tradeoff unacceptable for home cameras |
