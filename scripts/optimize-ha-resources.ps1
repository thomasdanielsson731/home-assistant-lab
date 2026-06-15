# optimize-ha-resources.ps1 - Reduce HA host load (4 GB Latitude 3120)
param(
    [switch]$DryRun,
    [switch]$SkipSync
)

$repoRoot = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=][^=]*)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

$HA_HOST = if ($env:HA_HOST) { $env:HA_HOST } else { "192.168.68.175" }
$SSH_PORT = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$SSH_USER = if ($env:HA_USER) { $env:HA_USER } else { "root" }
$sshTarget = "${SSH_USER}@${HA_HOST}"

function Invoke-HaSsh([string]$Command) {
    if ($DryRun) {
        Write-Host "  [dry-run] $Command"
        return
    }
    ssh -p $SSH_PORT -o StrictHostKeyChecking=no -o ConnectTimeout=15 $sshTarget $Command
}

function Get-LoadSnapshot {
    Invoke-HaSsh "uptime; free -h | head -2"
}

Write-Host "=== HA resource optimization ($HA_HOST) ===`n"

if (-not $SkipSync) {
    Write-Host "Syncing config to HAOS ..."
    if ($DryRun) {
        Write-Host "  [dry-run] .\scripts\sync-config.ps1"
    } else {
        & (Join-Path $PSScriptRoot "sync-config.ps1")
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

Write-Host "`nBefore:"
Get-LoadSnapshot

Write-Host "`nStopping non-lab add-ons (Scrypted, Double Take, duplicate Advanced SSH) ..."
$addons = @(
    @{ Slug = "09e60fb6_scrypted"; Name = "Scrypted" },
    @{ Slug = "c7657554_double-take"; Name = "Double Take" },
    @{ Slug = "a0d7b954_ssh"; Name = "Advanced SSH (error state)" }
)
foreach ($addon in $addons) {
    Write-Host "  $($addon.Name) ($($addon.Slug))"
    Invoke-HaSsh "ha apps stop $($addon.Slug) 2>/dev/null || true"
    Invoke-HaSsh "ha apps options $($addon.Slug) '{`"boot`":`"manual`"}' 2>/dev/null || true"
}

Write-Host "`nRestarting Frigate to apply detect FPS changes ..."
Invoke-HaSsh "ha apps restart ccab4aaf_frigate-fa"

Write-Host "`nRestarting Danielsson Insights (AOA poll interval) ..."
Invoke-HaSsh "ha apps restart 25d01a20_danielsson_insights"

Write-Host "`nReloading HA recorder config ..."
$token = $env:HA_TOKEN
if ($token -and -not $DryRun) {
    try {
        $headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
        Invoke-RestMethod -Uri "http://${HA_HOST}:8123/api/services/homeassistant/reload_core_config" `
            -Method Post -Headers $headers -TimeoutSec 30 | Out-Null
        Write-Host "  OK    core config reloaded"
    } catch {
        Write-Host "  WARN  reload failed - run: ha core restart (via SSH)"
    }
} else {
    Write-Host "  SKIP  set HA_TOKEN in .env for REST reload, or restart HA core manually"
}

Start-Sleep -Seconds 8
Write-Host "`nAfter:"
Get-LoadSnapshot

Write-Host "`nAdd-on states:"
Invoke-HaSsh 'for s in 09e60fb6_scrypted c7657554_double-take ccab4aaf_frigate-fa 25d01a20_danielsson_insights a0d7b954_grafana core_matter_server; do ha apps info $s 2>/dev/null | grep -E "^name:|^state:" | tr "\n" " "; echo; done'

Write-Host "`nDone. Hard-refresh HA UI (Ctrl+F5)."
if ($DryRun) { Write-Host "(dry-run - no changes applied)" }
