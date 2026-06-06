#!/usr/bin/env python3
"""Probe MQTT topics for 10 seconds."""
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

load_dotenv(Path(__file__).parent.parent / ".env")
HOST = os.environ.get("HA_HOST", "192.168.68.175")
USER = os.environ["MQTT_USER"]
PASS = os.environ["MQTT_PASS"]

TOPICS = [
    "axis/front/event/ObjectAnalytics/ScenarioOccupancy/PersonOccupancy/Active",
    "axis/front/scene/frame",
    "axis/driveway_env/air/temperature",
]

seen = {}

def on_message(client, userdata, msg):
    seen[msg.topic] = msg.payload.decode("utf-8", errors="replace")[:120]
    print(f"  {msg.topic}: {seen[msg.topic]}")

client = mqtt.Client(CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.on_message = on_message
client.connect(HOST, 1883, 60)
for t in TOPICS:
    client.subscribe(t)
    client.subscribe(t.replace("PersonOccupancy", "VehicleOcc"))

print(f"Listening 15s on {HOST} ...")
client.loop_start()
time.sleep(15)
client.loop_stop()

print("\nSummary:")
for t in TOPICS:
    print(f"  {'OK' if t in seen else 'NO DATA':6}  {t}")
