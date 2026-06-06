# D6210 Air Quality Sensor — Integration Runbook

Integrate the Axis D6210 Air Quality Sensor into Home Assistant via a Python MQTT bridge.

## Hardware

| Attribute | Value |
|---|---|
| Model | Axis D6210 Air Quality Sensor |
| Zone | `driveway_env` — outdoor at driveway |
| Access | Via M2036 (`driveway_id`) VAPIX proxy at `192.168.68.204` |
| API | `/config/rest/airqualitymonitor/v1beta` (REST, polling, BETA) |

## Metrics

| Parameter | Unit | HA entity |
|---|---|---|
| Temperature | °C | `sensor.driveway_env_temperature` |
| Humidity | % | `sensor.driveway_env_humidity` |
| CO₂ | ppm | `sensor.driveway_env_co2` |
| VOC | ppb | `sensor.driveway_env_voc` (`device_class: volatile_organic_compounds_parts`) |
| NOx | ppb | `sensor.driveway_env_nox` |
| PM2.5 | µg/m³ | `sensor.driveway_env_pm2_5` |
| PM10 | µg/m³ | `sensor.driveway_env_pm10` |
| AQI | 0–500 | `sensor.driveway_env_aqi` |

Config: `config/home-assistant/mqtt_sensors/air_quality.yaml`

## Architecture

```
D6210 ──(I/O)── M2036 VAPIX proxy ──REST── air_quality_bridge.py ──MQTT── Mosquitto ── HA
```

The bridge runs on the **Windows dev PC** (not HAOS) because HAOS has no persistent process manager for custom scripts. Schedule via Windows Task Scheduler for 24/7 operation.

**Why not HA REST sensors?** The D6210 API requires POST with dynamic ISO8601 timestamps. A Python bridge is simpler and already working.

## Step 1 — Explore the API (optional)

```bash
curl -u homeassistant:<password> \
  "http://192.168.68.204/config/rest/airqualitymonitor/v1beta/sensors"
```

## Step 2 — Configure environment

Ensure `.env` on the dev PC contains:

```
HA_HOST=192.168.68.175
MQTT_USER=frigate
MQTT_PASS=<password>
CAM_USER=homeassistant
CAM_PASS=<password>
```

## Step 3 — Start the bridge

```bash
pip install requests paho-mqtt python-dotenv
python scripts/air_quality_bridge.py
```

The bridge polls every 60 s and publishes retained MQTT messages under `axis/driveway_env/air/<metric>`.

## Step 4 — Sync HA config

```powershell
.\scripts\sync-config.ps1
```

In HA: **Developer Tools → YAML → Reload all YAML configuration**.

## Step 5 — Verify

```bash
# MQTT messages arriving
mosquitto_sub -h 192.168.68.175 -u frigate -P <password> -t "axis/driveway_env/#" -v

# HA entities
# Developer Tools → States → filter "driveway_env"
```

Expected: 8 sensors with live values (may show "unknown" until D6210 calibration completes — up to 12 h for AQI).

## Step 6 — Schedule (production)

Create a Windows Task Scheduler entry:

- **Trigger:** At startup + restart on failure every 5 min
- **Action:** `python C:\dev\home-assistant-lab\scripts\air_quality_bridge.py`
- **Working directory:** `C:\dev\home-assistant-lab`

## Dashboard

When sensors are verified:

- **Home view:** Temperature + CO₂ mini-graph-card
- **Operations view:** Full air quality gauges and trends

See [dashboard-design.md](../dashboard-design.md).

## Troubleshooting

| Symptom | Check |
|---|---|
| No MQTT messages | Bridge running? `.env` credentials correct? M2036 reachable? |
| HA sensors unavailable | YAML synced? MQTT integration connected? Topic matches config? |
| Stale values | Bridge crashed — check Task Scheduler restart policy |
| AQI shows unknown | D6210 still calibrating (up to 12 h after power-on) |
