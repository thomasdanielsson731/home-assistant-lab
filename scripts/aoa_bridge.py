#!/usr/bin/env python3
"""
Axis AOA Occupancy → MQTT bridge.

Firmware 12.x does not support setEventPublicationConfig via VAPIX, and
configureEventPublication alone does not publish scenario events without
manual UI "Add condition" steps. This bridge polls getOccupancy every 5 s
and publishes to the MQTT topics expected by HA mqtt_binary_sensors/.

MQTT topics (retained):
  axis/<zone>/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active
  axis/<zone>/event/ObjectAnalytics/ScenarioOccupancy/VehicleOcc/Active

Run: python scripts/aoa_bridge.py
Requires: pip install requests paho-mqtt python-dotenv
"""

import json
import logging
import os
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")

CAMERAS = [
    {"zone": "front",         "ip": "192.168.68.200"},
    {"zone": "driveway_wide", "ip": "192.168.68.203"},
    {"zone": "driveway_id",   "ip": "192.168.68.204"},
    {"zone": "backyard",      "ip": "192.168.68.202"},
    {"zone": "storage_ext",   "ip": "192.168.68.205"},
    {"zone": "storage_int",   "ip": "192.168.68.206"},
]

SCENARIO_TOPICS = {
    "PersonOccupancy": ("ScenarioOccupancy", "PersonOccupancy/Active"),
    "VehicleOcc": ("ScenarioOccupancy", "VehicleOcc/Active"),
    "Loitering": ("ScenarioLoitering", "Loitering/Active"),
}

POLL_INTERVAL = 10

CAM_USER  = os.environ["CAM_USER"]
CAM_PASS  = os.environ["CAM_PASS"]
MQTT_HOST = os.environ.get("HA_HOST", "192.168.68.175")
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASS"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("aoa_bridge")


def aoa_request(ip: str, method: str, params: dict | None = None) -> dict:
    payload = {"apiVersion": "1.0", "method": method}
    if params:
        payload["params"] = params
    r = requests.post(
        f"http://{ip}/local/objectanalytics/control.cgi",
        json=payload,
        auth=HTTPDigestAuth(CAM_USER, CAM_PASS),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def get_scenarios(ip: str) -> dict[str, int]:
    cfg = aoa_request(ip, "getConfiguration")
    result = {}
    for s in cfg.get("data", {}).get("scenarios", []):
        name = s.get("name")
        if name in SCENARIO_TOPICS:
            result[name] = s["id"]
    return result


def get_active(ip: str, scenario_id: int, scenario_name: str) -> bool:
    data = aoa_request(ip, "getOccupancy", {"scenario": scenario_id})
    if data.get("error"):
        log.warning("%s scenario %s: %s", ip, scenario_name, data["error"])
        return False
    occ = data.get("data", {})
    if scenario_name == "PersonOccupancy":
        return int(occ.get("human", 0) or 0) > 0
    if scenario_name == "Loitering":
        return int(occ.get("total", 0) or 0) > 0
    return int(occ.get("total", 0) or 0) > 0


def publish(client: mqtt.Client, zone: str, scenario_name: str, active: bool) -> None:
    group, suffix = SCENARIO_TOPICS[scenario_name]
    topic = f"axis/{zone}/event/ObjectAnalytics/{group}/{suffix}"
    payload = json.dumps({"Data": {"active": active}})
    client.publish(topic, payload, qos=0, retain=True)
    log.info("%-14s %-18s  %s  -> %s", zone, scenario_name, "ON " if active else "off", topic)


def main() -> None:
    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_HOST, 1883, 60)
    client.loop_start()

    scenario_map: dict[str, dict[str, int]] = {}
    log.info("Starting AOA bridge  mqtt=%s  interval=%ds", MQTT_HOST, POLL_INTERVAL)

    while True:
        for cam in CAMERAS:
            zone, ip = cam["zone"], cam["ip"]
            try:
                if zone not in scenario_map:
                    scenario_map[zone] = get_scenarios(ip)
                    if not scenario_map[zone]:
                        log.warning("%s: no PersonOccupancy/VehicleOcc scenarios", zone)
                        continue

                for name, sid in scenario_map[zone].items():
                    active = get_active(ip, sid, name)
                    publish(client, zone, name, active)

            except requests.RequestException as exc:
                log.error("%s (%s): %s", zone, ip, exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
