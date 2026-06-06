# install-scheduled-tasks.ps1 — Register Windows scheduled tasks for the lab
#
# Usage (run once):
#   .\scripts\install-scheduled-tasks.ps1
#
# Uses schtasks.exe (user-level, no admin required)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$python   = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = "python" }

$maintCmd  = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$repoRoot\scripts\repo-maintenance.ps1`""
$dailyCmd  = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$repoRoot\scripts\repo-maintenance.ps1`" -Reload"
$airCmd  = "`"$python`" `"$repoRoot\scripts\air_quality_bridge.py`""
$aoaCmd  = "`"$python`" `"$repoRoot\scripts\aoa_bridge.py`""
$normCmd = "`"$python`" `"$repoRoot\scripts\event_normalizer.py`""
$timeCmd = "`"$python`" `"$repoRoot\scripts\timeline_server.py`""

Write-Host "Registering Home Lab scheduled tasks ..."
Write-Host "  Repo: $repoRoot"
Write-Host ""

function Register-Task {
    param([string]$Name, [string]$Args)
    schtasks /create /tn $Name /tr $Args /f 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Registered: $Name"
    } else {
        Write-Host "  FAILED: $Name (exit $LASTEXITCODE)"
    }
}

# Every 6 hours: commit + push + sync
schtasks /create /tn "HomeLab-Maintenance" /tr $maintCmd /sc hourly /mo 6 /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-Maintenance (every 6 h)" }

# Daily at 04:00: commit + push + sync + HA reload
schtasks /create /tn "HomeLab-MaintenanceDaily" /tr $dailyCmd /sc daily /st 04:00 /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-MaintenanceDaily (04:00)" }

# MQTT bridges at logon
schtasks /create /tn "HomeLab-AirQualityBridge" /tr $airCmd /sc onlogon /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-AirQualityBridge (on logon)" }
schtasks /create /tn "HomeLab-AOABridge" /tr $aoaCmd /sc onlogon /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-AOABridge (on logon)" }
schtasks /create /tn "HomeLab-EventNormalizer" /tr $normCmd /sc onlogon /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-EventNormalizer (on logon)" }
schtasks /create /tn "HomeLab-TimelineServer" /tr $timeCmd /sc onlogon /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-TimelineServer (on logon)" }

Write-Host ""
Write-Host "Verify: schtasks /query /tn HomeLab-Maintenance"
Write-Host "Logs:   $repoRoot\logs\maintenance.log"
