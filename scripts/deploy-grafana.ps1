# deploy-grafana.ps1 — Sync Grafana dashboards to HA share and provision add-on
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
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
$sshOpts = @("-p", $HA_SSH_PORT, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no")
$scpOpts = @("-P", $HA_SSH_PORT, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no")

$influxUser = if ($env:INFLUX_USER) { $env:INFLUX_USER } else { "homelab" }
$influxPass = $env:INFLUX_PASSWORD
if (-not $influxPass) { throw "INFLUX_PASSWORD not set in .env" }

$remoteRoot = "/share/grafana"
$localGrafana = Join-Path $repoRoot "config\grafana"

function Invoke-Remote($cmd) {
    if ($DryRun) { Write-Host "[dry-run] ssh $cmd"; return "" }
    ssh @sshOpts $target $cmd
}

function Copy-File($local, $remote) {
    if ($DryRun) { Write-Host "[dry-run] scp $local -> $remote"; return }
    scp @scpOpts $local "${target}:${remote}" | Out-Null
}

Write-Host "Deploying Grafana config to ${target}:${remoteRoot} ..."

Invoke-Remote "mkdir -p ${remoteRoot}/provisioning/dashboards ${remoteRoot}/provisioning/datasources ${remoteRoot}/dashboards ${remoteRoot}/data"

Copy-File (Join-Path $localGrafana "provisioning\dashboards\default.yaml") "${remoteRoot}/provisioning/dashboards/default.yaml"
Copy-File (Join-Path $localGrafana "dashboards\home-metrics-7d.json") "${remoteRoot}/dashboards/home-metrics-7d.json"
Copy-File (Join-Path $repoRoot "scripts\setup_grafana.sh") "/share/danielsson-insights/scripts/setup_grafana.sh"

Write-Host "Running setup_grafana.sh ..."
Invoke-Remote "chmod +x /share/danielsson-insights/scripts/setup_grafana.sh; sh /share/danielsson-insights/scripts/setup_grafana.sh '$influxUser' '$influxPass'"

Write-Host "Done. Open HA sidebar -> Grafana -> Home Lab -> 7 Day Trends dashboard"
