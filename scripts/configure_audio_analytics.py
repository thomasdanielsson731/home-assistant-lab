#!/usr/bin/env python3
"""
Configure AXIS Audio Analytics SPL MQTT publisher on cameras.

Requires AXIS Audio Analytics ACAP installed (Analytics > AXIS Audio analytics).
Lists data_sources via analytics-mqtt API and creates publisher when audio key exists.

Usage:  python scripts/configure_audio_analytics.py
"""

import os
import re
import sys
from pathlib import Path

import requests
from requests.auth import HTTPDigestAuth

_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if _line.strip() and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())


def _require(key):
    v = os.environ.get(key)
    if not v:
        sys.exit(f"ERROR: {key} not set — add it to .env")
    return v


CAM_USER = _require("CAM_USER")
CAM_PASS = _require("CAM_PASS")

# SPL via analytics-mqtt — Q3558 has microphone; front P3288 may follow later
TARGETS = [
    {"zone": "driveway_wide", "ip": "192.168.68.201"},
    {"zone": "front", "ip": "192.168.68.200"},
]

AUDIO_KEY_RE = re.compile(r"audio|sound|spl", re.I)


def list_data_sources(ip):
    auth = HTTPDigestAuth(CAM_USER, CAM_PASS)
    r = requests.get(
        f"http://{ip}/config/rest/analytics-mqtt/v1/data_sources",
        auth=auth,
        timeout=12,
    )
    if r.status_code != 200:
        return None, r.text[:200]
    data = r.json().get("data", [])
    if isinstance(data, dict):
        data = data.get("data_sources", [])
    keys = [d.get("key", d) if isinstance(d, dict) else d for d in data]
    return keys, None


def list_publishers(ip):
    auth = HTTPDigestAuth(CAM_USER, CAM_PASS)
    r = requests.get(
        f"http://{ip}/config/rest/analytics-mqtt/v1/publishers",
        auth=auth,
        timeout=12,
    )
    if r.status_code != 200:
        return []
    return r.json().get("data", [])


def create_publisher(ip, zone, data_source_key):
    auth = HTTPDigestAuth(CAM_USER, CAM_PASS)
    body = {
        "data": {
            "id": f"{zone}_audio_spl",
            "data_source_key": data_source_key,
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
        timeout=12,
    )
    return r.status_code, r.text[:300]


def pick_audio_key(keys):
    for key in keys:
        if AUDIO_KEY_RE.search(str(key)):
            return key
    return None


def main():
    ok = True
    for cam in TARGETS:
        zone, ip = cam["zone"], cam["ip"]
        print(f"\n{'=' * 50}")
        print(f"{zone} ({ip})")

        keys, err = list_data_sources(ip)
        if keys is None:
            print(f"  FAIL list data_sources: {err}")
            ok = False
            continue

        audio_key = pick_audio_key(keys)
        if not audio_key:
            print("  SKIP — no audio analytics data source (install AXIS Audio Analytics ACAP)")
            print(f"  Available: {', '.join(keys)}")
            ok = False
            continue

        existing = list_publishers(ip)
        topic = f"axis/{zone}/audio/spl"
        if any(p.get("mqtt_topic") == topic for p in existing):
            print(f"  OK publisher already exists -> {topic}")
            continue

        code, text = create_publisher(ip, zone, audio_key)
        if code in (200, 201):
            print(f"  OK created publisher {audio_key} -> {topic}")
        else:
            print(f"  FAIL create publisher ({code}): {text}")
            ok = False

    print(f"\n{'Done' if ok else 'Some cameras need AXIS Audio Analytics ACAP first'}")


if __name__ == "__main__":
    main()
