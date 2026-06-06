#!/usr/bin/env python3
"""Probe Axis cameras for Audio Analytics / SPL APIs."""
import os
import re
import json
import requests
from requests.auth import HTTPDigestAuth
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])

CAMERAS = [
    ("front", "192.168.68.200"),
    ("driveway_wide", "192.168.68.201"),
]

for zone, ip in CAMERAS:
    print(f"\n=== {zone} {ip} ===")
    for ep in ("/config/rest/openapi", "/config/rest/analytics-mqtt/v1/openapi"):
        try:
            r = requests.get(f"http://{ip}{ep}", auth=auth, timeout=8)
            if r.status_code == 200 and "audio" in r.text.lower():
                hits = set(re.findall(r"com\.axis\.[^\s\"']*audio[^\s\"']*", r.text, re.I))
                hits |= set(re.findall(r"[^\s\"']*AudioAnalytics[^\s\"']*", r.text))
                for h in sorted(hits)[:15]:
                    print(" ", h)
        except Exception as exc:
            print(ep, exc)

    # Try create SPL publisher guesses
    for key in (
        "com.axis.audio_analytics.sound_pressure_level.v1",
        "com.axis.audioanalytics.sound_pressure_level.v1",
        "com.axis.audio_analytics.spl.v1",
    ):
        body = {
            "data": {
                "id": f"{zone}_audio_spl",
                "data_source_key": key,
                "mqtt_topic": f"axis/{zone}/audio/spl",
                "qos": 0,
                "retain": True,
                "use_topic_prefix": False,
            }
        }
        r = requests.post(
            f"http://{ip}/config/rest/analytics-mqtt/v1/publishers",
            json=body,
            auth=auth,
            timeout=8,
        )
        if r.status_code in (200, 201):
            print(f"  CREATED publisher {key}:", r.text[:200])
        elif r.status_code != 404:
            print(f"  {key}:", r.status_code, r.text[:200])
