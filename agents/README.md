# Cursor Agents

Role definitions for AI assistants working in this repo. Reference the appropriate agent when starting a task.

| Agent | File | Use when |
|---|---|---|
| Architect | [architect.md](architect.md) | System design, ADRs, integration decisions |
| Analyst | [analyst.md](analyst.md) | Data patterns, dashboards, insight queries |
| Security | [security.md](security.md) | Camera/security config, privacy, access control |
| Product Manager | [product-manager.md](product-manager.md) | Prioritization, scope, roadmap updates |

## Usage in Cursor

Paste the agent file content into a Cursor rule, or reference it at the start of a chat:

> "Act as the architect agent — review the proposed InfluxDB integration."

## Shared Context

All agents should read before working:

1. [docs/current-focus.md](../docs/current-focus.md)
2. [CLAUDE.md](../CLAUDE.md)
3. [docs/vision.md](../docs/vision.md)
4. [docs/scope.md](../docs/scope.md)
