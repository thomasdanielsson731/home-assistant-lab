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

Granska **Danielsson Home** (`home-lab.yaml`) och relaterade vyer. Kör alla via [ha-review-panel.md](ha-review-panel.md).

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
Granska home-lab.yaml och ge syntes med top 5 åtgärder på svenska.
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

1. [docs/current-focus.md](../docs/current-focus.md)
2. [CLAUDE.md](../CLAUDE.md)
3. [docs/vision.md](../docs/vision.md)
4. [docs/scope.md](../docs/scope.md)

Review agents should also skim [docs/dashboard-design.md](../docs/dashboard-design.md) and `config/home-assistant/dashboards/home-lab.yaml`.
