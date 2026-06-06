#!/usr/bin/env python3
"""Listen for any axis/front/event/# messages."""
import os, time
from pathlib import Path
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

load_dotenv(Path(__file__).parent.parent / ".env")
HOST = os.environ.get("HA_HOST", "192.168.68.175")

def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode('utf-8','replace')[:200]}")

c = mqtt.Client(CallbackAPIVersion.VERSION2)
c.username_pw_set(os.environ["MQTT_USER"], os.environ["MQTT_PASS"])
c.on_message = on_message
c.connect(HOST, 1883, 60)
c.subscribe("axis/+/event/#")
c.subscribe("axis/+/scene/#")
print(f"Listening 20s on axis/+/event/# and scene/# ...")
c.loop_start()
time.sleep(20)
c.loop_stop()
