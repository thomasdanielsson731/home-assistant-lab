# Project: Energy Insights

**Phase:** 7 · **Status:** Planned (blocked on data platform)

## Goal

Understand electricity consumption patterns. Answer: "When do we use most? What drives cost?"

## Prerequisites

- Energy meter or utility integration in HA
- InfluxDB storing energy metrics (see [data-platform.md](data-platform.md))
- 2+ weeks of data for baseline

## Done Criteria

- [ ] Energy sensor(s) identified and ingested to InfluxDB
- [ ] Daily and weekly consumption visible in dashboard
- [ ] Peak hours identified (morning/evening patterns)
- [ ] Correlation with occupancy (empty house vs occupied)
- [ ] (Stretch) Cost estimate if tariff data available

## Tasks

| # | Task | Status |
|---|---|---|
| 1 | Audit existing energy entities in HA | ⬜ |
| 2 | Add energy entities to InfluxDB filter | ⬜ |
| 3 | Create daily consumption mini-graph-card | ⬜ |
| 4 | Template sensor: today's consumption vs 7-day average | ⬜ |
| 5 | Weekly summary (manual or agent-generated) | ⬜ |

## References

- [integrations/data-platform/README.md](../integrations/data-platform/README.md)
- [agents/analyst.md](../agents/analyst.md)
