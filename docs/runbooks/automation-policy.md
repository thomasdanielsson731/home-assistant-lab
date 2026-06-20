# Automation policy — Danielsson Home

Which automations are **on by default**, which are **off**, and why.  
Edit `initial_state` in YAML or toggle in HA UI (Settings → Automations).

## Always on (safety + ops)

| Automation | File | Why |
|---|---|---|
| Smoke alert | `smoke_alert.yaml` | RÖKALARM → push + timeline |
| Water leak | `water_leak_alert.yaml` | Vattensensor diskmaskin |
| Loitering alert | `aoa_loitering_alert.yaml` | AOA loitering → push |
| Sensor offline | `sensor_offline_alert.yaml` | Rök/vatten offline varning |
| Insights counters offline | `insights_counters_offline.yaml` | MQTT räknare stale → push → Teknik Drift |
| Person at entry (multisensor) | `smart_notifications.yaml` | Frigate + AOA/scene 2-of-3 |

## Off by default (noise / pending)

| Automation | File | Enable when |
|---|---|---|
| Frigate person (simple) | `frigate_person_alert.yaml` | Superseded by multisensor — keep off |
| AOA person present | `aoa_person_present.yaml` | Too noisy without multisensor gate |
| AOA vehicle | `aoa_vehicle_alert.yaml` | Driveway false positives — enable for demo only |
| Scene delivery | `scene_delivery_detection.yaml` | Enable after tuning dwell thresholds |
| Scene crowd | `scene_delivery_detection.yaml` | Same file — off |
| Cat detected | `smart_notifications.yaml` | After reliable cat model |
| Cat / legacy Frigate push | `frigate_person_alert.yaml` | Use multisensor instead |

## Push target

All alerts use `notify.mobile_app_thomas_iphone_15` (Thomas iPhone).  
Deep links: Händelser `/lovelace/home-events/events`, Säkerhet `/lovelace/home-security/security`, Drift `/lovelace/home-tech/ops`.

## Manual hardware (not automations)

| Item | Action |
|---|---|
| Kitchen smoke 2/3 | ZHA re-pair — [zigbee-setup.md](zigbee-setup.md) |
| Water sensor unavailable | Re-pair SNZB-05P |
| Kraftringen energy | Credentials → `energy_bridge.py` |

See [ADR-006](../decisions/006-no-face-no-companion-presence.md) — no Companion presence, no face recognition automations.
