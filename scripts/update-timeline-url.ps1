# update-timeline-url.ps1 — Set timeline_url to this PC's LAN IP (for HA iframe dashboard)
param(
    [string]$HostIp = ""
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

if (-not $HostIp) {
    $HostIp = $env:DEV_PC_HOST
}
if (-not $HostIp) {
    $HostIp = (
        Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {
            $_.IPAddress -like '192.168.*' -and
            $_.IPAddress -notlike '169.254.*' -and
            $_.PrefixOrigin -ne 'WellKnown'
        } |
        Select-Object -First 1
    ).IPAddress
}
if (-not $HostIp) {
    Write-Error "Could not detect LAN IP. Set DEV_PC_HOST in .env"
    exit 1
}

$timelineUrl = "http://${HostIp}:8765/timeline"
Write-Host "Timeline URL: $timelineUrl"

# Update HA secrets on host
& (Join-Path $PSScriptRoot "set-ha-timeline-secret.ps1") -TimelineUrl $timelineUrl
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Quick reachability test
try {
    $r = Invoke-WebRequest -Uri $timelineUrl -UseBasicParsing -TimeoutSec 5
    Write-Host "Local test: HTTP $($r.StatusCode)"
} catch {
    Write-Warning "Timeline not reachable at $timelineUrl — run start-bridges.ps1"
}

Write-Host 'Next: sync-config.ps1 then ha core restart on HA host'
