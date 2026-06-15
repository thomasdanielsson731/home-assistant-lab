---
id: ADR-006
title: Drop face recognition and family Companion presence
status: Accepted
date: 2026-06-14
supersedes: ADR-003
---

# ADR-006 — Drop Face Recognition and Family Companion Presence

## Context

Phase 4 (Double Take + CodeProject.AI) was in progress but household accuracy and privacy expectations did not justify continued investment. The rest of the family also declined Home Assistant Companion app installs — phone-based `person.*` tracking is not available for Nils, Hugo, or Anna.

Thomas may keep the Companion app **only** for security push notifications (`notify.mobile_app_thomas_iphone_15`), not for household occupancy.

## Decision

1. **Remove face recognition** from scope, config, event pipeline, and documentation:
   - Double Take add-on uninstalled on HAOS (2026-06-15); do not sync `config/double-take/`
   - Remove CodeProject.AI / CompreFace runbooks and dev PC dependency
   - Remove `dt_*` entities, presence fusion, and Double Take MQTT handling in `event_normalizer.py`

2. **Remove family Companion presence** from product UX:
   - No "who is home" dashboard based on `person.*` or fused presence
   - Outdoor situational awareness uses camera analytics (`binary_sensor.house_outdoor_presence`, AOA, scene) instead

3. **Supersede [ADR-003](003-face-recognizer.md)** — face recognition is out of scope, not deferred.

## Consequences

- Arrival correlation uses camera + door events only; no identity attachment from face matches
- Phase 4 removed from active roadmap; phases renumbered in docs (Axis analytics remains Phase 5, etc.)
- Reduced HA load: Double Take add-on stopped; sync scripts no longer deploy DT config
- Digital twin "who is home?" deferred until a non-phone signal exists (e.g. explicit user input or reliable camera-only inference)

## Alternatives considered

| Option | Rejected because |
|---|---|
| CompreFace on dedicated host | Same accuracy/privacy concerns; extra infra |
| Companion for Thomas only | Does not answer "who is home" for household |
| Keep DT for unknown-person alerts only | Still requires face pipeline; user chose full removal |
