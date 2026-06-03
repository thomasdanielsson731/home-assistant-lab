#!/usr/bin/env python3
"""
Axis D6210 Air Quality → MQTT bridge.

Polls the VAPIX Air Quality REST API (via M2036 proxy) every 60 s and
publishes the latest reading for each metric to Mosquitto.

MQTT topics:  axis/driveway_env/air/<metric>
Run manually: python scripts/air_quality_bridge.py
Run as service: add to Windows Task Scheduler or a systemd unit.

Requires: pip install requests paho-mqtt python-dotenv
"""

import os
import time
import logging
from pathlib import Path

import requests
from requests.auth import HTTPDigestAuth
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Config ────────────────────────────────────────────────────────────────────

CAMERA_IP   = "192.168.68.204"          # M2036 — proxies D6210 API
SENSOR_ID   = "0"
API_BASE    = f"http://{CAMERA_IP}/config/rest/airqualitymonitor/v1beta"
CAM_USER    = os.environ["CAM_USER"]
CAM_PASS    = os.environ["CAM_PASS"]

MQTT_HOST   = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_PORT   = 1883
MQTT_USER   = os.environ["MQTT_USER"]
MQTT_PASS   = os.environ["MQTT_PASS"]
MQTT_PREFIX = "axis/driveway_env/air"

POLL_INTERVAL = 60  # seconds

# Category → (mqtt_suffix, unit)
METRICS = {
    "TEMPERATURE": ("temperature", "°C"),
    "HUMIDITY":    ("humidity",    "%"),
    "CO2":         ("co2",         "ppm"),
    "VOC":         ("voc",         "ppb"),
    "NOX":         ("nox",         "ppb"),
    "PM2_5":       ("pm2_5",       "µg/m³"),
    "PM10_0":      ("pm10",        "µg/m³"),
    "AQI":         ("aqi",         ""),
}

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── VAPIX fetch ───────────────────────────────────────────────────────────────

def fetch_latest(category: str) -> float | None:
    now   = int(time.time())
    start = now - 180  # 3-minute window guarantees at least one reading
    url   = f"{API_BASE}/sensors/{SENSOR_ID}/getHistoryData"
    body  = {"data": {"category": category, "startTime": start, "endTime": now}}
    try:
        resp = requests.post(
            url,
            json=body,
            auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        measurements = data.get("measurement", [])
        if measurements:
            return measurements[-1]
    except Exception as exc:
        log.warning("Failed to fetch %s: %s", category, exc)
    return None

# ── MQTT ──────────────────────────────────────────────────────────────────────

def make_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="air_quality_bridge")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client

# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("Starting air quality bridge  camera=%s  mqtt=%s", CAMERA_IP, MQTT_HOST)
    mqttc = make_mqtt_client()

    while True:
        for category, (suffix, unit) in METRICS.items():
            value = fetch_latest(category)
            if value is not None:
                topic = f"{MQTT_PREFIX}/{suffix}"
                mqttc.publish(topic, str(value), retain=True)
                log.info("%-12s  %s %s  → %s", suffix, value, unit, topic)
            else:
                log.warning("%-12s  no data", suffix)

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
