# install-mini-graph-card.ps1 — Deploy mini-graph-card bundle to HAOS via SSH
#
# Usage: .\scripts\install-mini-graph-card.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$envFile  = Join-Path $repoRoot ".env"

if (-not (Test-Path $envFile)) {
    Write-Error ".env missing — copy .env.example and set HA_HOST"
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}

$host_ = $env:HA_HOST
$port  = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$script = (Join-Path $repoRoot "scripts\install-mini-graph-card.sh") -replace '\\', '/'

scp -P $port $script "root@${host_}:/tmp/install-mini-graph-card.sh"
ssh -p $port "root@${host_}" "bash /tmp/install-mini-graph-card.sh"
Write-Host "Done. Sync configuration.yaml and reload HA YAML."
