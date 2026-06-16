# Cursor Agents

Role definitions for AI assistants working in this repo. Reference the appropriate agent when starting a task.

## Engineering agents

| Agent | File | Use when |
|---|---|---|
| Architect | [architect.md](architect.md) | System design, ADRs, integration decisions |
| Analyst | [analyst.md](analyst.md) | Data patterns, dashboards, insight queries (backend) |
| Security | [security.md](security.md) | Camera/security config, privacy, network (infra) |
| Product Manager | [product-manager.md](product-manager.md) | Prioritization, scope, roadmap updates |

## HA dashboard review panel (personas)

Granska **sidebar panels** (`home-hem`, `home-cameras`, `home-security`, `home-events`, `home-rooms`) och **Teknik** (`home-tech.yaml`, admin). Kör alla via [ha-review-panel.md](ha-review-panel.md).

| Persona | File | Perspektiv |
|---|---|---|
| Thomas | [ha-reviewer-thomas.md](ha-reviewer-thomas.md) | Technörd — demo-värde, events, Axis/Insights |
| Anna | [ha-reviewer-anna.md](ha-reviewer-anna.md) | Vardag — lampor, larm, enkel mobil |
| Nils & Hugo | [ha-reviewer-youth.md](ha-reviewer-youth.md) | 20-åringar — mobil, rum, integritet |
| UX expert | [ha-reviewer-ux.md](ha-reviewer-ux.md) | Tasks, friktion, informationsarkitektur |
| Visual | [ha-reviewer-visual.md](ha-reviewer-visual.md) | Utseende, färger, grid, Mushroom |
| Security analytics | [ha-reviewer-security-analytics.md](ha-reviewer-security-analytics.md) | Multisensor, larm, unavailable-risk |
| Data (HA UI) | [ha-reviewer-data.md](ha-reviewer-data.md) | Grafer, gaps, trust i siffror |
| **Orkestrator** | [ha-review-panel.md](ha-review-panel.md) | Kör panel + syntes + top 5 |

### Snabbstart — full panel-review

```
Kör HA Review Panel enligt agents/ha-review-panel.md.
Granska home-hem/home-cameras/home-security/home-events/home-rooms och home-tech.yaml. Ge syntes med top 5 åtgärder på svenska.
```

### En persona i taget

```
Act as Anna — agents/ha-reviewer-anna.md — review Rooms and Home views.
```

## Usage in Cursor

Paste the agent file into a Cursor rule, or reference it at the start of a chat:

> "Act as the architect agent — review the proposed InfluxDB integration."

## Shared context

All agents should read before working:

1. [docs/current-focus.md](../docs/current-focus.md) — **start here** (active phase, commands)
2. [docs/scope.md](../docs/scope.md) — in/out of scope incl. [ADR-006](../docs/decisions/006-no-face-no-companion-presence.md)
3. [CLAUDE.md](../CLAUDE.md) — production facts, entity IDs, commands
4. [docs/vision.md](../docs/vision.md) — long-term direction

Review agents should also skim [docs/dashboard-design.md](../docs/dashboard-design.md) and `config/home-assistant/dashboards/home-*.yaml` (+ `home-tech.yaml` for admin views).
