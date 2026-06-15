# stop-bridges.ps1 — Stop dev PC bridges (Analytics now on HAOS)

$scripts = @(
    "air_quality_bridge.py",
    "audio_bridge.py",
    "aoa_bridge.py",
    "energy_bridge.py",
    "event_normalizer.py",
    "timeline_server.py",
    "influx_metrics_bridge.py",
    "bridge_watchdog.py"
)

$stopped = 0
foreach ($leaf in $scripts) {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$leaf*" } |
        ForEach-Object {
            Write-Host "Stopping $leaf (pid $($_.ProcessId))"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $stopped++
        }
}

if ($stopped -eq 0) {
    Write-Host "No bridge processes were running."
} else {
    Write-Host "Stopped $stopped bridge process(es)."
}
