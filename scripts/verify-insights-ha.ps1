# verify-insights-ha.ps1 — Smoke-test Analytics/Environment on HAOS add-on
param(
    [string]$HaHost = "",
    [switch]$FixCloudflareUrls,
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
$sshPort = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$sshUser = if ($env:HA_USER) { $env:HA_USER } else { "root" }
$insightsHost = if ($env:INSIGHTS_HOSTNAME) { $env:INSIGHTS_HOSTNAME } else { "insights.danielsson.cloud" }

$directHealth = "http://${HA_HOST}:8765/health"
$directTimeline = "http://${HA_HOST}:8765/timeline"
$directEnv = "http://${HA_HOST}:8765/environment"
$cfTimeline = "https://${insightsHost}/timeline"
$cfEnv = "https://${insightsHost}/environment"

function Test-Url($label, $url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
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
$ok = (Test-Url "Add-on /health" $directHealth) -and $ok
$ok = (Test-Url "Direct Analytics" $directTimeline) -and $ok
$ok = (Test-Url "Direct Environment" $directEnv) -and $ok
$ok = (Test-Url "Cloudflare Analytics" $cfTimeline) -and $ok
$ok = (Test-Url "Cloudflare Environment" $cfEnv) -and $ok

$secretsLine = ssh -p $sshPort -o StrictHostKeyChecking=no "${sshUser}@${HA_HOST}" `
    "grep -E '^timeline_url:|^environment_url:' /config/secrets.yaml 2>/dev/null" 2>$null
$secretsBad = $false
if ($secretsLine) {
    Write-Host "`nsecrets.yaml:"
    $secretsLine | ForEach-Object { Write-Host "  $_" }
    if ($secretsLine -match 'hassio_ingress') {
        Write-Host '  FAIL  Ingress URLs in iframe return 401 - use Cloudflare URLs'
        $secretsBad = $true
        $ok = $false
    }
    if ($secretsLine -match 'http://192\.168\.|http://127\.0\.0\.1|:8765') {
        Write-Host '  WARN  LAN http URLs break remote HTTPS iframes - use Cloudflare'
        $secretsBad = $true
        $ok = $false
    }
    if ($secretsLine -notmatch 'insights\.danielsson\.cloud' -and -not $secretsBad) {
        Write-Host "  WARN  Expected insights.danielsson.cloud for iframe panels"
    }
} else {
    Write-Host "`n  WARN  Could not read secrets.yaml"
}

$addonState = ssh -p $sshPort -o StrictHostKeyChecking=no "${sshUser}@${HA_HOST}" `
    "ha apps info 25d01a20_danielsson_insights 2>/dev/null | grep '^state:'" 2>$null
if ($addonState) {
    Write-Host "`nAdd-on: $addonState"
    if ($addonState -notmatch 'started') { $ok = $false }
} else {
    Write-Host "`n  WARN  Danielsson Insights add-on not found"
    $ok = $false
}

if ($FixCloudflareUrls) {
    Write-Host "`nApplying Cloudflare iframe URLs..."
    & (Join-Path $PSScriptRoot "set-ha-timeline-secret.ps1") -UseCloudflareUrls
    Write-Host "Reload HA frontend (Ctrl+F5) after secrets change."
} elseif ($FixDirectUrls) {
    Write-Host "`nApplying LAN :8765 URLs (home network only)..."
    & (Join-Path $PSScriptRoot "set-ha-timeline-secret.ps1") -UseDirectUrls
    Write-Host "Reload HA frontend (Ctrl+F5) after secrets change."
}

if (-not $ok) {
    Write-Host "`nFix:"
    Write-Host "  .\scripts\verify-insights-ha.ps1 -FixCloudflareUrls"
    Write-Host "  ha apps restart 25d01a20_danielsson_insights  (on HA)"
    exit 1
}
Write-Host "`nAll checks passed."
exit 0
