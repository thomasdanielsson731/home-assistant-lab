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
$bridgesCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$repoRoot\scripts\start-bridges.ps1`""

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

# All MQTT bridges + event platform at logon (may need admin — Startup shortcut is fallback)
$prev = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
schtasks /create /tn "HomeLab-Bridges" /tr $bridgesCmd /sc onlogon /f 2>&1 | Out-Null
$ErrorActionPreference = $prev
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Registered: HomeLab-Bridges (on logon)"
} else {
    Write-Host "  SKIP  HomeLab-Bridges (access denied) — using Startup shortcut"
}

# Startup folder shortcut (backup if schtasks onlogon is delayed)
$startup = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startup "HomeLab-Bridges.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$repoRoot\scripts\start-bridges.ps1`""
$shortcut.WorkingDirectory = $repoRoot
$shortcut.Description = "Danielsson Insights MQTT bridges"
$shortcut.Save()
Write-Host "  Startup shortcut: $shortcutPath"

Write-Host ""
Write-Host "Verify: schtasks /query /tn HomeLab-Bridges"
Write-Host "Logs:   $repoRoot\logs\maintenance.log"
