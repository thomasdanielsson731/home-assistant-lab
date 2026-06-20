#!/usr/bin/env pwsh
# verify-ha-deploy.ps1 — Detect repo vs HA host config drift (dashboard YAML)
param(
    [string]$HaHost = "",
    [switch]$FailOnDrift
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

$HA_HOST = if ($HaHost) { $HaHost } elseif ($env:HA_HOST) { $env:HA_HOST } else { "192.168.68.175" }
$sshPort = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$sshUser = if ($env:HA_USER) { $env:HA_USER } else { "root" }
$target = "${sshUser}@${HA_HOST}"
$ssh = @("-p", $sshPort, "-o", "StrictHostKeyChecking=no")

$files = @(
    "home-events.yaml",
    "house-timeline.yaml",
    "house-graphs.yaml",
    "home-tech.yaml"
)

Write-Host "=== HA deploy parity ($HA_HOST) ===`n"
$drift = $false

foreach ($name in $files) {
    $local = Join-Path $repoRoot "config\home-assistant\dashboards\$name"
    if (-not (Test-Path $local)) {
        Write-Host "  SKIP  $name (missing locally)"
        continue
    }
    $localLines = (Get-Content $local).Count
    $remoteLines = ssh @ssh $target "wc -l < /config/dashboards/$name 2>/dev/null || echo 0"
    $remoteLines = [int]($remoteLines.Trim())
    $marker = ""
    if ($name -eq "home-events.yaml") { $marker = "insights_server_ok" }
    elseif ($name -eq "house-graphs.yaml") { $marker = "grafana_url" }
    elseif ($name -eq "home-tech.yaml") { $marker = "fit_mode" }
    else { $marker = "insights_server_ok" }

    $localHas = (Select-String -Path $local -Pattern $marker -Quiet)
    if ($name -eq "home-tech.yaml") {
        $ok = ($localLines -eq $remoteLines) -and $localHas
    } else {
        $remoteHasRaw = ssh @ssh $target "grep -c '$marker' /config/dashboards/$name 2>/dev/null || echo 0"
        $remoteHas = [int](($remoteHasRaw | Out-String).Trim().Split("`n")[0])
        $ok = ($localLines -eq $remoteLines) -and ($localHas -eq ($remoteHas -gt 0))
    }
    if (-not $ok) {
        $drift = $true
        if ($name -eq "home-tech.yaml") {
            Write-Host "  DRIFT  $name - local $localLines lines, host $remoteLines lines; marker $marker local=$localHas"
        } else {
            Write-Host "  DRIFT  $name - local $localLines lines, host $remoteLines lines; marker $marker local=$localHas host=$($remoteHas -gt 0)"
        }
    } else {
        Write-Host "  OK     $name - $localLines lines, marker $marker"
    }
}

if ($drift) {
    Write-Host "`nFix: .\scripts\sync-config.ps1"
    if ($FailOnDrift) { exit 1 }
    exit 1
}
Write-Host "`nHost dashboards match repo."
exit 0
