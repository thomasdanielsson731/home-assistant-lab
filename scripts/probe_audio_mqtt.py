#!/usr/bin/env python3
"""Probe MQTT and VAPIX for AXIS Audio Analytics SPL on cameras."""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from paho.mqtt.client import CallbackAPIVersion, Client
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])
HOST = os.environ.get("HA_HOST", "192.168.68.175")

CAMERAS = [
    ("front", "192.168.68.200"),
    ("driveway_wide", "192.168.68.201"),
    ("backyard", "192.168.68.203"),
]

ENDPOINTS = [
    "/axis-cgi/applications/list.cgi",
    "/local/audioanalytics/",
    "/local/audioanalytics/control.cgi",
    "/config/rest/analytics-mqtt/v1/data_sources",
]

seen: dict[str, str] = {}


def on_message(_client, _userdata, msg):
    payload = msg.payload.decode("utf-8", errors="replace")[:200]
    seen[msg.topic] = payload
    if any(x in msg.topic.lower() for x in ("audio", "sound", "spl")):
        print(f"MQTT {msg.topic}: {payload}")


def vapix_get(ip: str, path: str):
    try:
        r = requests.get(f"http://{ip}{path}", auth=auth, timeout=8)
        return r.status_code, r.text[:500]
    except Exception as exc:
        return 0, str(exc)


def vapix_post(ip: str, path: str, payload: dict):
    try:
        r = requests.post(f"http://{ip}{path}", json=payload, auth=auth, timeout=8)
        return r.status_code, r.text[:500]
    except Exception as exc:
        return 0, str(exc)


def main():
    print("=== VAPIX / ACAP probe ===")
    for zone, ip in CAMERAS:
        print(f"\n--- {zone} {ip} ---")
        code, text = vapix_get(ip, "/axis-cgi/applications/list.cgi")
        if code == 200 and "audio" in text.lower():
            for line in text.splitlines():
                if "audio" in line.lower():
                    print("  app:", line.strip()[:120])
        for ep in ENDPOINTS:
            code, text = vapix_get(ip, ep)
            if code == 200 and ("audio" in text.lower() or "spl" in text.lower()):
                print(f"  {ep} [{code}]: {text[:300]}")
        # try audio analytics control API
        for method in ("getConfiguration", "getStatus", "getSoundPressureLevel"):
            code, text = vapix_post(
                ip,
                "/local/audioanalytics/control.cgi",
                {"apiVersion": "1.0", "method": method},
            )
            if code == 200 and "error" not in text.lower()[:80]:
                print(f"  control.{method}: {text[:250]}")

        # MQTT event publication filters
        code, text = vapix_post(
            ip,
            "/axis-cgi/mqtt/event.cgi",
            {"apiVersion": "1.2", "method": "getEventPublicationConfig"},
        )
        if code == 200 and "audio" in text.lower():
            print(f"  mqtt events (audio): {text[:400]}")

    print("\n=== MQTT subscribe 20s axis/# (audio-related) ===")
    client = Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(os.environ["MQTT_USER"], os.environ["MQTT_PASS"])
    client.on_message = on_message
    client.connect(HOST, 1883, 60)
    client.subscribe("axis/#")
    client.loop_start()
    time.sleep(20)
    client.loop_stop()

    audio_topics = [t for t in seen if any(x in t.lower() for x in ("audio", "sound", "spl"))]
    print(f"\nAudio-related topics: {len(audio_topics)}")
    for t in sorted(audio_topics):
        print(f"  {t}: {seen[t][:120]}")

    if not audio_topics:
        print("  (none — SPL may need analytics-mqtt publisher or event filter config)")


if __name__ == "__main__":
    main()
