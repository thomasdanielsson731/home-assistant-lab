# start-bridges.ps1 — Start MQTT bridges (air quality, audio SPL, AOA) + event platform
# Add to Windows Startup folder if scheduled tasks fail:
#   shell:startup → shortcut to this script

$repoRoot = Split-Path $PSScriptRoot -Parent
$python   = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = "python" }

function Start-Bridge {
    param([string]$Name, [string]$Script)
    $scriptLeaf = Split-Path $Script -Leaf
    $running = Get-CimInstance Win32_Process |
        Where-Object { $_.CommandLine -like "*$scriptLeaf*" }
    if ($running) {
        Write-Host "$Name already running (pid $($running.ProcessId))"
        return
    }
    Start-Process -FilePath $python -ArgumentList $Script -WorkingDirectory $repoRoot -WindowStyle Hidden
    Write-Host "Started $Name"
}

Start-Bridge "AirQualityBridge"  "$repoRoot\scripts\air_quality_bridge.py"
Start-Bridge "AudioBridge"       "$repoRoot\scripts\audio_bridge.py"
Start-Bridge "AOABridge"         "$repoRoot\scripts\aoa_bridge.py"
Start-Bridge "EventNormalizer"   "$repoRoot\scripts\event_normalizer.py"
Start-Bridge "TimelineServer"    "$repoRoot\scripts\timeline_server.py"
Start-Bridge "InfluxBridge"      "$repoRoot\scripts\influx_metrics_bridge.py"
