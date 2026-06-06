#!/usr/bin/env python3
"""Lab health check — cameras, env sensors, bridges, events. No manual steps."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

HA_HOST = os.environ.get("HA_HOST", "192.168.68.175")
HA_TOKEN = os.environ.get("HA_TOKEN")
if not HA_TOKEN:
    sys.exit("HA_TOKEN not set in .env")

HEADERS = {"Authorization": f"Bearer {HA_TOKEN}"}
BASE = f"http://{HA_HOST}:8123/api"

CAMERAS = [
    "camera.front",
    "camera.driveway_wide",
    "camera.driveway_id",
    "camera.backyard",
    "camera.storage_ext",
    "camera.storage_int",
]

ENV_SENSORS = [
    "sensor.driveway_env_temperature",
    "sensor.driveway_env_humidity",
    "sensor.driveway_env_co2",
    "sensor.driveway_env_aqi",
    "sensor.driveway_env_pm2_5",
]

AOA_SENSORS = [
    "binary_sensor.front_aoa_person",
    "binary_sensor.driveway_wide_aoa_person",
    "binary_sensor.backyard_aoa_person",
]


def get_state(entity_id: str) -> dict | None:
    r = requests.get(f"{BASE}/states/{entity_id}", headers=HEADERS, timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


def ok_state(state: str) -> bool:
    return state not in ("unavailable", "unknown", "")


def main() -> int:
    issues: list[str] = []
    print("=== Danielsson Insights Health Check ===\n")

    print("Cameras (Frigate):")
    for cam in CAMERAS:
        s = get_state(cam)
        if not s:
            print(f"  FAIL  {cam} — not found")
            issues.append(cam)
            continue
        st = s["state"]
        mark = "OK" if ok_state(st) else "WARN"
        print(f"  {mark:4}  {cam}: {st}")
        if not ok_state(st):
            issues.append(cam)

    print("\nOutdoor environment:")
    for ent in ENV_SENSORS:
        s = get_state(ent)
        if not s:
            print(f"  FAIL  {ent}")
            issues.append(ent)
            continue
        st = s["state"]
        mark = "OK" if ok_state(st) else "WARN"
        print(f"  {mark:4}  {ent}: {st}")
        if not ok_state(st):
            issues.append(ent)

    print("\nAOA presence:")
    for ent in AOA_SENSORS:
        s = get_state(ent)
        if not s:
            print(f"  FAIL  {ent}")
            continue
        print(f"  OK    {ent}: {s['state']}")

    timeline = Path(__file__).parent.parent / "events" / "timeline.jsonl"
    print("\nEvent timeline:")
    if timeline.exists():
        lines = timeline.read_text(encoding="utf-8").strip().splitlines()
        print(f"  OK    {len(lines)} events in {timeline}")
        if lines:
            last = json.loads(lines[-1])
            print(f"        Last: {last.get('type')} @ {last.get('location', {}).get('zone')} — {last.get('timestamp', '')[:19]}")
    else:
        print(f"  WARN  No timeline yet — run event_normalizer.py")
        issues.append("timeline")

    print()
    if issues:
        print(f"Issues: {len(issues)}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
