# HACS Frontend Cards Runbook

Required custom Lovelace cards for the Home Lab dashboard.

## Installed Cards

| Card | HACS name | Resource URL | Used in |
|---|---|---|---|
| Mushroom Cards | Mushroom | `/hacsfiles/lovelace-mushroom/...` | All views |
| Advanced Camera Card | Advanced Camera Card | `/hacsfiles/advanced-camera-card/...` | Cameras |
| Built-in graphs | — | `history-graph` + `statistics-graph` | Insights → env graphs (no HACS needed) |

Resources are declared in `configuration.yaml` under `lovelace: resources:` (synced from repo).

## Environment graphs (Insights)

Uses **built-in** Lovelace cards — no custom resource required:

| Section | Card type | Config |
|---|---|---|
| LAST 7 DAYS | `history-graph` | `hours_to_show: 168` |
| LAST 90 DAYS | `statistics-graph` | `days_to_show: 90`, `period: day`, `stat_types: [mean]` |

Requires `state_class: measurement` on MQTT sensors (see `mqtt_sensors/air_quality.yaml`) and `recorder.purge_keep_days: 90`.

## Verify

1. Open **Home Lab → Insights**
2. **LAST 7 DAYS** — five line charts with today's data
3. **LAST 90 DAYS** — daily averages (fills in over time)

## Troubleshooting

| Symptom | Fix |
|---|---|
| Empty 7-day graphs | Confirm `air_quality_bridge.py` running; check **History** tab on sensor entity |
| Empty 90-day graphs | Statistics need ~24 h of data; wait or check **Developer Tools → Statistics** |
| Stale dashboard | Ctrl+F5 after sync |
