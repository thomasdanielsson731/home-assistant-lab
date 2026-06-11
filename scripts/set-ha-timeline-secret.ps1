# set-ha-timeline-secret.ps1 — Safely set timeline_url in HA secrets.yaml
param(
    [string]$TimelineUrl = "",
    [string]$EnvironmentUrl = "",
    [switch]$UseDirectUrls
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

$host_ = if ($env:HA_HOST) { $env:HA_HOST } else { "192.168.68.175" }
$port  = if ($env:HA_SSH_PORT) { $env:HA_SSH_PORT } else { "22222" }
$user  = if ($env:HA_USER) { $env:HA_USER } else { "root" }
$target = "${user}@${host_}"
$ssh = @("-p", $port, "-o", "StrictHostKeyChecking=no")

if (-not $TimelineUrl) {
    if ($UseDirectUrls -or $env:HA_HOST) {
        $haHost = if ($env:HA_HOST) { $env:HA_HOST } else { "192.168.68.175" }
        $TimelineUrl = "http://${haHost}:8765/timeline"
    } else {
        $detected = (
            Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { $_.IPAddress -like '192.168.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
            Select-Object -First 1
        ).IPAddress
        if (-not $detected) { Write-Error "Set -TimelineUrl, -UseDirectUrls, or DEV_PC_HOST in .env"; exit 1 }
        $TimelineUrl = "http://${detected}:8765/timeline"
    }
}
if (-not $EnvironmentUrl) {
    if ($TimelineUrl -match '^(https?://[^/]+)') {
        $EnvironmentUrl = "$($Matches[1])/environment"
    } else {
        $EnvironmentUrl = "http://192.168.68.136:8765/environment"
    }
}
Write-Host "Setting timeline_url on HA host: $TimelineUrl"
Write-Host "Setting environment_url on HA host: $EnvironmentUrl"

$cmd = @"
grep -v 'House Intelligence' /config/secrets.yaml | grep -v '^timeline_url:' | grep -v '^environment_url:' | sed -e '\${'$'}/^\$/d' > /tmp/secrets_fix.yaml
printf '\n# House Intelligence (Analytics / Environment iframe)\ntimeline_url: "%s"\nenvironment_url: "%s"\n' '$TimelineUrl' '$EnvironmentUrl' >> /tmp/secrets_fix.yaml
mv /tmp/secrets_fix.yaml /config/secrets.yaml
tail -4 /config/secrets.yaml
ha core check
"@

ssh @ssh $target $cmd
