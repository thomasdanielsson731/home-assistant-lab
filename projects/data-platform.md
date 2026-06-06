# Project: Data Platform

**Phase:** 7b · **Status:** In progress — bridge ready, InfluxDB add-on not deployed

## Goal

Time-series storage for trend analysis. Answer "what's normal?" and "what changed?" — not just "what's happening now?"

## Done Criteria

- [x] `influx_metrics_bridge.py` (metrics.jsonl → InfluxDB when `INFLUX_URL` set)
- [ ] InfluxDB add-on running on HAOS
- [ ] HA → InfluxDB integration with selective entity filter
- [ ] 30+ days of energy + environment + detection metrics stored
- [ ] At least one dashboard showing 7-day trends
- [ ] Event rate baseline computed for one zone

## Tasks

| # | Task | Status |
|---|---|---|
| 1 | Install InfluxDB add-on on HAOS | ⬜ |
| 2 | Set `INFLUX_URL` in dev PC `.env`; verify bridge | ⬜ |
| 3 | Add `influxdb:` block to `configuration.yaml` (HA sensors) | ⬜ |
| 4 | Filter: energy, driveway_env, detection entities | ⬜ |
| 5 | Verify data in InfluxDB UI | ⬜ |
| 6 | Add mini-graph-card trends to Operations view | ⬜ |
| 7 | After 2 weeks: compute hourly detection baseline | ⬜ |

## Key Files

- `scripts/influx_metrics_bridge.py` — metrics.jsonl exporter
- `docs/runbooks/influxdb-setup.md` — setup runbook
- `config/home-assistant/influxdb.yaml.example` — HA sensor integration sketch
- `config/home-assistant/dashboards/home-lab.yaml` — trend cards (future)

## References

- [integrations/data-platform/README.md](../integrations/data-platform/README.md)
- [agents/analyst.md](../agents/analyst.md)
