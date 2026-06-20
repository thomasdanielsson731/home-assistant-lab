# Danielsson Home — Panel Review & Top 30 (2026-06-20)

Orkestrerad enligt [agents/ha-review-panel.md](../agents/ha-review-panel.md). Live state: `python scripts/health-check.py` — **all checks passed**; Insights add-on v0.2.4, Cloudflare URLs i `secrets.yaml`.

**Senaste leveranser (sedan batch 20):** `/health` + CSP på timeline-server, `sensor.insights_server_ok`, offline-varning + desktop-fallback på Analytics/Environment, `verify-insights-ha.ps1` i maintenance, Tester-agent ersätter Youth.

**Öppet i working tree (ej committat):** Insights-hardening + Tester-agent — se [#1](#1).

---

## Executive summary

Dashboardarna är strukturellt mogna efter 20 panel-batchar: sidebar (Hem → Teknik), MQTT-räknare, coalesce-templates och mobil-fallback för Insights. **Analytics/Environment** har fått health-signal och offline-CTA — det var huvudorsaken till “tom iframe”.

Kvarvarande risker är **data** (endast 1 timeline-händelse / 24 h, 0 person/fordon) och **hårdvara** (köks-brandvarnare troligen 2/3 i `detector_count`). Familjevyerna (Anna/Rum) har fortfarande placeholder (Nils rum) och ingen daglig story-länk på Hem. Teknik-vyn bär admin-last som baseline/anomaly och story — bra för Thomas, men bör inte dupliceras rörigt i Hem.

---

## Top 5 (alla perspektiv)

| Prio | Åtgärd | Påverkar | Insats |
|------|--------|----------|--------|
| 1 | Commit + sync Insights reliability-fixar | Drift, Analytics, Environment | S |
| 2 | Utred låg event-volym (0 person/24 h trots live kameror) | Händelser, Säkerhet, data-trust | M |
| 3 | Re-pair köks-HEIMAN → `detector_count` 3/3 | Säkerhet, Hem-chip | S |
| 4 | Händelser-vy: samma `insights_server_ok`-chip + offline-banner som Analytics | Mobil, Händelser iframe | S |
| 5 | Daglig story-länk/chip på **Hem** (inte bara Teknik) | Anna, narrativ | S |

---

## Top 30 — prioriterad backlog

| # | Prio | Åtgärd | Fil / vy | Perspektiv | Insats |
|---|------|--------|----------|------------|--------|
| 1 | **P0** | Commit + `sync-config.ps1` + add-on restart för Insights-hardening | `scripts/timeline_server.py`, `house-*.yaml`, `verify-insights-ha.ps1` | Tester | S |
| 2 | **P0** | Felsök normalizer: varför 0 person/fordon/24 h (Frigate MQTT → timeline?) | `scripts/event_normalizer.py`, add-on loggar | Data, Security | M |
| 3 | **P0** | ZHA re-pair köks-brandvarnare (mål 3/3) | [zigbee-setup.md](runbooks/zigbee-setup.md), `templates/indoor_climate.yaml` | Security, Anna | S |
| 4 | **P1** | `home-events.yaml`: chip `insights_server_ok` + conditional offline-markdown | `dashboards/home-events.yaml` | Tester, UX | S |
| 5 | **P1** | Story-chip på Hem → `!secret story_url` | `dashboards/home-hem.yaml` | Anna, Thomas | S |
| 6 | **P1** | Rensa legacy `sensor.insights_*_24h_2` i HA registry; förenkla coalesce | `templates/insights_display.yaml`, HA UI | Data, Tester | S |
| 7 | **P1** | Verifiera vattensensor `binary_sensor.sonoff_snzb_05p` (ej `unavailable`) | `dashboards/home-security.yaml`, ZHA | Security | S |
| 8 | **P1** | Dokumentera vilka automations som är av medvetet (`initial_state: false`) | `automations/security/*.yaml`, `docs/runbooks/` | Tester, Thomas | S |
| 9 | **P2** | Baseline/anomaly-sammanfattning i Teknik Drift (MQTT eller template från API) | `home-tech.yaml`, `baseline_engine.py` | Data, Thomas | M |
| 10 | **P2** | Kraftringen credentials → `energy_bridge.py` live | `scripts/energy_bridge.py`, P6-6 | Data | M |
| 11 | **P2** | Nils rum: dölj sektion tills lampor finns, eller lägg `light.*` | `dashboards/home-rooms.yaml` | UX, Anna | S |
| 12 | **P2** | Yale Doorman: beslut Sprint 1 — visa eller ta bort dold `ACCESS`-sektion | `dashboards/home-security.yaml` | UX, Security | M |
| 13 | **P2** | Grafana 7d-länk från Environment (Thomas) — sidebar eller chip | `configure_ha_sidebar.py`, `house-graphs.yaml` | Thomas, Visual | S |
| 14 | **P2** | Enhetlig navigation: `/house-timeline` vs `/lovelace/...` audit | alla `home-*.yaml` | Tester | S |
| 15 | **P2** | `insights_counters_offline` push: testa deep link → Teknik Drift | `automations/security/insights_counters_offline.yaml` | Tester | S |
| 16 | **P2** | Hem: tydligare “utomhus aktivitet ≠ vem är hemma” (ADR-006 copy redan delvis) | `home-hem.yaml` | Anna, UX | S |
| 17 | **P2** | Kameror: tap → Frigate review/clip (zon) | `home-cameras.yaml` | Thomas | M |
| 18 | **P2** | `scene_delivery_detection` — enable eller dokumentera varför av | `automations/security/scene_delivery_detection.yaml` | Security | S |
| 19 | **P2** | `aoa_vehicle_alert` — driveway false positives vs nytta | `automations/security/aoa_vehicle_alert.yaml` | Security | S |
| 20 | **P3** | `frigate_person_alert` — selektiv enable (entrén only?) | `automations/frigate_person_alert.yaml` | Thomas, Security | S |
| 21 | **P3** | Stale Double Take / `dt_*` entities i HA registry (post ADR-006) | HA entity registry | Data | S |
| 22 | **P3** | Ta bort `home-lab` panel om den fortfarande syns på host | `configure_ha_sidebar.py` | UX | S |
| 23 | **P3** | Rum: fukt/temp per rum (ej bara brandvarnare-temp) | `home-rooms.yaml`, ZHA/MS100 | Anna | M |
| 24 | **P3** | Environment: kort om “Recorder ≠ Insights metrics” (som Teknik Historik) | `house-graphs.yaml` | Data, UX | S |
| 25 | **P3** | Säkerhet HISTORIK: visa senaste story-beat eller länk | `home-security.yaml` | Anna | S |
| 26 | **P3** | Visual: konsekvent chip-färgschema (grön=OK, amber=varning, röd=offline) | alla dashboards | Visual | S |
| 27 | **P3** | Svensk copy-audit push-notiser (rök, vatten, loitering, counters) | `automations/security/` | UX | S |
| 28 | **P3** | CI: säkerställ `test_insights_ingress.py` + dashboard-tester på varje PR | `.github/workflows/` | Tester | S |
| 29 | **P3** | Ta bort `agents/ha-reviewer-youth.md`; README + panel pekar på Tester | `agents/` | chore | S |
| 30 | **P3** | Panel batch 21: implementera #2–#7, kör pytest + health-check, commit | process | alla | M |

**Insats:** S &lt; 2 h · M halv dag · L hel dag

---

## Per persona (kort)

- **Thomas:** Teknik Live/Drift är demo-värdig; vill ha Grafana + baseline i UI och Frigate deep links. Low event count underminerar Analytics-demo — prioritera #2.
- **Anna:** Hem funkar för vardag (ljus, rök-chip, utomhus). Saknar story på Hem och riktigt Nils-rum. Yale “Kommer snart” skapar förvirring — dölj helt eller leverera.
- **Tester:** S1 om kök-rök 2/3; S2 om Händelser iframe utan offline-CTA; regression suite 260 gröna — commit uncommitted (#1) innan nästa batch. Legacy `_2` entities är teknisk skuld (#6).
- **UX:** Insights offline-banner på Analytics/Environment ✅; Händelser behöver samma (#4). Nils placeholder (#11). ADR-006 copy på utomhusnärvaro ✅.
- **Visual:** Mushroom-sections konsekventa; chip-färger nästan enhetliga — mindre avvikelser i Teknik Historik (#26).
- **Security:** Loitering + smoke push on; multisensor fusion OK. `detector_count` &lt; 3 ska synas amber överallt — verifiera live (#3). Vatten offline-handling finns (#7).
- **Data:** MQTT counters + coalesce ✅. 1 env-event/24 h är misstänkt (#2). Baseline/anomaly finns i timeline UI men inte HA (#9). Energy väntar credentials (#10).

---

## Konflikter mellan personas

| Topic | Thomas vill | Anna vill | Kompromiss |
|-------|-------------|-----------|------------|
| Push-larm person/fordon | På vid entré för demo | Tyst vardag | Behåll av som default; optional entré-only (#20) |
| Teknik synlighet | Allt admin synligt | Enkel familje-IA | Sidebar: Hem–Rum familj, Teknik sista + dold deep link |
| Yale / ACCESS | Integrera lock | Ingen halv-lösning | Dölj tills Sprint 1 (#12) |
| Story / AI | Ollama-summering synlig | Kort svensk dagssummering | Chip på Hem (#5), inte full iframe |
| Event-räknare 0 | Debug pipeline | “Fungerar det?” | Fix #2 + tillfällig fotnot på Händelser om 0 events |

---

## Klart sedan förra panel (referens)

| Item | Status |
|------|--------|
| MQTT Insights counters + `*_display` coalesce | ✅ |
| Loitering via `aoa_bridge.py` | ✅ |
| Analytics/Environment offline-chip + desktop ny flik | ✅ (deployed, commit pending) |
| `verify-insights-ha.ps1` i maintenance | ✅ |
| Ingress 401 → Cloudflare URLs | ✅ |
| Youth → Tester agent | ✅ (fil pending commit) |

---

## Backlog-förslag

Lägg i [backlog.md](backlog.md):

- **P7-25** Panel review 2026-06-20 — Top 30 i detta dokument; batch 21 = #1–#7.
- **P7-26** Event pipeline audit (person/fordon → timeline).
- **P7-27** Händelser parity med Analytics health UI.

Uppdatera [current-focus.md](current-focus.md) med länk till detta dokument som “nästa 30 åtgärder”.

---

## Nästa steg (rekommenderat)

1. Commit working tree (Insights + Tester).
2. Kör batch 21 på #2–#7.
3. `python scripts/health-check.py` + manuell check Händelser/Analytics/Environment på mobil och desktop.
