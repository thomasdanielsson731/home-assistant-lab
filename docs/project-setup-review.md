# Project Setup Review — varför gröna tester ≠ fungerande HA

**Datum:** 2026-06-20  
**Trigger:** Händelser, Analytics och Environment trasiga i HA Windows-klienten; Teknik-bilder utdragna. Tester och agenter rapporterar OK.

---

## Kort svar

Projektet har **tre separata “sanningar”** som inte hålls i synk:

| Sanning | Vad den verifierar | Vad den *inte* verifierar |
|---------|-------------------|---------------------------|
| **Git / pytest** | Python-logik + att YAML i repot innehåller rätt strängar | Att HA kör samma YAML |
| **health-check / verify-insights** | Add-on svarar HTTP 200 på `:8765` och Cloudflare | Att iframe fungerar i HA-appen |
| **HA runtime** (`/config` på host) | Det användaren faktiskt ser | — |

**Rotorsak #1:** Config i repot har pushats men **inte synkats till HA** (`sync-config.ps1` körs manuellt).  
**Rotorsak #2:** Insights-UX bygger på **cross-origin iframe** — arkiteturen är medvetet fragil i HA WebView (Windows-klienten).  
**Rotorsak #3:** Testerna och agenterna granskar **aldrig** den faktiska HA-upplevelsen.

---

## Bevis: host drift (2026-06-20)

Jämförelse repo vs `/config` på `192.168.68.175`:

| Fil | Repo (rader) | Host (rader) | `insights_server_ok` repo | Host | Status |
|-----|-------------|--------------|-------------------------|------|--------|
| `home-events.yaml` | 110 | **76** | 3 | **0** | ❌ **EJ SYNKAD** |
| `house-timeline.yaml` | 103 | 103 | 3 | 3 | ⚠️ nominellt synkad |
| `house-graphs.yaml` | 111 | 104 | 3 | 3 | ⚠️ saknar batch 21 (Grafana, recorder-fotnot) |
| `home-tech.yaml` | 972 | ~972 | — | `fit_mode` 8 | ✅ synkad |

**Händelser** på host saknar batch 21 helt: ingen `insights_server_ok`-chip, ingen offline-banner, ingen desktop-knapp “Öppna i ny flik”. Om iframe failar → tom vy utan fallback.

Backend (Insights add-on) svarar **200** med CSP — problemet är **inte** att servern är nere:

```
GET http://192.168.68.175:8765/timeline     → 200
GET https://insights.danielsson.cloud/      → 200
secrets.yaml: Cloudflare URLs ✅
add-on: started ✅
```

---

## Varför pytest är grönt (263/263)

Tester i `tests/` gör i princip:

1. **Python-unit/integration** — `timeline_server`, `event_normalizer`, etc. mot temp-filer och localhost.
2. **YAML string matching** — `"type: iframe" in text`, `"sensor.insights_server_ok" in text`.
3. **Ingress-safe HTML** — att JavaScript inte använder absoluta `/api/v1`-paths i *genererad* HTML.

Tester gör **inte**:

- SSH till HA och jämföra `/config/dashboards/*.yaml` med repot
- Öppna HA frontend (WebView eller webbläsare)
- Simulera `iframe` inbäddad från `https://ha.danielsson.cloud` → `https://insights.danielsson.cloud`
- Verifiera att Windows HA-klienten kan rendera panel-vyer
- Testa `picture-entity`-layout i sections/grid

**Konsekvens:** Varje commit kan vara “grön” medan produktion kör veckogammal YAML.

---

## Varför agenterna såg inga problem

Panel-agenter (`ha-review-panel.md`) instrueras att:

- Läsa dashboard-YAML **i repot**
- Köra `health-check.py` (API + entities)
- Syntetisera UX-bedömning utan screenshots

De **antar** att repo = runtime. Review board 2026-06-20 sa “Go with caveats” men noterade deploy som öppen punkt — utan att **automatiskt bevisa** host drift.

`verify-insights-ha.ps1` kontrollerar:

- HTTP GET till Insights (direct + Cloudflare)
- `timeline_url` / `environment_url` i secrets (inte `events_url` i output, men den finns på host)
- Add-on state

Den kontrollerar **inte** iframe embedding, CSP mot faktisk HA-origin, eller dashboard-filernas hash på host.

---

## Arkitekturproblem: Insights via iframe

