# Maintenance Runbook

Automated commit, push, and config sync between the dev PC and HAOS.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/finish-dev.ps1` | **Kör efter utveckling:** pytest, commit, push, sync, deploy, verify |
| `scripts/repo-maintenance.ps1` | Schemalagd snapshot (commit + push + sync) |
| `scripts/sync-config.ps1` | Sync only (no git) |
| `scripts/verify-ha-deploy.ps1` | Compare repo dashboards vs HA host (drift check) |
| `scripts/install-scheduled-tasks.ps1` | Register Windows scheduled tasks (run once) |

Linux/macOS: `scripts/repo-maintenance.sh` (same logic).

## Manual Run

```powershell
# Efter utveckling - allt i ett svep
.\scripts\finish-dev.ps1

# Schemalagd / lättare (ingen Insights-deploy)
.\scripts\repo-maintenance.ps1

# Also reload HA YAML after sync
.\scripts\repo-maintenance.ps1 -Reload

# Preview without changes
.\scripts\repo-maintenance.ps1 -DryRun
```

## Scheduled Tasks (Windows)

Run once to register:

```powershell
.\scripts\install-scheduled-tasks.ps1
```

| Task | Schedule | Action |
|---|---|---|
| `HomeLab-Maintenance` | Every 6 hours | Commit + push + sync |
| `HomeLab-MaintenanceDaily` | Daily 04:00 | Commit + push + sync + HA reload |
| `HomeLab-Bridges` | — | **Removed 2026-06-12** — use `remove-bridges-startup.ps1` if shortcut returns |

Remove legacy bridge autostart: `.\scripts\remove-bridges-startup.ps1`. Re-run `install-scheduled-tasks.ps1` only if you need to refresh maintenance tasks.

Verify:

```powershell
Get-ScheduledTask -TaskName 'HomeLab-*' | Format-Table TaskName, State
Get-Content logs\maintenance.log -Tail 20
```

## HA Reload Methods

The `-Reload` flag uses one of:

1. **REST** (preferred, lightweight) — set `HA_TOKEN` in `.env`
2. **SSH fallback** — `ha core restart` via SSH add-on (heavier, ~40 s downtime)

Create a long-lived token:

- **Automated:** `python scripts/create-ha-token.py` (uses existing `HA_TOKEN` in `.env` to mint a new one)
- **Manual:** HA → Profile → Security → Long-Lived Access Tokens

Current token name: `home-assistant-lab-maintenance` (10-year lifespan).

## What Gets Committed

Auto-commits include all tracked changes except:

- `.env` (secrets)
- `config/home-assistant/secrets.yaml`
- `logs/` (gitignored)

Commit message format: `chore: auto maintenance snapshot YYYY-MM-DD HH:mm`

## Troubleshooting

| Symptom | Fix |
|---|---|
| Task not running | `Get-ScheduledTaskInfo -TaskName HomeLab-Maintenance` |
| git push fails | Check network + GitHub credentials |
| Sync fails | Verify SSH: `ssh root@192.168.68.175 -p 22222` |
| HA reload fails | Add `HA_TOKEN` to `.env` or check SSH access |
