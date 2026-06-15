# Uptime Monitoring Runbook

Detect silent failures (bridges down, Insights offline, nattliga datagap) before they show up in empty graphs.

## Built-in heartbeats

`bridge_watchdog.py` (Danielsson Insights add-on) writes `_bridge/<service>` samples to `metrics.jsonl` every 60 s.

Check from dev PC:

```powershell
python scripts/health-check.py
```

Look for **Bridge heartbeats (add-on API)** — all services should show age &lt; 2 min.

Services monitored: `event_normalizer`, `air_quality_bridge`, `audio_bridge`, `aoa_bridge`, `influx_metrics_bridge`, `baseline_engine`.

## External uptime (recommended)

Run **Uptime Kuma** (Docker on dev PC or small Pi) with HTTP checks:

| Target | URL | Interval |
|---|---|---|
| Home Assistant | `http://192.168.68.175:8123` | 60 s |
| Danielsson Insights | `http://192.168.68.175:8765/timeline` | 60 s |
| Frigate | `http://192.168.68.175:5000` | 120 s |

Notify via Telegram or mobile push on 2 consecutive failures.

## Grafana / Influx

If Grafana panels go flat:

1. `python scripts/verify-influxdb.py`
2. Check Insights add-on logs: `ha apps logs 25d01a20_danielsson_insights`
3. Re-deploy: `.\scripts\deploy-insights-to-ha.ps1`

## Related

- [maintenance.md](maintenance.md)
- [timeline-addon.md](timeline-addon.md)
