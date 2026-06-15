---
id: ADR-003
title: Use CodeProject.AI as face recognizer backend
status: Superseded
date: 2026-06-06
superseded_by: ADR-006
---

# ADR-003 — Use CodeProject.AI as Face Recognizer Backend

> **Superseded by [ADR-006](006-no-face-no-companion-presence.md)** — face recognition removed from scope 2026-06-14.

## Context

Phase 4 requires a face recognizer behind Double Take. Two options were evaluated:

| Option | Hosting | Setup complexity | Accuracy | Availability |
|---|---|---|---|---|
| CodeProject.AI | Windows native service | Low — installer, no Docker | Medium–High | Only when dev PC is on |
| CompreFace | Docker (requires VT-x) | High — BIOS, Docker Desktop, compose | High | Separate always-on host needed |

Double Take is already configured in `config/double-take/config.yml` pointing to the dev PC (`DEV_PC_HOST`, currently `http://192.168.68.136:32168`).

## Decision

Use **CodeProject.AI** as the Phase 4 face recognizer, running on the Windows development machine.

## Reasons

- **Already configured** — Double Take `detectors.codeproject.url` points to the dev PC
- **No Docker dependency** — avoids VT-x BIOS change and Docker Desktop overhead
- **Fastest path to working recognition** — install, enable Face module, upload training photos
- **Good enough for household context** — four known persons, controlled lighting at `front`
- **Reversible** — can migrate to CompreFace later if accuracy is insufficient (ADR supersession)

## Tradeoffs Accepted

- Recognition only works when the Windows dev PC is powered on and CodeProject.AI is running
- Slightly lower accuracy than CompreFace for edge cases (angles, occlusion)
- Not suitable for unattended 24/7 production without moving to an always-on host

## Migration Path (if needed)

If recognition accuracy falls below target (>85% at `front`):

1. Enable Intel VT-x in BIOS
2. Deploy CompreFace via `docker/compreface/docker-compose.yml`
3. Update `config/double-take/config.yml` detector URL
4. Retrain with existing Double Take image library

## Next Steps

1. Install CodeProject.AI on Windows PC — `.\scripts\install-codeproject-ai.ps1`
2. Enable the Face Recognition module in CodeProject.AI dashboard
3. Restart Double Take add-on on HAOS
4. Upload training photos for Thomas, Nils, Hugo, Anna via Double Take UI (`http://192.168.68.175:3000`)
5. Verify `sensor.dt_<name>_confidence` entities appear in HA

## Alternatives Considered

| Alternative | Reason not chosen (for now) |
|---|---|
| CompreFace on Docker | Higher setup cost; deferred until accuracy proves insufficient |
| DeepStack | Less maintained; CodeProject.AI is more Windows-friendly |
| Cloud APIs | Privacy policy — local only |
