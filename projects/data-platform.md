# Project: Data Platform

**Phase:** 7b · **Status:** Done — bridge live in add-on; Grafana/trends optional

## Goal

Time-series storage for trend analysis. Answer "what's normal?" and "what changed?" — not just "what's happening now?"

## Done Criteria

- [x] `influx_metrics_bridge.py` (metrics.jsonl → InfluxDB)
- [x] InfluxDB add-on running on HAOS (`a0d7b954_influxdb`, `home_lab` DB)
- [x] Bridge runs in Danielsson Insights add-on v0.2.4+ (`influx_url` option)
- [ ] HA → InfluxDB integration with selective entity filter (optional)
- [ ] 30+ days of energy + environment + detection metrics stored (accumulating)
- [ ] At least one dashboard showing 7-day trends (Grafana or HA cards)
- [ ] Event rate baseline computed for one zone

## Tasks

| # | Task | Status |
|---|---|---|
| 1 | Install InfluxDB add-on on HAOS | ✅ |
| 2 | Configure add-on `influx_url` via `set_insights_influx_options.sh` | ✅ |
| 3 | Add `influxdb:` block to `configuration.yaml` (HA sensors) | ⬜ optional |
| 4 | Filter: energy, driveway_env, detection entities | ⬜ |
| 5 | Verify data in InfluxDB UI | ✅ bridge writing |
| 6 | Add mini-graph-card trends to Operations view | ⬜ |
| 7 | After 2 weeks: compute hourly detection baseline | ⬜ |

## Key Files

- `scripts/influx_metrics_bridge.py` — metrics.jsonl exporter
- `scripts/set_insights_influx_options.sh` — configure add-on options on HAOS
- `docs/runbooks/influxdb-setup.md` — setup runbook
- `config/home-assistant/influxdb.yaml.example` — HA sensor integration sketch
- `config/home-assistant/dashboards/home-lab.yaml` — trend cards (future)

## References

- [integrations/data-platform/README.md](../integrations/data-platform/README.md)
- [agents/analyst.md](../agents/analyst.md)
