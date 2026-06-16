# ADR-005: Home Intelligence Timeline (API-first)

**Status:** Accepted  
**Date:** 2026-06-06  
**Context:** Phase 7 — Danielsson Home Intelligence Platform

## Decision

The primary insights UX is **Analytics** — served by `timeline_server.py` on **HAOS** via the Danielsson Insights add-on, embedded in HA via YAML dashboards **`house-timeline`**, **`house-graphs`**, and **`home-events`** (iframe with Cloudflare or LAN URL — not Ingress). Family sidebar panels (Hem, Kameror, …) remain secondary.

**Updated 2026-06-12:** Platform cut over from Windows dev PC bridges to HAOS add-on v0.2.4.

**Updated 2026-06-14:** Face recognition removed — [ADR-006](006-no-face-no-companion-presence.md).

Architecture:

```
Sources (Frigate, Axis, D6210, Yale, HA)
    → event_normalizer.py
    → Event Store (events/, timeline.jsonl, metrics.jsonl)
    → correlation_engine.py (arrival, delivery, bicycle)
    → Timeline API (/api/v1/*)
    → Timeline UI (horizontal time scale, event layers, metrics, occupancy blocks)
```

Home Assistant remains:

- Event and state **hub** for automations and live entity cards
- **One source among many** — not the analytics store or primary timeline UI

## Rationale

| Requirement | Why API-first |
|---|---|
| "What happened?" vs "current state?" | Timeline needs time-range queries, not entity snapshots |
| Multiple sources | Same API regardless of Frigate, Axis, or Yale |
| Occupancy as duration blocks | Needs interval model, not binary_sensor cards |
| Metrics aligned to timeline | Continuous series (`metrics.jsonl`) separate from point events |
| Extensibility | New event types (cat, bicycle, scene metadata) without Lovelace redesign |

## Consequences

- **Do:** Extend `event_normalizer.py` for all MQTT sources; keep Lovelace for operations/security
- **Do:** Version REST API under `/api/v1/`
- **Do:** Store raw + enriched events; correlation writes `parent_event_ids` and `metadata.correlations`
- **Don't:** Build timeline features inside family panel YAML (`home-hem.yaml`, …) — link to Analytics/Händelser instead; Teknik may show summary chips only
- **Don't:** Couple timeline UI to HA entity IDs

## Implementation phases

| Phase | Deliverable |
|---|---|
| 7b | All live sources → events + metrics |
| 7c | Timeline API v1 (events, metrics, occupancy blocks) |
| 7d | Timeline UI v1 (1h / 24h / 7d, click → snapshot) |
| 7e | Correlation engine (`arrival`, `delivery`, `bicycle`, door boost) | ✅ |
| 7f | HA sidebar Analytics dashboard (`house-timeline`) | ✅ |
| 7g | InfluxDB metrics bridge in add-on | ✅ v0.2.4 |

## References

- [event-model.md](../analytics/event-model.md)
- [vision.md](../vision.md)
- `scripts/timeline_server.py`, `scripts/timeline_api.py`
