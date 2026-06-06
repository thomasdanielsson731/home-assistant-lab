# Project Backlog

Prioritized work items. Effort: S (< 2h), M (half-day), L (full day), XL (multiple days).

Vision: [vision.md](vision.md) · Active phase: **5 (Axis Analytics)** + **4 (Face Recognition)**

---

## Now — Phase 5 Verification

Complete the Axis analytics pipeline end-to-end.

| # | Item | Effort | Status |
|---|---|---|---|
| P5-1 | Commit + sync pending config changes | S | ✅ |
| P5-2 | Start `air_quality_bridge.py`, verify `sensor.driveway_env_*` | S | ✅ MQTT OK, HA reload needed |
| P5-3 | Run `configure_cameras.py` — MQTT + AOA on all cameras | M | ✅ |
| P5-4 | Verify scene/frame on `front` via MQTT subscribe | S | ✅ |
| P5-5 | AOA via `aoa_bridge.py` — poll getOccupancy → MQTT | M | ✅ |
| P5-6 | Create Loitering scenarios manually (3 cameras) | M | ⬜ |
| P5-7 | Add analytics cards to Security + Operations dashboard views | M | ✅ |
| P5-8 | House context template sensors | S | ✅ |
| P5-8 | Update stale docs (d6210 runbook ✅, backlog ✅, README ✅) | S | ✅ |

---

## Next — Phase 4 Face Recognition

CodeProject.AI path — see [ADR-003](decisions/003-face-recognizer.md).

| # | Item | Effort | Dependencies |
|---|---|---|---|
| P4-1 | Install CodeProject.AI on Windows dev PC | S | None |
| P4-2 | Enable Face Recognition module, verify `:32168` | S | P4-1 |
| P4-3 | Restart Double Take, confirm detector connection | S | P4-2 |
| P4-4 | Upload training photos (Thomas, Nils, Hugo, Anna) | M | P4-3 |
| P4-5 | Test recognition at `front` — target >85% | M | P4-4 |
| P4-6 | Unknown person alert automation | S | P4-3 |
| P4-7 | Add face match status to Security dashboard | S | P4-5 |

---

## Later — Phase 6 AI + Phase 7 Data Platform

| # | Item | Effort | Dependencies |
|---|---|---|---|
| L1 | Ollama + Qwen stable API on dev PC | S | None |
| L2 | InfluxDB add-on or external instance | M | None |
| L3 | HA → InfluxDB for energy + env + detection metrics | M | L2, P5-2 |
| L4 | HA Assist → Ollama REST integration | M | L1 |
| L5 | Vision model on Frigate snapshots | L | L1, Phase 2 |
| L6 | Scene description automation | M | L5 |
| L7 | Event rate baselines (zone × hour × object) | L | L3 |
| L8 | Grafana dashboard or HA history trends | M | L3 |
| L9 | Custom ACAP model on lab footage | XL | P5-8, Axis dev access |

---

## Future — Phase 8 Digital Twin

| # | Item | Effort | Dependencies |
|---|---|---|---|
| F1 | House state template sensor (who, env, activity) | M | P5, P4 |
| F2 | NL query over stored events (LLM + context) | L | L1, L3 |
| F3 | Weekly insight report (agent-generated) | M | F1, L7 |
| F4 | Wyoming STT/TTS for local voice (optional) | M | L4 |

---

## Completed (archive)

<details>
<summary>Foundation, Frigate, Dashboard (Phases 1–3)</summary>

| # | Item | Status |
|---|---|---|
| — | HAOS, SSH, MQTT, backups, naming, areas | ✅ |
| — | 6 cameras in Frigate, 99 HA entities | ✅ |
| — | 5 dashboard views at `/lovelace/home-lab` | ✅ |
| — | Person detection → push notification | ✅ |
| F2 | Axis MQTT config via `configure_cameras.py` | ✅ |
| F3 | HA sensors from Axis MQTT metadata | ✅ |

</details>

---

## Dropped / On Hold

| Item | Reason |
|---|---|
| Cloud face recognition | Local-only privacy policy |
| Nabu Casa remote access | Evaluate after local setup stable |
| ALPR | No current automation need |
| HA REST sensors for D6210 | Replaced by MQTT bridge — simpler, already working |