```
┌─────────────────────────────────────┐
│  HA frontend (ha.danielsson.cloud)   │
│  ┌───────────────────────────────┐  │
│  │ iframe → insights.danielsson   │  │  ← annan origin
│  │   .cloud/timeline              │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Kända failure modes:**

| Problem | Symptom | Nuvarande mitigering |
|---------|---------|---------------------|
| Cross-origin iframe | Tom iframe i HA Windows-app | “Öppna i ny flik”-knapp (saknas på host för Händelser) |
| CSP `frame-ancestors` | Blockerad embedding | Tillåter `ha.danielsson.cloud`, `192.168.68.175:8123` — **inte** t.ex. `https://192.168.68.175:8123` |
| Ingress URL | 401 i iframe | Bytt till Cloudflare ✅ |
| LAN `http://:8765` i secrets | Mixed content via HTTPS HA | Cloudflare ✅ |
| `panel: true` + iframe | Layout-buggar i vissa klienter | `aspect_ratio` 125–150% |

**Designbeslut (ADR-005):** Analytics/Environment/Händelser *är* iframe-first. Det ger kraftfull UX men **binder till webbläsare/WebView-beteende** som pytest inte fångar.

---

## Teknik — utdragna bilder

`home-tech.yaml` → **SENASTE BILDER**: `grid` 2 kolumner + `picture-entity` + `aspect_ratio: "16:9"` + `fit_mode: contain`.

Host har `fit_mode: contain` (synkad). Stretch beror troligen på:

1. **Frigate/Axis MQTT-bilder** är inte 16:9 — kortet tvingar ratio, bilden skalas konstigt i grid-cell.
2. **HA `picture-entity` i grid** respekterar aspect ratio inkonsekvent (känd frontend-quirk).
3. **Sections `max_columns: 2`** på Drift-vyn kan förstora celler.

Detta är **layout/entity**, inte trasig MQTT — tester fångar det inte.

---

## Grundläggande setup-problem (prioriterade)

### P0 — Deploy gap (mänsklig process)

| Problem | Fix |
|---------|-----|
| Git push ≠ HA config | Kör `.\scripts\sync-config.ps1` efter varje dashboard-ändring |
| Insights scripts ≠ add-on | Kör `.\scripts\deploy-insights-to-ha.ps1` + restart add-on |
| Ingen drift-detektion | Nytt script `verify-ha-deploy.ps1` (jämför host vs repo) |

### P1 — Test gap

| Problem | Fix |
|---------|-----|
| Ingen host parity-test | CI-steg: SSH + hash/rader för nyckel-YAML |
| Ingen iframe E2E | Playwright eller manuell checklista i runbook |
| Agents läser bara repo | Panel ska kräva `verify-ha-deploy` output |

### P2 — Arkitektur

| Problem | Fix |
|---------|-----|
| iframe-first för 3 huvudvyer | Överväg: HA sidebar-länk till Insights (ny flik) som primär; iframe som bonus |
| CSP origins ofullständiga | Utöka `frame-ancestors` med alla HA-URL:er inkl. `https://192.168.68.175:8123` |
| Windows HA-klient | Dokumentera: “Använd webbläsare eller Öppna i ny flik om iframe tom” |

### P3 — Teknik-bilder

| Problem | Fix |
|---------|-----|
| Grid + picture-entity | Byt till 1 kolumn, `type: picture`, eller `custom:frigate-card` |
| 8 små bilder | Färre, större kort — bättre UX |

---

## Rekommenderad omedelbar åtgärd (du)

```powershell
# 1. Synka dashboard-YAML till HA (fixar Händelser direkt)
.\scripts\sync-config.ps1

# 2. Synka Insights-server + starta om add-on
.\scripts\deploy-insights-to-ha.ps1
# SSH: ha apps restart 25d01a20_danielsson_insights

# 3. Hårdladda HA (Ctrl+F5) eller starta om Windows HA-klienten

# 4. Om iframe fortfarande tom: använd knapparna "Öppna i ny flik"
#    eller öppna https://insights.danielsson.cloud/timeline i Edge/Chrome
```

---

## Förslag: ny “Definition of Done”

En dashboard-/Insights-ändring är **inte klar** förrän:

1. ✅ pytest grön  
2. ✅ `verify-insights-ha.ps1` grön  
3. ✅ **`verify-ha-deploy.ps1` grön** (host = repo)  
4. ✅ Manuell 30 s check i HA Windows-klient *eller* webbläsare (Händelser + Analytics + Environment)

---

## Relaterade docs

- [ha-timeline-dashboard.md](runbooks/ha-timeline-dashboard.md) — iframe-felsökning  
- [review-board.md](review-board.md) — panel findings  
- [architecture-review.md](architecture-review.md) — äldre infra-granskning  
