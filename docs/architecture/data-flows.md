# Data Flows

Per-integration paths into the Danielsson event platform. All flows converge on `events/timeline.jsonl` and `events/metrics.jsonl` on HAOS (`/share/danielsson-insights/events/`).

> Face recognition and family Companion presence removed — [ADR-006](../decisions/006-no-face-no-companion-presence.md).

## Frigate → timeline

```
Axis RTSP → Frigate detect/record → MQTT frigate/events → event_normalizer.py → timeline.jsonl
                                                      ↘ HA Frigate integration (entities)
```

Event types: `person`, `vehicle`, `bicycle` (+ enriched `arrival`, `delivery` via correlation engine).

## Axis analytics → timeline + metrics

```
Camera VAPIX / MQTT → Mosquitto axis/<zone>/…
  ├─ AOA occupancy     → aoa_bridge (poll) + MQTT → normalizer → occupancy events
  ├─ scene/frame/track → MQTT → normalizer → scene + behavior events
  ├─ audio SPL         → audio_bridge (WebSocket) → metrics.jsonl (spl)
  └─ D6210 air quality → air_quality_bridge (REST via M2036 proxy) → MQTT + metrics
```

## HA / Zigbee → timeline + metrics

```
ZHA smoke alarm MQTT state → normalizer → smoke events
ZHA temp sensor MQTT       → normalizer → metrics (temperature per room)
Yale lock (future)         → normalizer → door events
```

Outdoor activity uses camera analytics templates (`binary_sensor.house_outdoor_presence`) — not phone presence.

## Metrics retention

```
metrics.jsonl → influx_metrics_bridge.py → InfluxDB home_metrics → Grafana 7-day dashboard
             → baseline_engine.py → aggregates/baselines.json + anomaly insight events
```

## Story + AI (optional)

```
timeline.jsonl → story_engine.py → events/stories/<date>.json
              → Ollama (OLLAMA_URL) → ai_summary field when configured
timeline_server :8765 → /api/v1/* + /timeline + /environment UI
```

## Dashboard consumption

| Consumer | Source |
|---|---|
| Hem / Kameror / Säkerhet / Rum | HA entities (MQTT, ZHA, Frigate, templates) |
| Händelser (`home-events.yaml`) | Insights add-on `:8765/` (iframe, Cloudflare or LAN) |
| Teknik Live | HA entities + `sensor.insights_*_24h` (REST → Insights API) |
| Teknik Historik | HA recorder / statistics |
| Teknik Drift | HA entities + add-on health |
| Analytics / Environment | Insights add-on `:8765` (`insights.danielsson.cloud` or LAN) |
| Grafana | InfluxDB |
