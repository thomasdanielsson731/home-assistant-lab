# Grafana Setup Runbook

7-day trend dashboards for environment (D6210) and audio SPL metrics stored in InfluxDB.

## Architecture

```
influx_metrics_bridge.py → InfluxDB (home_lab.home_metrics)
Grafana add-on (a0d7b954_grafana) → reads /share/grafana/provisioning/
```

Dashboard: **Home Lab — 7 Day Trends** (`uid: homelab-metrics-7d`)

Panels: outdoor temp/humidity/CO₂/AQI/PM, SPL (front, driveway_wide, backyard).

---

## One-time deploy

From dev PC (reads `INFLUX_*` from `.env`):

```powershell
.\scripts\deploy-grafana.ps1
```

This:

1. Copies dashboard JSON + provisioning YAML to `/share/grafana/` on HAOS
2. Writes InfluxDB datasource (internal URL `http://a0d7b954-influxdb:8086`)
3. Sets Grafana add-on env var `GF_PATHS_PROVISIONING` (SQLite stays in add-on; share is read-only for DB)
4. Restarts Grafana add-on

---

## Access

- HA sidebar → **Grafana** → folder **Home Lab** → **Home Lab — 7 Day Trends**
- Default time range: last 7 days (refresh every 5 min)

Login (if prompted): user `admin`, password `hassio` (HA Grafana add-on default).

---

## Re-deploy after dashboard changes

Edit `config/grafana/dashboards/home-metrics-7d.json`, then:

```powershell
.\scripts\deploy-grafana.ps1
```

Grafana reloads provisioned dashboards within ~30 s.

---

## Legacy dev PC bridges

Remove autostart if still present:

```powershell
.\scripts\remove-bridges-startup.ps1
```

Platform runs on **Danielsson Insights add-on** — do not run `start-bridges.ps1`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| No datasource | Re-run `deploy-grafana.ps1`; check Grafana add-on logs |
| Empty panels | Verify Influx data: `python scripts/verify-influxdb.py` |
| 403 on internal API | Normal — use HA sidebar Ingress, not raw port |
| Password changed | Update `.env` `INFLUX_PASSWORD` and re-run deploy |

---

## Related

- [influxdb-setup.md](influxdb-setup.md)
- [timeline-addon.md](timeline-addon.md)
