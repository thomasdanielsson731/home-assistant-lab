# Data Platform Integration

Phase 7 design — time-series storage and insight dashboards.

## Goal

Move from live-state monitoring to **trend analysis and baselines**:

- "When do we use most electricity?"
- "How does outdoor AQI correlate with indoor CO₂?"
- "What's the normal person-detection rate at `front` on weekdays?"

## Architecture

```
Sources                    Storage              Presentation
─────────                  ───────              ────────────
HA state changes    ──┐
Frigate events      ──┤
Axis MQTT metrics   ──┼──►  InfluxDB  ──►  Grafana / HA history cards
Energy meter        ──┤     (30+ days)
Air quality bridge  ──┘
```

## Recommended Stack

| Component | Option A (simple) | Option B (flexible) |
|---|---|---|
| Time-series DB | InfluxDB add-on on HAOS | InfluxDB on dev PC |
| HA integration | `influxdb` integration in `configuration.yaml` | Same |
| Dashboards | HA `mini-graph-card` + history | Grafana on dev PC |
| Event export | HA `logbook` + MQTT recorder | Custom Python exporter |

**Recommendation:** Start with Option A — InfluxDB HA add-on + `mini-graph-card`. Add Grafana later if needed.

## Metrics to Ingest (Priority Order)

| Priority | Metric | Source entity | Why |
|---|---|---|---|
| 1 | Energy consumption | `sensor.*_energy` or utility meter | Cost insight |
| 2 | Outdoor temperature + AQI | `sensor.driveway_env_*` | Environment correlation |
| 3 | Person detection count | Frigate event rate per zone | Activity baseline |
| 4 | Indoor temperature/humidity | Room climate sensors | Comfort patterns |
| 5 | Presence state | Person entities | Occupancy patterns |

## Retention Policy

| Data type | Retention | Rationale |
|---|---|---|
| High-frequency metrics (temp, energy) | 90 days | Trend analysis |
| Event counts (detections/hour) | 30 days | Baseline establishment |
| Raw MQTT events | 7 days | Debug only — not stored long-term |
| Frigate recordings | 7 days | Already configured on SSD |

## HA Configuration Sketch

```yaml
# configuration.yaml (future — not yet deployed)
influxdb:
  host: localhost
  port: 8086
  database: home_lab
  tags:
    source: hass
  tags_attributes:
    - friendly_name
  default_measurement: state
  include:
    domains:
      - sensor
      - binary_sensor
    entities:
      - sensor.driveway_env_temperature
      - sensor.driveway_env_co2
      - sensor.driveway_env_aqi
      # expand as needed
```

## Anomaly Detection (Phase 6 overlap)

Once 2+ weeks of data exist:

1. Compute hourly event rate per zone (person detections)
2. Build baseline: mean + 2σ per (zone, hour-of-day, day-of-week)
3. Alert when current rate exceeds baseline

Implementation options:
- HA template sensor + automation (simple)
- Python script on dev PC querying InfluxDB (flexible)
- LLM agent generating weekly summary (Phase 8)

## Next Steps

1. Install InfluxDB add-on on HAOS
2. Set `INFLUX_URL`, `INFLUX_TOKEN` in dev PC `.env` — `influx_metrics_bridge.py` tails `metrics.jsonl`
3. Add `influxdb:` block to `configuration.yaml` with selective entity filter (HA sensors)
4. Verify data flowing: InfluxDB UI → query `home_metrics` measurement
5. Add `mini-graph-card` trends to Operations dashboard
6. After 2 weeks: compute first baseline

See [docs/runbooks/influxdb-setup.md](../../docs/runbooks/influxdb-setup.md).

## Related

- [integrations/ai/README.md](../ai/README.md) — LLM and anomaly detection
- [projects/data-platform.md](../../projects/data-platform.md) — sub-project brief
- [docs/roadmap.md](../../docs/roadmap.md) — Phase 7 tasks
