# InfluxDB Setup Runbook

Phase 7b — long retention for continuous metrics (env, SPL).

## Architecture

```
event_normalizer.py → events/metrics.jsonl → influx_metrics_bridge.py → InfluxDB
HA influxdb integration (optional) → InfluxDB  ← sensor entities
```

**Production (2026-06-12):** `influx_metrics_bridge.py` runs inside the **Danielsson Insights add-on** when `influx_url` is configured. No dev PC needed.

---

## Option A — HAOS add-on bridge (recommended)

1. **InfluxDB add-on** on HAOS: `a0d7b954_influxdb` at `http://192.168.68.175:8086` (InfluxDB 1.8.x).
2. Verify auth + write: `python scripts/verify-influxdb.py`
3. Set Insights add-on options (on HA host):

   ```bash
   sh /share/danielsson-insights/scripts/set_insights_influx_options.sh homelab <password>
   ha apps restart 25d01a20_danielsson_insights
   ```

4. Check logs: `Wrote N metric rows to InfluxDB` (backfills from start of `metrics.jsonl`).

Add-on options:

| Option | Example |
|---|---|
| `influx_url` | `http://192.168.68.175:8086` |
| `influx_user` | `homelab` |
| `influx_password` | (from setup-influxdb.ps1) |
| `influx_db` | `home_lab` |
| `influx_v2` | `false` |

---

## Option B — Dev PC bridge (legacy)

Only if not using HAOS add-on. Add to `.env`:

```env
INFLUX_URL=http://192.168.68.175:8086
INFLUX_USER=homelab
INFLUX_PASSWORD=change-me
INFLUX_DB=home_lab
INFLUX_V2=false
```

Run `.\scripts\start-bridges.ps1` (legacy — platform is on HAOS).

---

## Initial InfluxDB setup

If database/user missing:

```powershell
.\scripts\setup-influxdb.ps1
```

Or on HA: `bash configure-influxdb-addon.sh` — disables auth for LAN (dev/lab only).

---

## Verify

```powershell
python scripts/health-check.py
python scripts/verify-influxdb.py
```

Query (InfluxQL):

```sql
SELECT COUNT(*) FROM home_metrics WHERE time > now() - 24h
```

---

## Retention

| Source | Measurement | Suggested retention |
|---|---|---|
| D6210 env bridge | `home_metrics` zone=`driveway_env` | 90 days |
| Audio SPL | `home_metrics` zone=`front` etc. | 30 days |
| HA sensors | `state` (HA integration) | 90 days |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Bridge idle | Set `influx_url` in add-on options |
| HTTP 401 | Run `verify-influxdb.py`; check user/password |
| No historical data | Bridge backfills on first successful write |
| health-check warns "not importable" | Fixed — uses importlib for `verify-influxdb.py` |

---

## Related

- [grafana-setup.md](grafana-setup.md)
- [timeline-addon.md](timeline-addon.md)
- [integrations/data-platform/README.md](../../integrations/data-platform/README.md)
