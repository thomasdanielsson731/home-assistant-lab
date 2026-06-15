# Scope

Explicit boundaries for the Home Assistant Lab / Data Insights Lab. When in doubt, check here before starting new work.

---

## Project Identity

| | |
|---|---|
| **Name** | Home Assistant Lab (repo) / **Danielsson Home Intelligence Platform** (product) |
| **Primary purpose** | Event-driven situational awareness — *what happened*, not just current state |
| **Primary UX** | **Analytics** — HA sidebar **Analytics** or `http://192.168.68.175:8765/timeline` (HAOS add-on) — [ADR-005](decisions/005-home-intelligence-timeline.md) |
| **Secondary UX** | HA `home-lab` dashboard — operations, security, live entity cards |
| **Not** | A replacement for HomeKit lighting and blind automation |

---

## In Scope

### Platform

- Home Assistant OS on Dell Latitude 3120
- Config-as-code via this Git repo + `sync-config` scripts
- Mosquitto MQTT as the internal event bus
- Automatic backups and documented restore procedure

### Data Sources

| Source | Zone / domain | Integration |
|---|---|---|
| 6× Axis cameras | `front`, `driveway_*`, `backyard`, `storage_*` | Frigate RTSP + Axis MQTT |
| D6210 air quality | `driveway_env` | `air_quality_bridge.py` → MQTT |
| HA device sensors | Rooms, energy, weather | Native HA integrations |
| Person presence | Outdoor activity only | Camera analytics (AOA, scene, Frigate) — not phone/face |
| Frigate detections | All camera zones | MQTT + HA integration |

### Analytics and Vision

- Frigate object detection (person, car)
- Axis Object Analytics (person occupancy, vehicle, loitering)
- Scene frame/track metadata (person/vehicle counts, snapshots)
- Future: local LLM scene descriptions, anomaly detection

### Storage and Insights

- Event store (`events/timeline.jsonl`, `metrics.jsonl`) — **live**
- Correlation engine (`arrival`, `delivery`, `bicycle`) — **live**
- InfluxDB metrics retention — **live** in Danielsson Insights add-on v0.2.4+
- Grafana / baselines — **7-day dashboard live** (HA sidebar → Grafana)
- Digital twin state model — Phase 8

### Development Tooling

- VS Code + Cursor for config authoring
- Claude Code / Cursor agents (`agents/`) for structured assistance
- Ollama + Qwen on Windows dev machine for LLM experiments
- Runbooks, ADRs, and `current-focus.md` for operational context

---

## Out of Scope

| Item | Reason | Alternative |
|---|---|---|
| Lamp/blind automation | HomeKit already works well | Use HA only for security/presence context |
| Cloud AI for security data | Privacy policy — local only | Ollama (local LLM experiments) |
| Face recognition / Double Take | Removed — [ADR-006](decisions/006-no-face-no-companion-presence.md) | Camera analytics + correlation |
| Family Companion app presence | Household declined HA app | Outdoor analytics; Thomas push for alerts only |
| ALPR (license plates) | No current automation need | Add if a specific use case appears |
| Nabu Casa remote access | Evaluate later | VPN or Tailscale if needed |
| Multi-home / multi-tenant | Single property lab | N/A |
| 3D visualisation of the house | Digital twin is a state model, not geometry | HA dashboard + Grafana |

---

## Phase Gate Rules

1. **Do not start Phase N+1** until Phase N has been stable for two weeks
2. **Every HA config change** must be committed to this repo before considering it done
3. **New integrations** must not break existing automations
4. **Secrets** never committed — documented shape only in `secrets.yaml.example`
5. **Documentation updates** are part of the deliverable, not optional

---

## Success Criteria (Overall)

The lab is "working" when:

- [ ] All Phase 5 MQTT pipelines verified end-to-end (AOA, scene, air quality)
- [ ] Outdoor activity and correlation events reliable at entry zones
- [ ] At least one insight dashboard shows a trend (not just live state)
- [ ] Time-series data retained for 30+ days
- [ ] An AI assistant can answer "what happened today?" from stored events
- [ ] All decisions recorded in ADRs; all operations in runbooks

---

## Related Documents

- [vision.md](vision.md) — long-term direction
- [roadmap.md](roadmap.md) — phase tasks and status
- [backlog.md](backlog.md) — prioritized work queue
