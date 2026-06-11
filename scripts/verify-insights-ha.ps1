# verify-insights-ha.ps1 — Smoke-test Analytics/Environment on HAOS add-on
param(
    [string]$HaHost = "",
    [switch]$FixDirectUrls
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
$directTimeline = "http://${HA_HOST}:8765/timeline"
$directEnv = "http://${HA_HOST}:8765/environment"

function Test-Url($label, $url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
        Write-Host "  OK    ${label} HTTP $($r.StatusCode)"
        return $true
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code) {
            Write-Host "  FAIL  ${label} HTTP $code"
        } else {
            Write-Host "  FAIL  ${label} $($_.Exception.Message)"
        }
        return $false
    }
}

Write-Host "=== Insights health ($HA_HOST) ===`n"
$ok = $true
$ok = (Test-Url "Direct Analytics" $directTimeline) -and $ok
$ok = (Test-Url "Direct Environment" $directEnv) -and $ok

$sshPort = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$sshUser = if ($env:HA_USER) { $env:HA_USER } else { "root" }
$secretsLine = ssh -p $sshPort -o StrictHostKeyChecking=no "${sshUser}@${HA_HOST}" `
    "grep -E '^timeline_url:|^environment_url:' /config/secrets.yaml 2>/dev/null" 2>$null
if ($secretsLine) {
    Write-Host "`nsecrets.yaml:"
    $secretsLine | ForEach-Object { Write-Host "  $_" }
    if ($secretsLine -match 'hassio_ingress') {
        Write-Host "  WARN  Ingress URLs in iframe often return 401 - use -FixDirectUrls"
        $ok = $false
    }
} else {
    Write-Host "`n  WARN  Could not read secrets.yaml"
}

$addonState = ssh -p $sshPort -o StrictHostKeyChecking=no "${sshUser}@${HA_HOST}" `
    "ha apps info 25d01a20_danielsson_insights 2>/dev/null | grep '^state:'" 2>$null
if ($addonState) {
    Write-Host "`nAdd-on: $addonState"
    if ($addonState -notmatch 'started') { $ok = $false }
}

if ($FixDirectUrls) {
    Write-Host "`nApplying direct URLs..."
    & (Join-Path $PSScriptRoot "set-ha-timeline-secret.ps1") -UseDirectUrls
    Write-Host "Reload HA frontend (Ctrl+F5) after secrets change."
}

if (-not $ok) {
    Write-Host "`nFix: .\scripts\verify-insights-ha.ps1 -FixDirectUrls"
    Write-Host "     ha apps restart 25d01a20_danielsson_insights  (on HA)"
    exit 1
}
Write-Host "`nAll checks passed."
exit 0
