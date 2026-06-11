# deploy-insights-to-ha.ps1 — Sync scripts + events to HA share; optional Ingress secrets
param(
    [switch]$UseIngressSecrets,
    [string]$AppSlug = "",
    [switch]$DryRun
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
$HA_USER = if ($env:HA_USER) { $env:HA_USER } else { "root" }
$HA_SSH_PORT = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$target = "${HA_USER}@${HA_HOST}"
$sshOpts = @("-p", $HA_SSH_PORT, "-o", "StrictHostKeyChecking=no")
$scpOpts = @("-P", $HA_SSH_PORT, "-o", "StrictHostKeyChecking=no")

$shareRoot = "/share/danielsson-insights"
$scriptsRemote = "$shareRoot/scripts"
$eventsRemote = "$shareRoot/events"

function Invoke-Remote($cmd) {
    if ($DryRun) { Write-Host "[dry-run] ssh $cmd"; return "" }
    return ssh @sshOpts $target $cmd 2>$null
}

function Copy-File($local, $remote) {
    if ($DryRun) { Write-Host "[dry-run] scp $local -> $remote"; return }
    scp @scpOpts $local "${target}:${remote}" | Out-Null
}

function Get-InsightsAppSlug {
    $line = Invoke-Remote "ha apps list 2>/dev/null | grep danielsson_insights | head -1"
    if (-not $line) { return "" }
    if ($line -match '^\s*(\S+)\s') { return $Matches[1].Trim() }
    return ($line -split '\s+')[0]
}

Write-Host "=== Deploy Danielsson Insights to ${target} ==="

Invoke-Remote "mkdir -p $scriptsRemote/static $eventsRemote"

$scriptFiles = Get-ChildItem (Join-Path $repoRoot "scripts") -File -Filter "*.py" |
    Where-Object { $_.Name -notmatch '^test_' }
foreach ($f in $scriptFiles) {
    Write-Host "  -> scripts/$($f.Name)"
    Copy-File $f.FullName "$scriptsRemote/$($f.Name)"
}

$staticDir = Join-Path $repoRoot "scripts\static"
if (Test-Path $staticDir) {
    Get-ChildItem $staticDir -File | ForEach-Object {
        Write-Host "  -> static/$($_.Name)"
        Copy-File $_.FullName "$scriptsRemote/static/$($_.Name)"
    }
}

foreach ($name in @("timeline.jsonl", "metrics.jsonl")) {
    $local = Join-Path $repoRoot "events\$name"
    if (Test-Path $local) {
        Write-Host "  -> events/$name"
        Copy-File $local "$eventsRemote/$name"
    }
}

if ($UseIngressSecrets) {
    if (-not $AppSlug) { $AppSlug = Get-InsightsAppSlug }
    if (-not $AppSlug) {
        Write-Warning "Danielsson Insights add-on not installed yet — install from GitHub repo first, then re-run with -UseIngressSecrets"
        Write-Host "Repository URL (paste exactly): https://github.com/thomasdanielsson731/home-assistant-lab"
    } else {
        Write-Host "Setting Ingress URLs for app slug: $AppSlug"
        & (Join-Path $PSScriptRoot "set-ha-timeline-secret.ps1") `
            -TimelineUrl "/api/hassio_ingress/${AppSlug}/timeline" `
            -EnvironmentUrl "/api/hassio_ingress/${AppSlug}/environment"
    }
}

Write-Host "Done."
Write-Host "Add-on repo: https://github.com/thomasdanielsson731/home-assistant-lab (repository.yaml + danielsson_insights/ at repo root)"
