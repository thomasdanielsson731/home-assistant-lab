# InfluxDB Setup Runbook

Phase 7-10 — long retention for continuous metrics (env, SPL).

## Architecture

```
event_normalizer.py → events/metrics.jsonl → influx_metrics_bridge.py → InfluxDB
HA influxdb integration (optional) → InfluxDB  ← sensor entities
```

Event platform metrics (`co2`, `temperature`, `spl`, etc.) are written to `metrics.jsonl` today. The bridge tails that file and exports to InfluxDB when configured.

## Option A — InfluxDB add-on on HAOS (recommended)

**Status (2026-06-07):** Add-on `a0d7b954_influxdb` v5.0.2 installed and running on `http://192.168.68.175:8086` (InfluxDB 1.8.x).

1. **Settings → Add-ons → InfluxDB → Configuration** — set **Authentication** to `false` (home lab LAN), **SSL** to `false`, Save, Restart add-on  
   *(Or create user/database in Chronograf: Open Web UI → database `home_lab`, user `homelab` with read/write.)*
2. On dev PC: `.\scripts\setup-influxdb.ps1` — writes `INFLUX_*` to `.env`
3. `.\scripts\start-bridges.ps1` — restarts `influx_metrics_bridge.py`
4. Optional: HA integration — copy from `config/home-assistant/influxdb.yaml.example`

## Option B — Dev PC bridge only

Add to `.env` on Windows dev PC:

```env
INFLUX_URL=http://192.168.68.175:8086
INFLUX_TOKEN=your-write-token
INFLUX_ORG=home
INFLUX_BUCKET=home_lab
INFLUX_MEASUREMENT=home_metrics
INFLUX_V2=true
```

Restart bridges:

```powershell
.\scripts\start-bridges.ps1
```

The bridge starts with other services. Without `INFLUX_URL` it stays idle (metrics remain in `metrics.jsonl`).

## Verify

```powershell
python scripts/health-check.py
```

Look for `InfluxDB: OK` when configured.

Query in InfluxDB UI (Data Explorer):

```flux
from(bucket: "home_lab")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "home_metrics")
```

## Retention

| Source | Measurement | Suggested retention |
|---|---|---|
| D6210 env bridge | `home_metrics` zone=`driveway_env` | 90 days |
| Audio SPL | `home_metrics` zone=`front` etc. | 30 days |
| HA sensors | `state` (HA integration) | 90 days |

Set bucket retention in InfluxDB add-on configuration.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Bridge idle | Set `INFLUX_URL` in `.env` |
| HTTP 401 | Check `INFLUX_TOKEN` write permission |
| No historical data | Bridge backfills from start of `metrics.jsonl` on first successful write |
| Duplicate points | Normal — Influx treats same timestamp+tags as overwrite |

## Related

- [integrations/data-platform/README.md](../../integrations/data-platform/README.md)
- [config/home-assistant/influxdb.yaml.example](../../config/home-assistant/influxdb.yaml.example)
