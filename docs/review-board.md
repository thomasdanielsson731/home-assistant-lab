# Danielsson Home — Review Board

Levande panel-syntes från [ha-review-panel.md](../agents/ha-review-panel.md).  
Prioriterad åtgärdslista: [top-30-proposal.md](top-30-proposal.md).

**Senast uppdaterad:** 2026-06-20  
**Panel-körning:** alla 7 reviewers + orkestrator

---

## Verifiering (automated)

| Check | Resultat | Detalj |
|-------|----------|--------|
| `python -m pytest` | ✅ **263/263** | Coverage 90.06% (gate 85%) |
| `python scripts/health-check.py` | ✅ Pass | Add-on API 200 — **säger inget om HA iframe** |
| `verify-ha-deploy.ps1` | ❌ **DRIFT** | `home-events.yaml` 110 vs 76 rader på host; `house-graphs` saknar batch 21 |

**2026-06-20 rotorsak:** Gröna tester + agenter granskar **repot**, inte **HA runtime**. Se [project-setup-review.md](project-setup-review.md).

**Live timeline (2026-06-20 ~09:15):** 2 händelser / 24 h (environment @ `driveway_env`). Person/fordon = 0 — troligen lugnt + batch 21 (AOA→person) ej deployat till add-on än.

---

## Executive summary

Efter batch 21 är familje- och Teknik-vyer i bra form: health-chips på Händelser/Analytics/Environment, story-länkar, Frigate-zonlänkar, automation-policy dokumenterad. **263 tester gröna** — release readiness **Go with caveats**.

Kvarvarande gaps är **operativa** (deploy till HAOS, ZHA kök 3/3, `grafana_url` i secrets, rensa stale entities) och **små UX-trassel** (Nils-rum-chip på Hem utan motsvarande sektion i Rum). Frigate REST :5000 nås inte från dev PC — förväntat om porten inte exponeras; MQTT `frigate/events` på add-on är den viktiga vägen.

---

## Top 5 — nästa åtgärder (batch 22)

| Prio | Åtgärd | Påverkar | Insats | Fil / vy |
|------|--------|----------|--------|----------|
| 1 | Deploy batch 21 till HAOS | Timeline person-events, anomalies chip | S | `sync-config.ps1`, `deploy-insights-to-ha.ps1` |
| 2 | Köks-HEIMAN re-pair → 3/3 | Säkerhet S1 om 2/3 | S | [zigbee-setup.md](runbooks/zigbee-setup.md) |
| 3 | Ta bort eller fixa **Nils rum**-chip på Hem | Anna UX — död navigering | S | `home-hem.yaml` |
| 4 | Host `secrets.yaml`: `grafana_url` + kör cleanup script | Environment Grafana-chip | S | `cleanup_stale_entities.py` |
| 5 | Svensk copy audit push (rök, vatten, loitering) | UX polish | S | `automations/security/` |

---

## Review board — öppna findings

| ID | Severity | Finding | Agent | Status | Åtgärd |
|----|----------|---------|-------|--------|--------|
| RB-01 | S1 | Brandvarnare troligen 2/3 (`detector_count`) | Security | ⬜ Open | ZHA re-pair kök |
| RB-02 | S2 | Batch 21 kod ej deployad till add-on | Tester | ⬜ Open | deploy + restart |
| RB-03 | S3 | Nils rum-chip på Hem, sektion borttagen i Rum | Anna, UX | ⬜ Open | ta bort chip eller återinför sektion |
| RB-04 | S3 | `grafana_url` saknas troligen i host secrets | Data | ⬜ Open | secrets + sync |
| RB-05 | S3 | Stale `dt_*` / `_2` entities i HA registry | Data | ⬜ Open | `cleanup_stale_entities.py` |
| RB-06 | S3 | Frigate API :5000 unreachable från dev PC | Tester | 📋 Won't fix | MQTT-väg OK; ev. health-check note |
| RB-07 | S3 | Story öppnar extern URL — ingen one-liner på Hem | Anna | ⬜ Open | valfritt: template från `/api/v1/story/today` |
| RB-08 | S4 | Chip “Frigate” på svenska UI (engelska etikett) | Visual | ⬜ Open | byt till “Klipp” eller “Frigate-klipp” |
| RB-09 | S4 | Chip-färgschema delvis inkonsekvent Historik | Visual | ➖ Backlog | batch 22+ |
| RB-10 | — | Kraftringen energy | Data | ⬜ Blocked | credentials |
| RB-11 | — | Fukt/temp per rum | Anna | ⬜ Blocked | hårdvara |

### Stängda sedan förra board (batch 21)

| ID | Finding | Status |
|----|---------|--------|
| — | Händelser utan `insights_server_ok` | ✅ batch 21 |
| — | Story saknas på Hem/Säkerhet | ✅ batch 21 |
| — | Yale ACCESS “Kommer snart” | ✅ borttagen |
| — | Legacy `_2` coalesce i templates | ✅ förenklad |
| — | Youth-agent kvar i repo | ✅ borttagen (lokal fil rensad) |

---

## Per persona

### Thomas — technörd-review

**Demo-poäng:** 7/10 (visar efter deploy + några person-events)

**Det som imponerar**
- Insights add-on v0.2.4, correlation, Teknik Live/Drift/Anomalier
- Frigate-länkar per zon, automation-policy, diagnose script
- Axis stack synlig (AOA + scene + SPL + D6210)

**Skämmer sig / fixa före demo**
- [P1] Deploy batch 21 — annars tom person-spår trots AOA-kod i repo
- [P2] Timeline sparse (2 env/24 h) — visa minst en AOA/scene-person efter deploy
- [P3] Grafana-chip kräver `grafana_url` i secrets

