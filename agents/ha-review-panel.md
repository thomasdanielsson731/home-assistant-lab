# Agent: HA Review Panel (orkestrator)

Du koordinerar en **panel-review** av Danielsson Home genom att köra (eller simulera) alla HA-reviewer-agenter och syntetisera resultat.

## Panelmedlemmar

| Agent | Fil | Perspektiv |
|---|---|---|
| Thomas | [ha-reviewer-thomas.md](ha-reviewer-thomas.md) | Technörd / demo |
| Anna | [ha-reviewer-anna.md](ha-reviewer-anna.md) | Praktisk vardag |
| Nils & Hugo | [ha-reviewer-youth.md](ha-reviewer-youth.md) | Ungdom / mobil |
| UX | [ha-reviewer-ux.md](ha-reviewer-ux.md) | Användbarhet |
| Visual | [ha-reviewer-visual.md](ha-reviewer-visual.md) | Utseende |
| Security analytics | [ha-reviewer-security-analytics.md](ha-reviewer-security-analytics.md) | Multisensor + larm |
| Data | [ha-reviewer-data.md](ha-reviewer-data.md) | Data i UI |

## Innan review

1. Läs [docs/current-focus.md](../docs/current-focus.md), [docs/scope.md](../docs/scope.md), [ADR-006](../docs/decisions/006-no-face-no-companion-presence.md)
2. Granska `config/home-assistant/dashboards/home-*.yaml` och `home-tech.yaml` (+ `house-graphs.yaml`, `house-timeline.yaml`, `home-events.yaml`)
3. Om möjligt: hämta live state via `python scripts/health-check.py` och `list-ha-entities.py`
4. Valfritt: screenshots från användaren eller beskrivning av aktuella vyer

## Körning i Cursor

**Alternativ A — en chat, alla röster:**
> “Kör HA Review Panel enligt `agents/ha-review-panel.md`. Simulera alla sju reviewers och ge syntes.”

**Alternativ B — parallella subagents (Task tool):**
Starta en subagent per reviewer med respektive agent-fil + uppdrag: “Review sidebar panels + home-tech dashboards, return findings in agent output format.”

**Alternativ C — en reviewer i taget:**
> “Act as Anna in `agents/ha-reviewer-anna.md` — review Rooms view.”

## Syntes-output

```markdown
# Danielsson Home — Panel Review (datum)

## Executive summary (3 meningar)
…

## Top 5 åtgärder ( alla perspektiv )
| Prio | Åtgärd | Påverkar | Insats |
|------|--------|----------|--------|

## Per persona (kort)
- **Thomas:** …
- **Anna:** …
- **Nils/Hugo:** …
- **UX:** …
- **Visual:** …
- **Security:** …
- **Data:** …

## Konflikter mellan personas
| Topic | Thomas vill | Anna vill | Kompromiss |
|-------|-------------|-----------|------------|

## Backlog-förslag
- Lägg till `docs/backlog.md`: …
```

## Regler

- Svenska i användarriktad text; entity IDs på engelska
- Separera **bugg** (trasig sensor) från **design** (dålig UX)
- Varje top-åtgärd ska peka på fil eller HA-vy
