# Project Backlog

Prioritized work items grouped by time horizon. Effort is T-shirt sized: S (< 2h), M (half-day), L (full day), XL (multiple days).

---

## Now — Foundation and Cleanup

Work that must complete before anything else can start.

| # | Item | Effort | Dependencies | Value |
|---|---|---|---|---|
| N1 | Apply naming conventions to all existing HA entities and areas | M | None | High — prevents cascading renames later |
| N2 | Enable and test automatic backups (Settings → Backups) | S | None | Critical — safety net for all future work |
| N3 | Install and verify Mosquitto MQTT broker | S | None | Blocker for Frigate and Axis MQTT |
| N4 | Mount external 1 TB SSD to `/media/frigate` | S | SSD physical install | Blocker for Frigate recording |
| N5 | Create all Areas and assign all devices | S | N1 (naming) | Required for dashboard and automations |
| N6 | Create Person entities for Thomas, Nils, Hugo | S | None | Presence detection, dashboard |
| N7 | Delete or disable all unavailable/stale entities | S | None | Reduce noise, improve startup time |
| N8 | Install HACS and Mushroom Cards, Frigate Card, mini-graph-card | S | None | Required before building dashboards |
| N9 | Set up `.env` and `sync-config.sh` on dev machine | S | SSH access to HAOS | Enables config-as-code workflow |
| N10 | Take a manual backup after cleanup | S | N1–N7 | Restore point before Frigate install |

---

## Next — Cameras, Frigate, Dashboard

Work that delivers visible value once the foundation is clean.

| # | Item | Effort | Dependencies | Value |
|---|---|---|---|---|
| X1 | Install Frigate add-on and verify it starts | S | N3, N4 | Unblocks all camera work |
| X2 | Add `front` (P3288) to Frigate — dual stream, detect + record | M | X1 | First camera live, validates the pattern |
| X3 | Add remaining 5 cameras to Frigate using same pattern | L | X2 | Full camera coverage |
| X4 | Validate D6210 radar sensor — VAPIX or MQTT integration | M | N3, X3 | Driveway pre-trigger without camera polling |
| X5 | Install Frigate HA integration and verify entities appear | S | X3 | Enables HA automations on detection |
| X6 | Build Security dashboard view — detections, event log | M | X5, N8 | Daily driver for security monitoring |
| X7 | Build Cameras dashboard view — all 6 feeds in zone layout | M | X5, N8 | Main camera overview |
| X8 | Build Home dashboard view — presence, quick status, events | M | N6, X7 | Primary daily-use view |
| X9 | Build Rooms dashboard view — per-room controls | M | N5, N8 | Room control access |
| X10 | Build Operations dashboard view — system health, add-ons | S | X1 | Operational visibility |
| X11 | Person detection automation → push notification with snapshot | M | X5 | First working end-to-end security loop |
| X12 | Configure Frigate recording retention (7-day default) | S | X3 | Prevents SSD from filling up |

---

## Later — Face Recognition

Work that builds the face recognition pipeline once cameras are stable.

| # | Item | Effort | Dependencies | Value |
|---|---|---|---|---|
| L1 | Deploy CompreFace on a separate host or as a HAOS add-on | M | X3 | Recognizer backend |
| L2 | Install Double Take add-on and connect to CompreFace | M | L1 | Middleware layer |
| L3 | Configure Double Take → Frigate webhook on `front` and `driveway_id` | S | L2, X3 | Enables face match events |
| L4 | Collect training images for Thomas, Nils, Hugo | M | L2 | Model accuracy |
| L5 | Train CompreFace on household members | S | L4 | Known-person recognition |
| L6 | Test recognition accuracy at `front` — target >85% confidence | M | L5 | Validate pipeline |
| L7 | Build "unknown person" alert automation (notify + snapshot) | S | L3 | Core security value |
| L8 | Build "known person" welcome automation | S | L5, L7 | Personalised entry experience |
| L9 | Add face recognition status to Security dashboard view | S | L5, X6 | Surface face match results |
| L10 | Retrain model with additional images to reduce false negatives | L | L6 | Ongoing improvement |

---

## Future — Axis Analytics and AI

Experimental and longer-horizon work. Sequence within this group is flexible.

| # | Item | Effort | Dependencies | Value |
|---|---|---|---|---|
| F1 | Audit ACAP apps installed on each Axis camera | S | X3 | Baseline for analytics work |
| F2 | Enable Axis MQTT on cameras — metadata to Mosquitto | M | N3, F1 | Rich event metadata without Frigate |
| F3 | Build HA sensors from Axis MQTT metadata (loitering, vehicle class) | L | F2 | Axis analytics value in HA |
| F4 | Train custom ACAP object model on lab footage (Axis toolchain) | XL | F1, Axis dev access | Custom on-camera detection |
| F5 | Set up Ollama + Qwen stable API on Windows dev machine | S | None | LLM foundation |
| F6 | Connect Ollama to HA Assist pipeline (REST integration) | M | F5 | Natural language automation commands |
| F7 | Vision model (Qwen-VL or LLaVA) receiving Frigate snapshots | L | F5, X5 | Scene understanding |
| F8 | Scene description automation: event → LLM caption → notification | M | F7 | Richer alerts |
| F9 | Establish anomaly detection baseline (time-of-day event frequency) | XL | X12, F2 | Pattern-based alerting |
| F10 | AI agent loop: event → context → LLM decision → HA action | XL | F6, F7, F9 | Autonomous response |
| F11 | Wyoming STT + Piper TTS for local voice interface | M | F6 | Voice control without cloud |

---

## Dropped / On Hold

| Item | Reason |
|---|---|
| Cloud face recognition (AWS Rekognition) | Privacy preference — local-only policy |
| Nabu Casa remote access | Evaluate after local setup is stable |
| ALPR (license plate recognition) | Add only if there is a specific automation need |
