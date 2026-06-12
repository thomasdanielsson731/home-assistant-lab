# install-scheduled-tasks.ps1 — Register Windows scheduled tasks for the lab
#
# Usage (run once):
#   .\scripts\install-scheduled-tasks.ps1
#
# Uses schtasks.exe (user-level, no admin required)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent

$maintCmd  = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$repoRoot\scripts\repo-maintenance.ps1`""
$dailyCmd  = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$repoRoot\scripts\repo-maintenance.ps1`" -Reload"

Write-Host "Registering Home Lab scheduled tasks ..."
Write-Host "  Repo: $repoRoot"
Write-Host ""

function Remove-OldTask {
    param([string]$Name)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    schtasks /delete /tn $Name /f 2>$null | Out-Null
    $ErrorActionPreference = $prev
}

# Retire per-bridge logon tasks (replaced by HomeLab-Bridges)
foreach ($old in @(
    "HomeLab-AirQualityBridge",
    "HomeLab-AOABridge",
    "HomeLab-EventNormalizer",
    "HomeLab-TimelineServer"
)) {
    Remove-OldTask $old
}

# Every 6 hours: commit + push + sync
schtasks /create /tn "HomeLab-Maintenance" /tr $maintCmd /sc hourly /mo 6 /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-Maintenance (every 6 h)" }

# Daily at 04:00: commit + push + sync + HA reload
schtasks /create /tn "HomeLab-MaintenanceDaily" /tr $dailyCmd /sc daily /st 04:00 /f
if ($LASTEXITCODE -eq 0) { Write-Host "  Registered: HomeLab-MaintenanceDaily (04:00)" }

# Legacy HomeLab-Bridges (start-bridges.ps1) — retired 2026-06-12; platform runs on HAOS add-on.
Remove-OldTask "HomeLab-Bridges"
$startup = [Environment]::GetFolderPath("Startup")
$legacyShortcut = Join-Path $startup "HomeLab-Bridges.lnk"
if (Test-Path $legacyShortcut) {
    Remove-Item -Force $legacyShortcut
    Write-Host "  Removed legacy startup shortcut: HomeLab-Bridges.lnk"
}

Write-Host ""
Write-Host "Verify: schtasks /query /tn HomeLab-Maintenance"
Write-Host "Logs:   $repoRoot\logs\maintenance.log"
