# repo-maintenance.ps1 — Auto-commit, push, and sync config to HAOS
#
# Usage:
#   .\scripts\repo-maintenance.ps1              # commit + push + sync
#   .\scripts\repo-maintenance.ps1 -Reload      # also reload HA YAML via REST/SSH
#   .\scripts\repo-maintenance.ps1 -DryRun      # preview only
#
# Scheduled: registered by install-scheduled-tasks.ps1 (every 6 hours)

param(
    [switch]$Reload,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$logDir   = Join-Path $repoRoot "logs"
$logFile  = Join-Path $logDir "maintenance.log"

function Write-Log {
    param([string]$Message)
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Message"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

Set-Location $repoRoot
Write-Log "=== Maintenance start ==="

# Load .env
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=][^=]*)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

$HA_HOST     = if ($env:HA_HOST)     { $env:HA_HOST }     else { "192.168.68.175" }
$HA_SSH_PORT = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$HA_USER     = if ($env:HA_USER)     { $env:HA_USER }     else { "root" }

# ── 1. Git commit + push ─────────────────────────────────────────────────────

$status = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: git status failed"
    exit 1
}

# Filter out paths that must never be committed
$dirty = $status | Where-Object {
    $_ -notmatch '^\?\? .*\.env$' -and
    $_ -notmatch 'secrets\.yaml' -and
    $_ -notmatch '^\?\? logs/'
}

if ($dirty) {
    Write-Log "Uncommitted changes detected:"
    $dirty | ForEach-Object { Write-Log "  $_" }

    if ($DryRun) {
        Write-Log "[dry-run] Would commit and push"
    } else {
        git add -A
        # Unstage secrets and .env if accidentally picked up
        git reset HEAD -- .env 2>$null
        git reset HEAD -- config/home-assistant/secrets.yaml 2>$null

        $staged = git diff --cached --name-only
        if ($staged) {
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
            git commit -m "chore: auto maintenance snapshot $timestamp"
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Committed: $($staged -join ', ')"
                git push origin HEAD
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "Pushed to origin"
                } else {
                    Write-Log "WARN: git push failed (exit $LASTEXITCODE)"
                }
            }
        } else {
            Write-Log "Nothing staged after filter - skip commit"
        }
    }
} else {
    Write-Log "Working tree clean - skip commit"
}

# ── 2. Sync config to HAOS ───────────────────────────────────────────────────

if ($DryRun) {
    & "$PSScriptRoot\sync-config.ps1" -DryRun
} else {
    Write-Log "Syncing config to HAOS ..."
    & "$PSScriptRoot\sync-config.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: sync-config failed"
        exit 1
    }
    Write-Log "Sync complete"
}

# ── 3. Reload HA YAML (optional) ─────────────────────────────────────────────

if ($Reload -and -not $DryRun) {
    $haToken = $env:HA_TOKEN
    if ($haToken) {
        Write-Log "Reloading HA YAML via REST ..."
        try {
            $headers = @{ Authorization = "Bearer $haToken" }
            Invoke-RestMethod -Method POST `
                -Uri "http://${HA_HOST}:8123/api/services/homeassistant/reload_core_config" `
                -Headers $headers -TimeoutSec 30 | Out-Null
            Write-Log "HA YAML reload requested"
        } catch {
            Write-Log "WARN: REST reload failed - $($_.Exception.Message)"
        }
    } else {
        Write-Log "Reloading HA via SSH (ha core restart) ..."
        ssh -p $HA_SSH_PORT -o StrictHostKeyChecking=no "${HA_USER}@${HA_HOST}" "ha core restart" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "HA core restart initiated"
        } else {
            Write-Log "WARN: HA restart failed (exit $LASTEXITCODE)"
        }
    }
}

Write-Log "=== Maintenance done ==="
