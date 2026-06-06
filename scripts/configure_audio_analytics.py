#!/usr/bin/env python3
"""
Verify AXIS Audio Analytics SPL plugin on cameras.

Audio Analytics is a firmware plugin (audioanalytics.cgi), not a separate ACAP.
SPL data reaches HA via MQTT action rules — see docs/runbooks/audio-analytics-setup.md

Usage:  python scripts/configure_audio_analytics.py
"""

import os
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

CAMERAS = [
    {"zone": "front", "ip": "192.168.68.200", "model": "P3288-LVE"},
    {"zone": "driveway_wide", "ip": "192.168.68.201", "model": "Q3558-LVE"},
    {"zone": "backyard", "ip": "192.168.68.203", "model": "Q1656-LE"},
]


def get_spl_settings(ip: str) -> dict | None:
    auth = HTTPDigestAuth(CAM_USER, CAM_PASS)
    r = requests.post(
        f"http://{ip}/axis-cgi/audioanalytics.cgi",
        json={"apiVersion": "1.0", "method": "getPluginsSettings", "params": {}},
        auth=auth,
        timeout=12,
    )
    if r.status_code != 200:
        return None
    data = r.json().get("data", {})
    for device in data.get("devices", []):
        for inp in device.get("inputs", []):
            for plugin in inp.get("plugins", []):
                if plugin.get("id") == "SoundPressureLevel":
                    return plugin.get("settings", {})
    return None


def main():
    print("AXIS Audio Analytics — SPL plugin status\n")
    all_ok = True
    for cam in CAMERAS:
        zone, ip, model = cam["zone"], cam["ip"], cam["model"]
        settings = get_spl_settings(ip)
        if not settings:
            print(f"  {zone:15} ({model})  FAIL — no SoundPressureLevel plugin")
            all_ok = False
            continue
        enabled = settings.get("enable", False)
        interval = settings.get("summaryEventInterval", "?")
        mark = "OK" if enabled else "OFF"
        print(f"  {zone:15} ({model})  {mark}  interval={interval}s  thresholds={settings.get('thresholdLower')}-{settings.get('thresholdUpper')} dB")
        if not enabled:
            all_ok = False

    print()
    if all_ok:
        print("Plugins OK. Next: MQTT action rules per camera (see docs/runbooks/audio-analytics-setup.md)")
    else:
        print("Enable Sound pressure level in Analytics → AXIS Audio analytics on each camera.")


if __name__ == "__main__":
    main()
