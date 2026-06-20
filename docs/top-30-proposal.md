# Danielsson Home — Panel Review & Top 30 (2026-06-20)

Orkestrerad enligt [agents/ha-review-panel.md](../agents/ha-review-panel.md).  
**Batch 21 implementerad 2026-06-20** — se statuskolumn nedan.

---

## Executive summary

Dashboardarna är strukturellt mogna. Batch 21 levererade Händelser health-parity, story på Hem/Säkerhet, AOA→person i normalizer, anomaliräknare i Teknik Drift, Frigate-länkar på Kameror, samt automation-policy runbook.

**Kvar manuellt:** köks-brandvarnare 3/3 (ZHA), ev. vattensensor re-pair, Kraftringen credentials, Grafana URL i host `secrets.yaml`, rensa stale entities via `scripts/cleanup_stale_entities.py`.

---

## Top 5 (alla perspektiv)

| Prio | Åtgärd | Status |
|------|--------|--------|
| 1 | Commit + sync Insights reliability | ✅ `09ae691` |
| 2 | Event pipeline audit | ✅ diagnose script + AOA person + health-check |
| 3 | Re-pair köks-HEIMAN | ⬜ manuell ZHA |
| 4 | Händelser insights_server_ok + offline | ✅ |
| 5 | Story-chip på Hem | ✅ |

---

## Top 30 — status

| # | Åtgärd | Status |
|---|--------|--------|
| 1 | Commit Insights hardening | ✅ |
| 2 | Normalizer / låg event-volym | ✅ kod + `diagnose_event_pipeline.py` |
| 3 | Köks-HEIMAN 3/3 | ⬜ manuell |
| 4 | Händelser health UI | ✅ |
| 5 | Story på Hem | ✅ |
| 6 | Legacy `_2` coalesce bort | ✅ template förenklad + cleanup script |
| 7 | Vattensensor verify | ⬜ manuell — offline-hantering finns |
| 8 | Automation policy doc | ✅ [automation-policy.md](runbooks/automation-policy.md) |
| 9 | Baseline/anomaly i Teknik | ✅ MQTT `anomalies_24h` + chip Drift |
| 10 | Kraftringen live | ⬜ credentials |
| 11 | Nils rum placeholder | ✅ sektion borttagen |
| 12 | Yale ACCESS | ✅ borttagen |
| 13 | Grafana 7d-länk | ✅ chip Environment (+ `grafana_url` secret) |
| 14 | Navigation audit | ➖ oförändrat (fungerar) |
| 15 | Counters offline deep link | ✅ redan `/lovelace/home-tech/ops` |
| 16 | Hem utomhus ADR-006 copy | ✅ |
| 17 | Kameror → Frigate | ✅ 6 zoner |
| 18 | Scene delivery doc | ✅ i automation-policy |
| 19 | AOA vehicle doc + sv copy | ✅ |
| 20 | Frigate person selective | ✅ doc — multisensor på |
| 21 | Stale dt_* cleanup | ✅ `cleanup_stale_entities.py` |
| 22 | home-lab panel | ✅ redan i `configure_ha_sidebar.py` |
| 23 | Rum fukt/temp per rum | ⬜ väntar hårdvara |
| 24 | Environment recorder-fotnot | ✅ |
| 25 | Säkerhet story-länk | ✅ |
| 26 | Chip-färgschema | ➖ delvis (ny chips följer mönster) |
| 27 | Push copy audit | ➖ delvis (fordon, frigate alias) |
| 28 | CI dashboard-tester | ✅ `test-python.yml` + config path |
| 29 | Youth → Tester | ✅ |
| 30 | Batch 21 commit | ✅ denna commit |

---

## Nästa steg

1. `.\scripts\sync-config.ps1` + `.\scripts\deploy-insights-to-ha.ps1` + add-on restart  
2. Lägg `grafana_url` i host `secrets.yaml`  
3. `python scripts/cleanup_stale_entities.py` → rensa i HA UI  
4. ZHA re-pair kök brandvarnare
