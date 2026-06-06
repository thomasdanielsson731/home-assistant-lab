#!/usr/bin/env python3
"""Try MQTT event filters for SoundPressureLevel Summary."""
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion, Client
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])
IP = "192.168.68.201"
HOST = os.environ.get("HA_HOST", "192.168.68.175")

FILTERS = [
    "tnsaxis:SoundPressureLevel",
    "tns1:RuleEngine/tnsaxis:SoundPressureLevel",
    "tnsaxis:SoundPressureLevel/Summary",
    "tns1:RuleEngine/tnsaxis:SoundPressureLevel/tnsaxis:Summary",
    "RuleEngine/tnsaxis:SoundPressureLevel//.",
    "#",
]

base_filters = [
    {"topicFilter": "tns1:Analytics/tnsaxis:ObjectAnalytics/ScenarioOccupancy", "qos": 0, "retain": "none"},
]

for f in FILTERS:
    flist = base_filters + [{"topicFilter": f, "qos": 0, "retain": "none"}]
    requests.post(
        f"http://{IP}/axis-cgi/mqtt/event.cgi",
        json={
            "apiVersion": "1.2",
            "method": "configureEventPublication",
            "params": {
                "topicPrefix": "default",
                "customTopicPrefix": "",
                "appendEventTopic": True,
                "includeTopicNamespaces": False,
                "includeSerialNumberInPayload": False,
                "eventFilterList": flist,
            },
        },
        auth=auth,
        timeout=10,
    )
    seen = []

    def on_message(_c, _u, m):
        if "SoundPressure" in m.topic or "sound" in m.topic.lower():
            seen.append((m.topic, m.payload.decode()[:200]))

    client = Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(os.environ["MQTT_USER"], os.environ["MQTT_PASS"])
    client.on_message = on_message
    client.connect(HOST, 1883, 60)
    client.subscribe("axis/driveway_wide/event/#")
    client.loop_start()
    time.sleep(65)
    client.loop_stop()
    print(f"filter={f!r} -> {len(seen)} hits")
    for t, p in seen[:3]:
        print(f"  {t}: {p}")
