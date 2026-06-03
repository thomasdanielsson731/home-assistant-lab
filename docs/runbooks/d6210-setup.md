# D6210 Air Quality Sensor — Integration Runbook

Integrera Axis D6210 Air Quality Sensor i Home Assistant via VAPIX REST API.

## Hårdvara

- **Modell**: Axis D6210 Air Quality Sensor (luftkvalitet — ej radar)
- **Zon**: `driveway_env` — utomhus vid uppfart
- **Åtkomst**: Via M2036 (driveway_id) som VAPIX-proxy på `192.168.68.204`
- **API**: `/config/rest/airqualitymonitor/v1beta` (REST, polling, BETA)

## Mätvärden

| Parameter | Enhet | Noteringar |
|---|---|---|
| Temperatur | °C | |
| Relativ fuktighet | % | |
| CO₂ | ppm | 0–40 000; 2 dagars kalibrering |
| VOC | ppb | max 500; 1 h kalibrering |
| NOx | ppb | max 500; 6 h kalibrering |
| PM1.0 / PM2.5 / PM4.0 / PM10.0 | µg/m³ | |
| AQI (Air Quality Index) | 0–500 | 12 h kalibrering |
| Rök/vaping | binär event | |

## Steg 1 — Utforska API:et

Kör mot M2036 för att se vilka sensorer som finns och JSON-strukturen:

```bash
# Lista sensorer och connection status
curl -u homeassistant:<lösenord> \
  "http://192.168.68.204/config/rest/airqualitymonitor/v1beta/sensors"

# Hämta historikdata för senaste minuten (ersätt <sensorId> med id från ovan)
curl -u homeassistant:<lösenord> \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"category":"all","startTime":"<ISO8601-1min-ago>","endTime":"<ISO8601-now>"}' \
  "http://192.168.68.204/config/rest/airqualitymonitor/v1beta/sensors/<sensorId>/getHistoryData"
```

Notera `sensorId` och exakt fältnamn för varje mätvärde i JSON-svaret.

## Steg 2 — HA REST-sensorer

HA integreras via `rest:` i `configuration.yaml` (polling, inte MQTT). Lägg till:

```yaml
rest:
  - resource: "http://192.168.68.204/config/rest/airqualitymonitor/v1beta/sensors/<sensorId>/getHistoryData"
    method: POST
    payload: '{"category":"all","startTime":"{{ (now() - timedelta(minutes=2)).isoformat() }}","endTime":"{{ now().isoformat() }}"}'
    headers:
      Content-Type: application/json
    authentication: basic
    username: !secret driveway_id_camera_user
    password: !secret driveway_id_camera_password
    scan_interval: 60
    sensor:
      - name: "driveway_env temperature"
        unique_id: "driveway_env_temperature"
        value_template: "{{ value_json.data.measurement.temperature[-1] }}"
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
      # ... fler sensorer baserat på faktisk JSON-struktur
```

> **OBS**: Exakt JSON-path bekräftas i Steg 1 — fältnamn och struktur kan variera.

## Steg 3 — Secrets

Lägg till i `/config/secrets.yaml` på hosten om de saknas:

```yaml
driveway_id_camera_user: homeassistant
driveway_id_camera_password: <lösenord>
```

## Steg 4 — Dashboard

När sensorer är verifierade, lägg till:
- **Home-vy**: Temperatur + CO₂ mini-graph-card
- **Ny "Miljö"-flik**: Fullständigt luftkvalitetsdashboard med gauges och trendgrafer

Se `docs/dashboard-design.md` för layoutspecifikation (uppdateras när sensorer är klara).

## Verify

```bash
# Verifiera att HA plockat upp sensorerna
ha core logs --lines 100 | grep driveway_env
```

Förväntat: inga fel, och entiteter synliga i HA Developer Tools → States.
