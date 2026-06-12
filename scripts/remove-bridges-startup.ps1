# remove-bridges-startup.ps1 — Remove legacy dev PC bridge autostart (HAOS add-on cutover)
$ErrorActionPreference = "SilentlyContinue"
schtasks /delete /tn "HomeLab-Bridges" /f | Out-Null
$startup = [Environment]::GetFolderPath("Startup")
$shortcut = Join-Path $startup "HomeLab-Bridges.lnk"
if (Test-Path $shortcut) {
    Remove-Item -Force $shortcut
    Write-Host "Removed $shortcut"
} else {
    Write-Host "No HomeLab-Bridges startup shortcut found"
}
