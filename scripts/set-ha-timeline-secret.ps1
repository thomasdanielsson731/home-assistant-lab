# set-ha-timeline-secret.ps1 — Safely set Insights URLs in HA secrets.yaml
param(
    [string]$TimelineUrl = "",
    [string]$EnvironmentUrl = "",
    [string]$EventsUrl = "",
    [string]$StoryUrl = "",
    [switch]$UseDirectUrls,
    [switch]$UseIngressUrls,
    [switch]$UseCloudflareUrls,
    [switch]$UseHybridUrls,
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

if ($UseHybridUrls) {
    $insightsHost = if ($InsightsHost) { $InsightsHost } elseif ($env:INSIGHTS_HOSTNAME) { $env:INSIGHTS_HOSTNAME } else { "insights.danielsson.cloud" }
    $cfBase = "https://${insightsHost}"
    $TimelineExternalUrl = "${cfBase}/timeline"
    $EnvironmentExternalUrl = "${cfBase}/environment"
    $EventsExternalUrl = "${cfBase}/"
    $StoryExternalUrl = "${cfBase}/story"
    $ingressBase = Get-InsightsIngressBase
    if ($ingressBase) {
        $TimelineUrl = "${ingressBase}/timeline"
        $EnvironmentUrl = "${ingressBase}/environment"
        $EventsUrl = "${ingressBase}/"
        $StoryUrl = "${ingressBase}/story"
        Write-Host "Hybrid: Ingress in-app + Cloudflare external"
    } else {
        Write-Warning 'Ingress unavailable - using Cloudflare for both primary and external URLs'
        $TimelineUrl = $TimelineExternalUrl
        $EnvironmentUrl = $EnvironmentExternalUrl
        $EventsUrl = $EventsExternalUrl
        $StoryUrl = $StoryExternalUrl
        $TimelineExternalUrl = $TimelineUrl
        $EnvironmentExternalUrl = $EnvironmentUrl
        $EventsExternalUrl = $EventsUrl
        $StoryExternalUrl = $StoryUrl
    }
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
        Write-Error 'Set -UseHybridUrls, -UseCloudflareUrls, -UseDirectUrls, -UseIngressUrls, or pass -TimelineUrl'
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

if ($UseHybridUrls -and -not $TimelineExternalUrl) {
    $TimelineExternalUrl = $TimelineUrl
    $EnvironmentExternalUrl = $EnvironmentUrl
    $EventsExternalUrl = $EventsUrl
    $StoryExternalUrl = $StoryUrl
}
if (-not $TimelineExternalUrl) {
    $TimelineExternalUrl = $TimelineUrl
    $EnvironmentExternalUrl = $EnvironmentUrl
    $EventsExternalUrl = $EventsUrl
    $StoryExternalUrl = $StoryUrl
}

Write-Host "Setting timeline_url on HA host: $TimelineUrl"
Write-Host "Setting environment_url on HA host: $EnvironmentUrl"
Write-Host "Setting events_url on HA host: $EventsUrl"
Write-Host "Setting story_url on HA host: $StoryUrl"
if ($TimelineExternalUrl) {
    Write-Host "Setting timeline_external_url on HA host: $TimelineExternalUrl"
    Write-Host "Setting environment_external_url on HA host: $EnvironmentExternalUrl"
    Write-Host "Setting events_external_url on HA host: $EventsExternalUrl"
    Write-Host "Setting story_external_url on HA host: $StoryExternalUrl"
}

$blockPath = Join-Path $env:TEMP "insights-secrets-block.yaml"
$blockLines = @(
    "",
    "# House Intelligence (Analytics / Environment / Events - Ingress in-app, Cloudflare external)",
    ('timeline_url: "{0}"' -f $TimelineUrl),
    ('environment_url: "{0}"' -f $EnvironmentUrl),
    ('events_url: "{0}"' -f $EventsUrl),
    ('story_url: "{0}"' -f $StoryUrl)
)
if ($TimelineExternalUrl) {
    $blockLines += @(
        ('timeline_external_url: "{0}"' -f $TimelineExternalUrl),
        ('environment_external_url: "{0}"' -f $EnvironmentExternalUrl),
        ('events_external_url: "{0}"' -f $EventsExternalUrl),
        ('story_external_url: "{0}"' -f $StoryExternalUrl)
    )
}
$blockLines | Set-Content -Path $blockPath -Encoding utf8

$remoteDest = "$target`:/tmp/insights-secrets-block.yaml"
scp @("-P", $port, "-o", "StrictHostKeyChecking=no") $blockPath $remoteDest | Out-Null

$remoteCmd = @'
grep -v '# House Intelligence' /config/secrets.yaml \
  | grep -v '^timeline_url:' \
  | grep -v '^environment_url:' \
  | grep -v '^events_url:' \
  | grep -v '^story_url:' \
  | grep -v '^timeline_external_url:' \
  | grep -v '^environment_external_url:' \
  | grep -v '^events_external_url:' \
  | grep -v '^story_external_url:' \
  | sed '/^$/d' > /tmp/secrets_fix.yaml
cat /tmp/insights-secrets-block.yaml >> /tmp/secrets_fix.yaml
mv /tmp/secrets_fix.yaml /config/secrets.yaml
tail -12 /config/secrets.yaml
ha core check
'@

ssh @ssh $target $remoteCmd
