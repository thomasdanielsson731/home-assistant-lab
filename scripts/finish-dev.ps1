# finish-dev.ps1 - Synka allt till HAOS efter utveckling (inga flaggor)
#
#   .\scripts\finish-dev.ps1
#
# Gör: pytest -> commit+push (om dirty) -> sync -> deploy Insights -> omstart add-on
#      -> HA YAML/MQTT reload -> verify drift + Insights + health-check

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$logDir = Join-Path $repoRoot "logs"
$logFile = Join-Path $logDir "finish-dev.log"
$InsightsAddon = "25d01a20_danielsson_insights"

function Write-Log {
    param([string]$Text)
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

function Reload-HaYaml {
    param([string]$HostAddr, [string]$Token)
    if (-not $Token) {
        Write-Log "WARN: HA_TOKEN saknas i .env - hoppar YAML-reload"
        return
    }
    $headers = @{ Authorization = "Bearer $Token" }
    Invoke-RestMethod -Method POST `
        -Uri "http://${HostAddr}:8123/api/services/homeassistant/reload_core_config" `
        -Headers $headers -TimeoutSec 30 | Out-Null
    Write-Log "reload_core_config OK"

    $entries = Invoke-RestMethod -Method GET `
        -Uri "http://${HostAddr}:8123/api/config/config_entries/entry" `
        -Headers $headers -TimeoutSec 30
    $mqttEntry = ($entries | Where-Object { $_.domain -eq 'mqtt' } | Select-Object -First 1).entry_id
    if ($mqttEntry) {
        $body = @{ entry_id = $mqttEntry } | ConvertTo-Json
        Invoke-RestMethod -Method POST `
            -Uri "http://${HostAddr}:8123/api/services/homeassistant/reload_config_entry" `
            -Headers $headers -Body $body -ContentType "application/json" `
            -TimeoutSec 120 | Out-Null
        Write-Log "MQTT reload OK"
    }
}

Set-Location $repoRoot
Write-Log "=== finish-dev ==="

$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#=][^=]*)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

$HA_HOST = if ($env:HA_HOST) { $env:HA_HOST } else { "192.168.68.175" }
$HA_SSH_PORT = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$HA_USER = if ($env:HA_USER) { $env:HA_USER } else { "root" }
$sshTarget = "${HA_USER}@${HA_HOST}"
$sshOpts = @("-p", $HA_SSH_PORT, "-o", "StrictHostKeyChecking=no")

Write-Log "pytest ..."
python -m pytest
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }

$status = git status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) { throw "git status failed" }

$dirty = $status | Where-Object {
    $_ -notmatch '^\?\? .*\.env$' -and
    $_ -notmatch 'secrets\.yaml' -and
    $_ -notmatch '^\?\? logs/'
}

if ($dirty) {
    git add -A
    git reset HEAD -- .env 2>$null
    git reset HEAD -- config/home-assistant/secrets.yaml 2>$null
    $staged = git diff --cached --name-only
    if ($staged) {
        $msg = "chore: ship " + (Get-Date -Format "yyyy-MM-dd HH:mm")
        git commit -m $msg
        if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
        Write-Log "committed: $msg"
    }
} else {
    Write-Log "git clean"
}

git push origin HEAD
if ($LASTEXITCODE -ne 0) { throw "git push failed" }
Write-Log "pushed"

Write-Log "sync-config ..."
& "$PSScriptRoot\sync-config.ps1"
if ($LASTEXITCODE -ne 0) { throw "sync-config failed" }

Write-Log "deploy-insights ..."
& "$PSScriptRoot\deploy-insights-to-ha.ps1"
if ($LASTEXITCODE -ne 0) { throw "deploy-insights failed" }

Write-Log "restart Insights add-on ..."
ssh @sshOpts $sshTarget "ha apps restart $InsightsAddon"
if ($LASTEXITCODE -ne 0) { throw "add-on restart failed" }
Start-Sleep -Seconds 15

Write-Log "HA YAML reload ..."
Reload-HaYaml -HostAddr $HA_HOST -Token $env:HA_TOKEN

Write-Log "verify-ha-deploy ..."
& "$PSScriptRoot\verify-ha-deploy.ps1" -FailOnDrift
if ($LASTEXITCODE -ne 0) { throw "host config drift - sync failed?" }

Write-Log "verify-insights-ha ..."
& "$PSScriptRoot\verify-insights-ha.ps1"
if ($LASTEXITCODE -ne 0) { throw "Insights verify failed" }

Write-Log "health-check ..."
python "$PSScriptRoot\health-check.py"
if ($LASTEXITCODE -ne 0) { Write-Log "WARN: health-check reported issues" }

Write-Log "done - ladda om HA-klienten (Ctrl+F5)"
