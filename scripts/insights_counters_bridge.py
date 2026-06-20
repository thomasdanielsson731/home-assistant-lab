#!/usr/bin/env python3
"""Publish 24h Insights event counters to MQTT for HA dashboard chips."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from timeline_api import event_summary_stats, load_events  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent
EVENTS_PATH = Path(os.environ.get("EVENTS_PATH", REPO_ROOT / "events"))
TIMELINE_JSONL = EVENTS_PATH / "timeline.jsonl"
MQTT_HOST = os.environ.get("HA_HOST", "192.168.68.175")
INSIGHTS_API = os.environ.get(
    "INSIGHTS_API", f"http://127.0.0.1:8765/api/v1/events?hours=24"
)
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASS = os.environ["MQTT_PASS"]
POLL_INTERVAL = int(os.environ.get("INSIGHTS_COUNTERS_INTERVAL", "60"))

COUNTERS = (
    ("events", None),
    ("persons", "person"),
    ("arrivals", "arrival"),
    ("deliveries", "delivery"),
    ("bicycles", "bicycle"),
    ("anomalies", "anomaly"),
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("insights_counters")


def counts() -> dict[str, int]:
    for url in (
        INSIGHTS_API,
        f"http://127.0.0.1:8765/api/v1/events?hours=24",
        f"http://{MQTT_HOST}:8765/api/v1/events?hours=24",
    ):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            events = resp.json()
            if not isinstance(events, list):
                continue
            log.info("Counters from %s", url)
            stats = event_summary_stats(events)
            anomalies = sum(
                1 for e in events if (e.get("metadata") or {}).get("anomaly")
            )
            return {
                "events": len(events),
                "persons": stats.get("person", 0),
                "arrivals": stats.get("arrival", 0),
                "deliveries": stats.get("delivery", 0),
                "bicycles": stats.get("bicycle", 0),
                "anomalies": anomalies,
            }
        except (requests.RequestException, ValueError, TypeError):
            continue
    events = load_events(hours=24, timeline_path=TIMELINE_JSONL)
    stats = event_summary_stats(events)
    anomalies = sum(1 for e in events if (e.get("metadata") or {}).get("anomaly"))
    return {
        "events": len(events),
        "persons": stats.get("person", 0),
        "arrivals": stats.get("arrival", 0),
        "deliveries": stats.get("delivery", 0),
        "bicycles": stats.get("bicycle", 0),
        "anomalies": anomalies,
    }


def server_ok() -> bool:
    for url in (
        f"http://127.0.0.1:8765/health",
        f"http://{MQTT_HOST}:8765/health",
        f"http://127.0.0.1:8765/timeline",
        f"http://{MQTT_HOST}:8765/timeline",
    ):
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                return True
        except requests.RequestException:
            continue
    return False


def publish(client: mqtt.Client, values: dict[str, int]) -> None:
    for key, _ in COUNTERS:
        topic = f"danielsson/insights/{key}_24h"
        payload = str(values[key])
        client.publish(topic, payload, qos=0, retain=True)
        log.info("MQTT %s = %s", topic, payload)
    now = str(int(time.time()))
    client.publish("danielsson/insights/counters_bridge_ok", now, qos=0, retain=True)
    if server_ok():
        client.publish("danielsson/insights/server_ok", now, qos=0, retain=True)
        log.info("MQTT danielsson/insights/server_ok = %s", now)
    else:
        client.publish("danielsson/insights/server_ok", "", qos=0, retain=True)
        log.warning("Insights server not reachable on :8765")


def main() -> None:
    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_HOST, 1883, 60)
    client.loop_start()
    log.info("Insights counters bridge  mqtt=%s  interval=%ds", MQTT_HOST, POLL_INTERVAL)
    while True:
        try:
            publish(client, counts())
        except Exception as exc:
            log.error("counter publish failed: %s", exc)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
