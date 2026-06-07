#!/usr/bin/env python3
"""
Danielsson Home Intelligence — Energy Bridge (Phase 5).

Polls Kraftringen electricity and district heating APIs, publishes readings
to Mosquitto MQTT so the event_normalizer can pick them up as metric events.

MQTT topics published:
  danielsson/energy/electricity/w        — current power draw (W)
  danielsson/energy/electricity/kwh      — consumption today (kWh)
  danielsson/energy/heating/kwh          — district heating today (kWh)
  danielsson/energy/heating/return_c     — return temperature (°C)

Status: STUB — Kraftringen API credentials not yet available.
        Replace _fetch_electricity() and _fetch_heating() with real API calls
        once credentials are obtained. The rest of the pipeline is ready.

Run: python scripts/energy_bridge.py
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion

load_dotenv(Path(__file__).parent.parent / ".env")

MQTT_HOST = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")

# Kraftringen API — fill in once available
KRAFTRINGEN_USER = os.environ.get("KRAFTRINGEN_USER", "")
KRAFTRINGEN_PASS = os.environ.get("KRAFTRINGEN_PASS", "")
KRAFTRINGEN_METERING_POINT = os.environ.get("KRAFTRINGEN_METERING_POINT", "")

POLL_INTERVAL = 300  # 5 minutes

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("energy_bridge")


def _fetch_electricity() -> dict | None:
    """
    Fetch electricity data from Kraftringen API.

    TODO: Implement once API credentials are available.
    Expected return format:
      {"power_w": 2400.0, "kwh_today": 8.3, "kwh_month": 142.0, "cost_today_sek": 18.5}
    """
    # Stub — return None until API is configured
    if not KRAFTRINGEN_USER or not KRAFTRINGEN_PASS:
        return None

    # Real implementation goes here:
    # import requests
    # r = requests.get("https://api.kraftringen.se/v1/metering/...", auth=(KRAFTRINGEN_USER, KRAFTRINGEN_PASS))
    # data = r.json()
    # return {"power_w": data["currentPower"], "kwh_today": data["consumptionToday"], ...}
    return None


def _fetch_heating() -> dict | None:
    """
    Fetch district heating data from Kraftringen API.

    TODO: Implement once API credentials are available.
    Expected return format:
      {"kwh_today": 18.3, "return_temp_c": 42.1, "kwh_month": 380.0}
    """
    if not KRAFTRINGEN_USER or not KRAFTRINGEN_PASS:
        return None
    return None


def publish(client: mqtt.Client, topic: str, value: float | int) -> None:
    payload = json.dumps({"value": value, "timestamp": datetime.utcnow().isoformat() + "Z"})
    client.publish(topic, payload, qos=0, retain=True)
    log.debug("Published %s = %s", topic, value)


def poll_once(client: mqtt.Client) -> None:
    electricity = _fetch_electricity()
    if electricity:
        if "power_w" in electricity:
            publish(client, "danielsson/energy/electricity/w", electricity["power_w"])
        if "kwh_today" in electricity:
            publish(client, "danielsson/energy/electricity/kwh", electricity["kwh_today"])
        log.info("Electricity: %.0f W, %.2f kWh today", electricity.get("power_w", 0), electricity.get("kwh_today", 0))
    else:
        log.debug("Electricity data unavailable (API not configured)")

    heating = _fetch_heating()
    if heating:
        if "kwh_today" in heating:
            publish(client, "danielsson/energy/heating/kwh", heating["kwh_today"])
        if "return_temp_c" in heating:
            publish(client, "danielsson/energy/heating/return_c", heating["return_temp_c"])
        log.info("Heating: %.2f kWh today, %.1f°C return", heating.get("kwh_today", 0), heating.get("return_temp_c", 0))
    else:
        log.debug("Heating data unavailable (API not configured)")


def main() -> None:
    if not MQTT_USER or not MQTT_PASS:
        raise SystemExit("MQTT_USER and MQTT_PASS must be set in .env")

    if not KRAFTRINGEN_USER:
        log.warning(
            "KRAFTRINGEN_USER not set — energy bridge running in stub mode. "
            "Set KRAFTRINGEN_USER, KRAFTRINGEN_PASS, KRAFTRINGEN_METERING_POINT in .env "
            "and implement _fetch_electricity()/_fetch_heating() once API credentials are available."
        )

    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="energy_bridge")
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_HOST, 1883, 60)
    client.loop_start()

    log.info("Energy bridge started (poll every %ds)", POLL_INTERVAL)

    while True:
        try:
            poll_once(client)
        except Exception as exc:
            log.error("Poll error: %s", exc)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