**Cool factor**
- Story-länk + anomaly chip i Drift — bra narrativ för kollegor

---

### Anna — vardags-review

**Skulle jag använda detta dagligen?** Ja, delvis

**Det som funkar bra**
- Släck allt / kök / vardagsrum chips
- Rök/vatten chips med tydliga färger
- Story-chip på Hem (öppnar dagssummering)

**Irriterande / förvirrande**
- [P2] “Nils rum”-chip leder till Rum utan Nils-innehåll
- [P3] Story i ny flik — önskar kort svensk rad på Hem (valfritt)
- [P3] Environment/Analytics iframes på iPad — fallback finns men kräver ett extra tryck

**Önskemål**
- En rad “Inget särskilt utomhus idag” när event-räknare = 0

---

### Tester — QA review

**Release readiness:** **Go with caveats**

| ID | Flow | Result | Severity |
|----|------|--------|----------|
| T1 | `pytest` full suite | Pass (263) | — |
| T2 | `health-check.py` | Pass | — |
| T3 | Insights iframes + mobil fallback | Pass (YAML + tester) | — |
| T4 | Händelser health parity | Pass (batch 21) | — |
| T5 | Event pipeline person count | Caveat — 0/24 h | S3 |
| T6 | Nils chip → Rum | Fail — ingen sektion | S3 |
| T7 | Deploy parity repo vs HAOS | Not verified | S2 |

**Regressions att bevaka**
- `insights_*_display` utan `_2` fallback — kräver MQTT counters live
- `test_insights_ingress.py` vid secrets-ändringar

**Test gaps**
- E2E deploy verify i CI (optional smoke mot :8765)

---

### UX review

**Task success (1–5):** T1 utomhus 4 · T2 lampor 5 · T3 säkerhet 4 · T4 händelser 4 · T5 unavailable 4

| Task | Problem | Impact | Fix |
|------|---------|--------|-----|
| Nils chip | Navigerar till tom sektion | Förvirring | RB-03 |
| Händelser vs Analytics | Två vägar till liknande data | Kognitiv load | OK — olika granularitet; behåll chips |
| Story | Extern URL | Bryter HA-kontext | RB-07 valfritt |

**Quick wins:** RB-03, RB-08  
**Structural:** Rum fukt/temp när sensorer finns (RB-11)

---

### Visual review

**Overall polish:** 8/10

**Styrkor**
- Mushroom sections konsekventa; grön/amber/röd semantik på säkerhet
- Counter chips använder `*_display`

**Visuella buggar**
- [Kameror] “Frigate” engelska på svenska UI → RB-08
- [Hem] Två bed-chips (Hugo + Nils) när Nils saknas i Rum

**Färg-/ikon-lexikon (befintlig)**
- Alarm: röd · OK: grön · Varning/offline: amber · Metrics: grå/blå

---

### Security & multisensor review

| Risk | Severity | Nuvarande | Gap | Förslag |
|------|----------|-----------|-----|---------|
| Köks brandvarnare | High | 2/3 troligen | S1 om offline | RB-01 |
| Vatten SNZB-05P | Medium | UI hanterar unavailable | Verifiera live | manuell check |
| Person push | Low | Multisensor ON | Bra | behåll |
| Loitering | Low | ON | Bra | — |

**Larmtäckning:** Frigate + AOA + scene + house_outdoor_presence — defense in depth OK vid entré/uppfart.

**Sensor health:** `detector_count` amber i UI — korrekt beteende om < 3.

---

### Data review (HA experience)

**Trust score:** 7/10

| Metric | Källa | UI | Kommentar |
|--------|-------|-----|-----------|
| Temp/humidity/CO₂ ute | D6210 MQTT | Hem, Environment | ✅ live |
| Inne snitt | HEIMAN | Hem, Rum | ✅ |
| 24 h counters | MQTT bridge | Chips alla vyer | ✅ om deployad |
| Anomalier | baseline_engine | Teknik Drift | ✅ kod; deploy pending |
| Person events | Frigate + AOA | Timeline | ⚠️ sparse |

**Misleading / broken:** Inga trasiga grafer — låg event-volym kan misstolkas som “trasig pipeline” (fotnot på Händelser delvis fixad batch 21).

**Saknad i UI:** Kraftringen energy (blocked RB-10).

---

## Konflikter mellan personas

| Topic | Thomas vill | Anna vill | Kompromiss |
|-------|-------------|-----------|------------|
| Story | Full story + Ollama | Kort svensk rad på Hem | Extern story URL + ev. en-rads template senare |
| Frigate chip | Engelskt varumärke “Frigate” | Svenska “Klipp” | “Frigate-klipp” eller mdi-filmstrip utan text |
| Event-räknare 0 | Debug/deploy | “Fungerar det?” | Deploy batch 21 + lugnt-hus copy ✅ delvis |
| Teknik synlig | All admin synlig | Enkel familje-IA | Oförändrat — funkar |

---

## Backlog-koppling

| Backlog | Item |
|---------|------|
| P7-28 | Panel review 2026-06-20 — review board + batch 22 |
| P7-29 | Deploy batch 21 till HAOS |
| P7-30 | Nils chip + push copy audit |

---

## Körning (upprepa)

```powershell
python -m pytest
python scripts/health-check.py
python scripts/diagnose_event_pipeline.py
```

Panel: *“Kör HA Review Panel enligt `agents/ha-review-panel.md`”* → uppdatera detta dokument + [top-30-proposal.md](top-30-proposal.md).
