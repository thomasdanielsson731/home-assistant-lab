# Project: Data Platform

**Phase:** 7 · **Status:** Planned (blocked on Phase 5 stability)

## Goal

Time-series storage for trend analysis. Answer "what's normal?" and "what changed?" — not just "what's happening now?"

## Done Criteria

- [ ] InfluxDB running (HA add-on or external)
- [ ] HA → InfluxDB integration with selective entity filter
- [ ] 30+ days of energy + environment + detection metrics stored
- [ ] At least one dashboard showing 7-day trends
- [ ] Event rate baseline computed for one zone

## Tasks

| # | Task | Status |
|---|---|---|
| 1 | Install InfluxDB add-on on HAOS | ⬜ |
| 2 | Add `influxdb:` block to `configuration.yaml` | ⬜ |
| 3 | Filter: energy, driveway_env, detection entities | ⬜ |
| 4 | Verify data in InfluxDB UI | ⬜ |
| 5 | Add mini-graph-card trends to Operations view | ⬜ |
| 6 | After 2 weeks: compute hourly detection baseline | ⬜ |

## Key Files (future)

- `config/home-assistant/configuration.yaml` — influxdb block
- `config/home-assistant/dashboards/home-lab.yaml` — trend cards

## References

- [integrations/data-platform/README.md](../integrations/data-platform/README.md)
- [agents/analyst.md](../agents/analyst.md)
