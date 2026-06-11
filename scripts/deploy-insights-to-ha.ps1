# deploy-insights-to-ha.ps1 — Sync scripts + events to HA share and install local add-on
param(
    [switch]$SkipAddon,
    [switch]$UseIngressSecrets,
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
    if ($DryRun) { Write-Host "[dry-run] ssh $cmd"; return }
    ssh @sshOpts $target $cmd
}

function Copy-File($local, $remote) {
    if ($DryRun) { Write-Host "[dry-run] scp $local -> $remote"; return }
    scp @scpOpts $local "${target}:${remote}" | Out-Null
}

Write-Host "=== Deploy Danielsson Insights to ${target} ==="

Invoke-Remote "mkdir -p $scriptsRemote/static $eventsRemote"

# Scripts (runtime only)
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

# Events (preserve existing on host if larger — append-only sync of jsonl tails optional)
foreach ($name in @("timeline.jsonl", "metrics.jsonl")) {
    $local = Join-Path $repoRoot "events\$name"
    if (Test-Path $local) {
        Write-Host "  -> events/$name"
        Copy-File $local "$eventsRemote/$name"
    }
}

if (-not $SkipAddon) {
    Write-Host "Deploying add-on to /addons/danielsson_insights ..."
    Invoke-Remote "mkdir -p /addons/danielsson_insights"
    $addonDir = Join-Path $repoRoot "addons\danielsson_insights"
    Get-ChildItem $addonDir -File | ForEach-Object {
        Write-Host "  -> addons/danielsson_insights/$($_.Name)"
        Copy-File $_.FullName "/addons/danielsson_insights/$($_.Name)"
    }
    Copy-File (Join-Path $repoRoot "addons\repository.yaml") "/addons/repository.yaml"

    Write-Host "Supervisor: reload + install local add-on ..."
    Invoke-Remote "ha addons reload 2>/dev/null || true"
    Invoke-Remote "ha addons install local_danielsson_insights 2>/dev/null || ha addons start local_danielsson_insights 2>/dev/null || true"
}

if ($UseIngressSecrets) {
    Write-Host "Setting Ingress URLs in secrets.yaml ..."
    & (Join-Path $PSScriptRoot "set-ha-timeline-secret.ps1") `
        -TimelineUrl "/api/hassio_ingress/local_danielsson_insights/timeline" `
        -EnvironmentUrl "/api/hassio_ingress/local_danielsson_insights/environment"
}

Write-Host "Done. Start add-on in Supervisor if not auto-started."
