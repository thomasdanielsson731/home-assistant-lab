#!/usr/bin/env python3
"""List analytics-mqtt data sources and try SPL publisher keys."""
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth

load_dotenv(Path(__file__).parent.parent / ".env")
auth = HTTPDigestAuth(os.environ["CAM_USER"], os.environ["CAM_PASS"])

IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.68.201"
ZONE = sys.argv[2] if len(sys.argv) > 2 else "driveway_wide"

base = f"http://{IP}"

for path in (
    "/config/rest/analytics-mqtt/v1/openapi",
    "/config/rest/analytics-mqtt/v1/data-sources",
    "/config/rest/analytics-mqtt/v1/publishers",
):
    r = requests.get(f"{base}{path}", auth=auth, timeout=12)
    print(f"\n=== GET {path} -> {r.status_code} ===")
    if not r.ok:
        print(r.text[:400])
        continue
    try:
        data = r.json()
    except Exception:
        print(r.text[:2000])
        continue
    text = json.dumps(data)
    if "audio" in text.lower() or "sound" in text.lower():
        for m in sorted(set(re.findall(r"com\.axis\.[^\s\"']+", text))):
            if re.search(r"audio|sound|spl", m, re.I):
                print(" ", m)
    if path.endswith("publishers"):
        print(json.dumps(data, indent=2)[:2500])
    elif path.endswith("data-sources"):
        keys = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(keys, list):
            for item in keys:
                k = item.get("key") or item.get("data_source_key") or item
                if isinstance(k, str) and re.search(r"audio|sound|spl", k, re.I):
                    print(" ", k)

# Try #1 suffix keys from existing scene publishers pattern
candidates = [
    "com.axis.audio_analytics.sound_pressure_level.v1#1",
    "com.axis.audio_analytics.sound_pressure_level.v1#0",
    "com.axis.audio_analytics.sound_pressure_level#1",
]
for key in candidates:
    body = {
        "data": {
            "id": f"{ZONE}_audio_spl_probe",
            "data_source_key": key,
            "mqtt_topic": f"axis/{ZONE}/audio/spl",
            "qos": 0,
            "retain": True,
            "use_topic_prefix": False,
        }
    }
    r = requests.post(
        f"{base}/config/rest/analytics-mqtt/v1/publishers",
        json=body,
        auth=auth,
        timeout=12,
    )
    print(f"\nPOST {key} -> {r.status_code}")
    print(r.text[:300])
