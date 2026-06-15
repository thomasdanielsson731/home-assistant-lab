---
id: ADR-001
title: Use Home Assistant OS (HAOS) as the platform
status: Accepted
date: 2026-05-30
---

# ADR-001 — Use Home Assistant OS (HAOS)

> **Note:** Double Take and CompreFace references below are historical. Face recognition removed — [ADR-006](006-no-face-no-companion-presence.md).

## Context

Home Assistant can be deployed in four modes: HAOS, Supervised, Container, or Core. The choice affects add-on support, update management, and operational complexity.

## Decision

Use **Home Assistant OS** on the Dell Latitude 3120.

## Reasons

- **Add-on ecosystem**: HAOS is the only mode with full, officially supported add-on management (Supervisor). Frigate, Mosquitto, and Danielsson Insights run as HAOS add-ons — no Docker compose management required.
- **Update management**: One-click OS + HA + add-on updates. Lower operational overhead for a solo-managed lab.
- **Hardware support**: HAOS generic x86-64 image runs well on the Latitude 3120; no driver conflicts.
- **Recovery**: HAOS supports snapshot backups and restore that cover the full system state.

## Tradeoffs Accepted

- Less flexibility than Container mode for running arbitrary workloads alongside HA
- Ollama/Qwen runs on the **Windows dev machine**, not on the HAOS host — acceptable given the workstation has more resources

## Alternatives Considered

| Mode | Reason rejected |
|---|---|
| HA Container | No Supervisor, add-ons not available — would require manual Docker compose for all services |
| HA Supervised | Supported but fragile; any Docker change outside HA can break Supervisor |
| HA Core | Python virtualenv only — no add-ons, maximum complexity |
