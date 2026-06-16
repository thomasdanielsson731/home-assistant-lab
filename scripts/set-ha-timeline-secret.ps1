# set-ha-timeline-secret.ps1 — Safely set Insights URLs in HA secrets.yaml
param(
    [string]$TimelineUrl = "",
    [string]$EnvironmentUrl = "",
    [string]$EventsUrl = "",
    [string]$StoryUrl = "",
    [switch]$UseDirectUrls,
    [switch]$UseIngressUrls,
    [switch]$UseCloudflareUrls,
    [string]$InsightsHost = ""
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

function Get-InsightsIngressBase {
    $line = ssh @ssh $target "ha apps info 25d01a20_danielsson_insights 2>/dev/null | grep '^ingress_entry:'"
    if ($line -match 'ingress_entry:\s*(/api/hassio_ingress/\S+)') {
        return $Matches[1].Trim()
    }
    return ""
}

if ($UseCloudflareUrls -and -not $TimelineUrl) {
    $insightsHost = if ($InsightsHost) { $InsightsHost } elseif ($env:INSIGHTS_HOSTNAME) { $env:INSIGHTS_HOSTNAME } else { "insights.danielsson.cloud" }
    $base = "https://${insightsHost}"
    $TimelineUrl = "${base}/timeline"
    $EnvironmentUrl = "${base}/environment"
    $EventsUrl = "${base}/"
    $StoryUrl = "${base}/story"
}

if ($UseIngressUrls -and -not $TimelineUrl) {
    $ingressBase = Get-InsightsIngressBase
    if (-not $ingressBase) {
        Write-Error "Danielsson Insights add-on not running - start it before -UseIngressUrls"
        exit 1
    }
    $TimelineUrl = "${ingressBase}/timeline"
    $EnvironmentUrl = "${ingressBase}/environment"
    $EventsUrl = "${ingressBase}/"
    $StoryUrl = "${ingressBase}/story"
}

if (-not $TimelineUrl) {
    if ($UseDirectUrls) {
        $TimelineUrl = "http://${host_}:8765/timeline"
    } else {
        Write-Error "Set -UseCloudflareUrls, -UseDirectUrls (LAN only), -UseIngressUrls (401 in iframe), or pass -TimelineUrl"
        exit 1
    }
}
if (-not $EnvironmentUrl) {
    if ($TimelineUrl -match '^(/api/hassio_ingress/\S+)/timeline$') {
        $EnvironmentUrl = "$($Matches[1])/environment"
    } elseif ($TimelineUrl -match '^(https?://[^/]+)/timeline$') {
        $EnvironmentUrl = "$($Matches[1])/environment"
    } else {
        $EnvironmentUrl = "http://${host_}:8765/environment"
    }
}
if (-not $EventsUrl) {
    if ($TimelineUrl -match '^(/api/hassio_ingress/\S+)/timeline$') {
        $EventsUrl = "$($Matches[1])/"
    } elseif ($TimelineUrl -match '^(https?://[^/]+)/timeline$') {
        $EventsUrl = "$($Matches[1])/"
    } else {
        $EventsUrl = "http://${host_}:8765/"
    }
}
if (-not $StoryUrl) {
    if ($TimelineUrl -match '^(/api/hassio_ingress/\S+)/timeline$') {
        $StoryUrl = "$($Matches[1])/story"
    } elseif ($TimelineUrl -match '^(https?://[^/]+)/timeline$') {
        $StoryUrl = "$($Matches[1])/story"
    } else {
        $StoryUrl = "http://${host_}:8765/story"
    }
}

Write-Host "Setting timeline_url on HA host: $TimelineUrl"
Write-Host "Setting environment_url on HA host: $EnvironmentUrl"
Write-Host "Setting events_url on HA host: $EventsUrl"
Write-Host "Setting story_url on HA host: $StoryUrl"

$blockPath = Join-Path $env:TEMP "insights-secrets-block.yaml"
@(
    "",
    "# House Intelligence (Analytics / Environment / Events iframe)",
    ('timeline_url: "{0}"' -f $TimelineUrl),
    ('environment_url: "{0}"' -f $EnvironmentUrl),
    ('events_url: "{0}"' -f $EventsUrl),
    ('story_url: "{0}"' -f $StoryUrl)
) | Set-Content -Path $blockPath -Encoding utf8

$remoteDest = "$target`:/tmp/insights-secrets-block.yaml"
scp @("-P", $port, "-o", "StrictHostKeyChecking=no") $blockPath $remoteDest | Out-Null

$remoteCmd = @'
grep -v '# House Intelligence' /config/secrets.yaml \
  | grep -v '^timeline_url:' \
  | grep -v '^environment_url:' \
  | grep -v '^events_url:' \
  | grep -v '^story_url:' \
  | sed '/^$/d' > /tmp/secrets_fix.yaml
cat /tmp/insights-secrets-block.yaml >> /tmp/secrets_fix.yaml
mv /tmp/secrets_fix.yaml /config/secrets.yaml
tail -6 /config/secrets.yaml
ha core check
'@

ssh @ssh $target $remoteCmd
